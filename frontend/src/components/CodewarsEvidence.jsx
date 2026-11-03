import { useEffect, useState } from "react";
import { Code2, ExternalLink, Search } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function CodewarsEvidence({ onSaved }) {
  const [enabled, setEnabled] = useState(false), [open, setOpen] = useState(false);
  const [preview, setPreview] = useState(null), [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  useEffect(() => {
    let active = true;
    api.get("/integrations/codewars/capabilities").then(({ data }) => { if (active) setEnabled(data.codewars_public); })
      .catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, []);
  async function inspect(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    setBusy(true); setError(""); setNotice(""); setPreview(null);
    try {
      const { data } = await api.post("/integrations/codewars/preview", { username: values.get("username").trim(), confirm_public_access: true }, { __quiet: true });
      setPreview(data); setSelected(data.report.signals.map((row) => row.skill));
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function save(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    setBusy(true); setError(""); setNotice("");
    try {
      const { data } = await api.post("/integrations/codewars/evidence", { preview_token: preview.preview_token,
        title: values.get("title"), description: values.get("description"), skills: selected,
        confirm_ownership: true, add_to_profile: values.has("add_to_profile") });
      await onSaved(data); setPreview(null);
      setNotice("Referencia de Codewars guardada. Consultar y guardar nuevamente actualizará esta cuenta sin duplicarla.");
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="rounded-xl border border-[var(--line)] p-4">
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><Code2 size={21} /><h3 className="font-bold">Tu práctica en Codewars</h3></div>
      <button type="button" className="button-secondary button-sm" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? "Cerrar" : "Consultar Codewars"}</button></div>
    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Consulta tus retos y rangos públicos. Elige los lenguajes que quieres relacionar con tu perfil.</p>
    {error && <p className="mt-3 text-sm text-[var(--error)]" role="alert">{error}</p>}{notice && <p className="mt-3 text-sm" role="status">{notice}</p>}
    {open && (!enabled ? <p className="mt-3 text-sm text-[var(--muted)]">La consulta de Codewars está desactivada en este entorno.</p> : <>
      <form className="mt-4 space-y-3" onSubmit={inspect}><label className="block text-sm">Usuario de Codewars<input name="username" className="field-control mt-1" required maxLength={80} placeholder="Tu nombre de usuario, sin la URL" disabled={busy} onChange={() => { setPreview(null); setSelected([]); }} /></label>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" required disabled={busy} className="mt-1" />Autorizo consultar los rangos y estadísticas públicos de esta cuenta.</label>
        <button className="button-secondary" disabled={busy}><Search size={16} />{busy ? "Consultando…" : "Consultar mi práctica"}</button></form>
      {preview && <div className="mt-5 border-t border-[var(--line)] pt-4">
        <div className="flex flex-wrap items-center justify-between gap-2"><h4 className="font-bold">@{preview.report.username}</h4><a className="inline-flex items-center gap-1 text-sm text-[var(--accent)]" href={preview.report.profile_url} target="_blank" rel="noopener noreferrer">Abrir en Codewars <ExternalLink size={14} /></a></div>
        <div className="mt-3 grid grid-cols-2 gap-3"><div className="rounded-xl bg-[var(--surface-2)] p-3"><p className="text-xs text-[var(--muted)]">Rango general</p><p className="mt-1 text-xl font-bold">{preview.report.overall.rank}</p></div>
          <div className="rounded-xl bg-[var(--surface-2)] p-3"><p className="text-xs text-[var(--muted)]">Retos resueltos en total</p><p className="mt-1 text-xl font-bold">{preview.report.completed_challenges.toLocaleString("es-CO")}</p></div></div>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{preview.report.notice}</p>
        {preview.report.truncated && <p className="mt-2 text-xs text-[var(--muted)]">Se muestran hasta 20 lenguajes por consulta.</p>}
        {!preview.report.signals.length ? <p className="mt-3 text-sm">Esta cuenta aún no informa lenguajes con rango y puntos de práctica. Puedes aportar una referencia manual o volver después de completar retos.</p> : <form key={preview.preview_token} onSubmit={save} className="mt-4 space-y-3">
          <fieldset><legend className="text-sm font-semibold">Lenguajes que quieres relacionar</legend><div className="mt-2 grid gap-2 sm:grid-cols-2">{preview.report.signals.map((row) => <label key={row.skill} className="flex items-center gap-2 rounded-xl border border-[var(--line)] px-3 py-2 text-sm"><input type="checkbox" checked={selected.includes(row.skill)} disabled={busy} onChange={(event) => setSelected(event.target.checked ? [...selected, row.skill] : selected.filter((skill) => skill !== row.skill))} /><span><strong>{row.skill}</strong><span className="ml-2 text-xs text-[var(--muted)]">{row.rank} · {row.score.toLocaleString("es-CO")} puntos</span></span></label>)}</div></fieldset>
          <label className="block text-sm">Título de la referencia<input className="field-control mt-1" name="title" required minLength={3} maxLength={160} defaultValue={`Mi práctica en Codewars · ${preview.report.username}`} disabled={busy} /></label>
          <label className="block text-sm">Qué practicas y cómo lo aplicas<textarea className="field-control mt-1" name="description" required minLength={10} maxLength={2000} placeholder="Describe los problemas que has resuelto y qué has aprendido." disabled={busy} /></label>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" required disabled={busy} className="mt-1" />Declaro que esta cuenta de Codewars es mía y puedo compartir su información pública.</label>
          <label className="flex items-start gap-2 text-sm"><input name="add_to_profile" type="checkbox" disabled={busy} className="mt-1" />Añadir los lenguajes seleccionados a mis habilidades declaradas.</label>
          <button className="button-primary" disabled={busy || !selected.length}>{busy ? "Guardando…" : "Guardar referencia en mi perfil"}</button>
          <p className="text-xs leading-5 text-[var(--muted)]">La vista previa vence en 10 minutos. La consulta puede usar datos en caché de hasta 10 minutos. No se sincroniza en segundo plano. Retirar la referencia conserva tus habilidades declaradas.</p>
        </form>}
      </div>}
    </>)}
  </section>;
}
