import { useEffect, useState } from "react";
import { CalendarDays, CheckCircle2, Link2, Unplug } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { InlineNotice } from "./ui/Panel.jsx";
import "../styles/account-controls.css";

export function GoogleCalendarPanel() {
  const { confirm } = useFeedback();
  const [status, setStatus] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const callback = new URLSearchParams(window.location.search).get("calendar");
  async function load() { setStatus((await api.get("/account/calendar")).data); }
  useEffect(() => { load().catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function connect() {
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/account/calendar/google/connect", {}, { __quiet: true });
      const target = new URL(data.url);
      if (target.origin !== "https://accounts.google.com") throw new Error("No se recibió una dirección válida de Google.");
      window.location.assign(target.href);
    } catch (failure) { setError(getApiErrorMessage(failure)); setBusy(false); }
  }
  async function disconnect() {
    if (!await confirm({ title: "Desconectar Google Calendar", description: "Se detendrán las actualizaciones de entrevistas. Los eventos ya copiados en Google se conservan y podrás eliminarlos allí.", confirmLabel: "Desconectar" })) return;
    setBusy(true); setError("");
    try { await api.delete("/account/calendar", { __quiet: true }); await load(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section id="security-calendar" className="security-panel account-controls"><header><CalendarDays size={24} /><div><h2>Google Calendar</h2><p>Tus entrevistas, con sus cambios de fecha y cancelaciones.</p></div></header>
    {error && <InlineNotice error>{error}</InlineNotice>}{callback === "not_connected" && <InlineNotice tone="warning">La autorización no se completó. Puedes volver a intentarlo.</InlineNotice>}
    {!status && !error && <p role="status">Consultando la conexión…</p>}
    {status && <><span className="status-chip">{status.connected ? <CheckCircle2 size={16} /> : <Unplug size={16} />}{status.connected ? "Calendario conectado" : "Sin conectar"}</span>{status.error && <InlineNotice tone="warning">{status.error}</InlineNotice>}
    <p>{status.note}</p><ol className="calendar-steps"><li>Autoriza el acceso a los eventos de tu propio calendario.</li><li>Abre un proceso y elige la entrevista que quieras sincronizar.</li><li>Se actualizará cuando cambie la fecha o finalice el proceso.</li></ol>
    {!status.configured && <InlineNotice>La conexión con Google Calendar todavía no está habilitada en este entorno. Puedes descargar cada cita desde tu proceso.</InlineNotice>}
    <footer><small>La autorización del calendario es independiente del inicio de sesión con Google. Puedes revocarla en cualquier momento.</small><div className="account-button-row"><button className="button-primary" disabled={busy || !status.configured} onClick={connect}><Link2 size={17} />{busy ? "Procesando…" : status.connected ? "Volver a autorizar" : "Conectar Google Calendar"}</button>{status.connected && <button className="button-secondary" disabled={busy} onClick={disconnect}>Desconectar</button>}</div></footer></>}
  </section>;
}
