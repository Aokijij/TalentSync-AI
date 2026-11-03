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
  const reason = new URLSearchParams(window.location.search).get("reason");
  const callbackMessage = reason === "expired" ? "La autorización venció o se abrió en otra sesión. Inicia una conexión nueva desde aquí."
    : reason === "cancelled" || reason === "authorization" ? "Google no autorizó la conexión. Comprueba la cuenta elegida y vuelve a autorizar el acceso al calendario."
      : "La autorización no se completó. Puedes volver a intentarlo.";
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
    if (!await confirm({ title: "Desconectar Google Calendar", description: "Se detendrán las actualizaciones de entrevistas. Los eventos ya añadidos a Google se conservan y podrás eliminarlos allí.", confirmLabel: "Desconectar" })) return;
    setBusy(true); setError("");
    try { await api.delete("/account/calendar", { __quiet: true }); await load(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section id="security-calendar" className="security-panel account-controls"><header><CalendarDays size={24} /><div><h2>Google Calendar</h2><p>Tus entrevistas, con sus cambios de fecha y cancelaciones.</p></div></header>
    {error && <InlineNotice error>{error}</InlineNotice>}{callback === "not_connected" && <InlineNotice tone="warning">{callbackMessage}</InlineNotice>}
    {!status && !error && <p role="status">Consultando la conexión…</p>}
    {status && <>
      <div className={`calendar-connection-card ${status.connected && !status.needs_reconnect ? "is-connected" : ""}`}>
        <span className="calendar-connection-icon">{status.connected && !status.needs_reconnect ? <CheckCircle2 size={25} /> : <CalendarDays size={25} />}</span>
        <div><strong>{status.needs_reconnect ? "Tu conexión necesita renovarse" : status.connected ? "Calendario conectado" : "Conecta tus entrevistas"}</strong><p>{status.needs_reconnect ? "Google ya no permite actualizar tus entrevistas. Vuelve a conectar para recuperarlo." : status.connected ? "Todo listo para añadir entrevistas y mantener sus cambios al día." : "Guarda las entrevistas que elijas en tu calendario de Google."}</p>{status.connected_at && <small>Conectado el {new Date(`${status.connected_at.replace(/Z$/, "")}Z`).toLocaleDateString("es-CO", { timeZone: "America/Bogota" })}</small>}</div>
      </div>
      {status.error && <InlineNotice tone="warning">{status.error}</InlineNotice>}
      <div className="calendar-benefits"><div><strong>Detalles completos</strong><p>Fecha, duración, modalidad y enlace o dirección definidos por la empresa.</p></div><div><strong>Cambios al día</strong><p>Las entrevistas añadidas se actualizan cuando cambian o se cancelan, con un recordatorio 30 minutos antes.</p></div></div>
      {!status.configured && <InlineNotice>La conexión todavía no está habilitada en este entorno.</InlineNotice>}
      {!status.connected && <details className="calendar-access-help"><summary>¿Google muestra «Acceso bloqueado»?</summary><p>Si la aplicación está en pruebas, el administrador debe añadir tu cuenta a los usuarios de prueba de Google. Después puedes conectar de nuevo.</p></details>}
      <footer><small>Elige las entrevistas desde tu agenda o desde cada proceso. No se añaden invitados ni se comparten notas internas.</small><div className="account-button-row">{(!status.connected || status.needs_reconnect) && <button className="button-primary" disabled={busy || !status.configured} onClick={connect}><Link2 size={17} />{busy ? "Conectando…" : status.needs_reconnect ? "Renovar conexión" : "Conectar Google Calendar"}</button>}{status.connected && <button className="button-secondary calendar-disconnect security-disconnect-action" disabled={busy} onClick={disconnect}><Unplug size={16} />Desconectar</button>}</div></footer>
    </>}

  </section>;
}
