import { useEffect, useRef, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { useInterviewCall } from "../hooks/useInterviewCall.js";

export function InterviewsPage() {
  const { user } = useAuth();
  const [params] = useSearchParams();
  const [rooms, setRooms] = useState([]);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function load() { setRooms((await api.get("/interviews/rooms")).data); }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  return <div className="space-y-5">
    <PageHeader kicker="Entrevista integrada" title="Salas de entrevista" description="Editor y pizarra compartidos, con videollamada entre dos navegadores locales. La empresa prepara la sala al avanzar a entrevista técnica." />
    {error && <p role="alert" className="text-[var(--error)]">{error}</p>}
    {user.role !== "candidate" && <form className="surface-card grid gap-3 p-5 sm:grid-cols-3" onSubmit={async (event) => {
      event.preventDefault(); setBusy(true); setError(""); const data = new FormData(event.currentTarget);
      try { await api.post("/interviews/rooms", { application_id: Number(data.get("application")), title: data.get("title") }); await load(); }
      catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
    }}><label>ID del proceso asignado<input className="field-control mt-1" type="number" name="application" min="1" defaultValue={params.get("proceso")} required /></label><label>Título<input className="field-control mt-1" name="title" defaultValue="Entrevista técnica" minLength={3} maxLength={150} required /></label><button disabled={busy} className="button-primary self-end">Preparar sala</button></form>}
    <div className="grid gap-4 md:grid-cols-2">{rooms.map((room) => <section className="surface-card space-y-3 p-5" key={room.id}><h2 className="font-bold">{room.title}</h2><p className="text-sm text-[var(--muted)]">Proceso #{room.application_id} · {room.active ? "Abierta" : "Solo lectura"} · versión {room.version}</p><Link className="button-primary inline-flex" to={`/entrevistas/${room.id}`}>Entrar a la sala</Link></section>)}</div>
    {!rooms.length && <p className="surface-card p-5 text-[var(--muted)]">Aún no tienes salas. Recibirás una notificación cuando tu empresa prepare una entrevista.</p>}
  </div>;
}

export function InterviewRoomPage() {
  const { roomId } = useParams(); const { user } = useAuth();
  const [room, setRoom] = useState(null); const [code, setCode] = useState(""); const [board, setBoard] = useState([]);
  const [dirty, setDirty] = useState(false); const [incoming, setIncoming] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState(""); const [notice, setNotice] = useState(""); const [stroke, setStroke] = useState([]);
  const dirtyRef = useRef(false); const version = useRef(0); const draftStroke = useRef(null);
  const call = useInterviewCall(roomId);
  function apply(data) { setRoom(data); setCode(data.code); setBoard(data.whiteboard); version.current = data.version; dirtyRef.current = false; setDirty(false); setIncoming(false); }
  function edit() { dirtyRef.current = true; setDirty(true); }
  useEffect(() => {
    let alive = true; let timer;
    async function poll() {
      try {
        const { data } = await api.get(`/interviews/rooms/${roomId}`);
        if (!alive) return;
        if (!dirtyRef.current) apply(data);
        else { setIncoming(data.version !== version.current); setRoom((current) => current ? { ...current, active: data.active, closed: data.closed } : data); }
      } catch (failure) { if (alive) setError(getApiErrorMessage(failure)); }
      if (alive) timer = setTimeout(poll, 3000);
    }
    poll(); return () => { alive = false; clearTimeout(timer); };
  }, [roomId]);
  useEffect(() => { if (room && !room.active) call.stop(); }, [room?.active]);
  function point(event) { const bounds = event.currentTarget.getBoundingClientRect(); return { x: Math.max(0, Math.min(1000, (event.clientX - bounds.left) * 1000 / bounds.width)), y: Math.max(0, Math.min(600, (event.clientY - bounds.top) * 600 / bounds.height)) }; }
  function endStroke() { if (draftStroke.current) { setBoard((current) => [...current, { points: draftStroke.current }]); draftStroke.current = null; setStroke([]); edit(); } }
  async function save() {
    setBusy(true); setError(""); setNotice("");
    try { const { data } = await api.put(`/interviews/rooms/${roomId}`, { expected_version: version.current, code, whiteboard: board }); apply(data); setNotice("Versión compartida publicada"); }
    catch (failure) { setError(getApiErrorMessage(failure)); if (failure.response?.status === 409) setIncoming(true); }
    finally { setBusy(false); }
  }
  return <div className="space-y-5">
    <PageHeader kicker="Colaboración local" title={room?.title || "Cargando sala…"} description="Publica para compartir tus cambios. La sala conserva el código y la pizarra; la videollamada no se graba." />
    {error && <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>}{notice && <p role="status">{notice}</p>}
    {room && <>
      <section className="surface-card space-y-4 p-5"><div className="flex flex-wrap items-center justify-between gap-3"><p>Proceso #{room.application_id} · versión {version.current} · {room.active ? dirty ? "Cambios sin publicar" : "Actualizado" : "Solo lectura"}</p><div className="flex flex-wrap gap-2"><button className="button-outline" onClick={() => { const blob = new Blob([code], { type: "text/plain" }); const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = `entrevista-${room.application_id}.txt`; link.click(); URL.revokeObjectURL(url); }}>Descargar mi código</button><button className="button-primary" disabled={!room.active || !dirty || busy} onClick={save}>Publicar cambios</button></div></div>
        {incoming && <div role="status" className="rounded-lg bg-[var(--surface-subtle)] p-4">Hay una nueva versión compartida. Tu borrador se conserva. Descárgalo antes de reemplazarlo.<button className="button-outline ml-3" disabled={busy} onClick={async () => { try { apply((await api.get(`/interviews/rooms/${roomId}`)).data); } catch (failure) { setError(getApiErrorMessage(failure)); } }}>Reemplazar borrador con versión compartida</button></div>}
        <div className="grid gap-5 xl:grid-cols-2"><label className="min-w-0 font-semibold">Editor de código<textarea spellCheck={false} aria-label="Editor de código compartido" className="field-control mt-2 min-h-[360px] resize-y font-mono text-sm" value={code} maxLength={30000} readOnly={!room.active || busy} onChange={(event) => { setCode(event.target.value); edit(); }} /></label>
          <div><div className="flex items-center justify-between"><h2 className="font-semibold">Pizarra compartida</h2><button disabled={!room.active || busy || !board.length} className="button-ghost" onClick={() => { setBoard([]); edit(); }}>Limpiar mi borrador</button></div><svg aria-label="Pizarra para dibujar diagramas" role="img" viewBox="0 0 1000 600" className="mt-2 w-full touch-none rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)]" onPointerDown={(event) => { if (!room.active || busy || board.length >= 150) return; event.currentTarget.setPointerCapture(event.pointerId); draftStroke.current = [point(event)]; setStroke(draftStroke.current); }} onPointerMove={(event) => { if (!draftStroke.current || draftStroke.current.length >= 100) return; draftStroke.current = [...draftStroke.current, point(event)]; setStroke(draftStroke.current); }} onPointerUp={endStroke} onPointerCancel={endStroke}>{[...board, ...(stroke.length ? [{ points: stroke }] : [])].map((line, index) => <polyline key={index} points={line.points.map((item) => `${item.x},${item.y}`).join(" ")} fill="none" stroke="currentColor" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />)}</svg><p className="mt-2 text-xs text-[var(--muted)]">Hasta 150 trazos por versión. Publica para que aparezcan en la otra pestaña.</p></div></div>
        <p className="text-sm text-[var(--muted)]">El código se comparte como texto. La ejecución automática requiere un entorno aislado y está desactivada.</p>
      </section>
      <section className="surface-card space-y-4 p-5"><h2 className="font-bold">Videollamada local</h2><p className="text-sm text-[var(--muted)]">Dos participantes en localhost o una red compatible. La conexión directa intercambia datos de red entre participantes. Para llamadas por Internet se necesita configurar un servidor de retransmisión.</p><div className="grid gap-4 sm:grid-cols-2"><div><p className="mb-2 text-sm">Tu cámara</p><video ref={call.localVideo} autoPlay muted playsInline className="aspect-video w-full rounded-xl bg-slate-950" /></div><div><p className="mb-2 text-sm">Otro participante</p><video ref={call.remoteVideo} autoPlay playsInline className="aspect-video w-full rounded-xl bg-slate-950" /></div></div><p role="status">{call.status}</p>{call.error && <p role="alert" className="text-[var(--error)]">{call.error}</p>}<div className="flex gap-3"><button disabled={!room.active || call.connected} className="button-primary" onClick={call.start}>Activar cámara y micrófono</button><button className="button-outline" onClick={call.stop}>Desconectar</button></div></section>
      <div className="flex flex-wrap gap-3"><Link className="button-outline" to="/entrevistas">Volver a mis salas</Link>{user.role !== "candidate" && room.active && <button disabled={busy} className="button-outline" onClick={async () => { setBusy(true); try { apply((await api.post(`/interviews/rooms/${roomId}/close`)).data); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }}>Cerrar sala y conservar versión publicada</button>}</div>
    </>}
  </div>;
}
