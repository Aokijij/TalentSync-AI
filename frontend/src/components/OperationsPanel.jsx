import { useEffect, useState } from "react";
import { Activity, Mail, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { InlineNotice } from "./ui/Panel.jsx";
import "../styles/operations.css";

const mailStates = { accepted: "Aceptado por el proveedor", delivered: "Entregado", bounced: "Rebotado", complained: "Marcado como spam", delayed: "Entrega retrasada", failed: "Entrega fallida" };
const queueStates = { pending: "En cola", sending: "Enviando", sent: "Enviado al transporte", failed: "Fallido", expired: "Vencido", local: "Solo bandeja local", retry: "Reintento pendiente" };

export function OperationsPanel() {
  const [status, setStatus] = useState(null), [mail, setMail] = useState(null), [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function load() {
    setBusy(true); setError("");
    try { const [a, b] = await Promise.all([api.get("/admin/operations"), api.get("/admin/mail-delivery", { params: { page } })]); setStatus(a.data); setMail(b.data); }
    catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  useEffect(() => { load(); }, [page]);
  return <div className="operations-workspace"><header><div><h2><Activity size={21} />Estado operativo</h2><p>Dependencias, reintentos y entrega de correos.</p></div><button className="button-secondary button-sm" disabled={busy} onClick={load}><RefreshCw size={16} />Actualizar</button></header>
    {error && <InlineNotice error>{error}</InlineNotice>}{busy && !status && <p role="status">Consultando el estado…</p>}
    {status && <><div className="operations-summary">{[["Base de datos", status.checks.database, "Disponible", "Sin respuesta"], ["Archivos privados", status.checks.private_storage, "Disponible", "Sin respuesta"], ["Google Calendar", status.calendar_configured, "Configurado", "Sin configurar"], ["Limpieza de archivos", status.cleanup_enabled, "Activada", "Desactivada"], ["Conservación automática", status.retention_enabled, "Activada", "Desactivada"]].map(([label, available, positive, negative]) => <article className="surface-card" key={label}><span>{label}</span><strong data-ready={available}>{available ? positive : negative}</strong></article>)}</div>
    {!!status.alerts.length && <InlineNotice tone="warning" title="Requiere atención"><ul>{status.alerts.map((alert) => <li key={alert}>{alert}</li>)}</ul></InlineNotice>}
    <section className="surface-card operations-section"><h3>Solicitudes recientes</h3><p>{status.note}</p><div className="operations-table-scroll"><table><thead><tr><th>Ruta</th><th>Muestras</th><th>Errores 5xx</th><th>p95</th></tr></thead><tbody>{status.requests.routes.slice(0, 12).map((row) => <tr key={row.method + row.route}><td><code>{row.method} {row.route}</code></td><td>{row.samples}</td><td>{row.errors}</td><td>{row.p95_ms} ms</td></tr>)}</tbody></table></div>{!status.requests.routes.length && <p>Aún no hay muestras.</p>}<small>p95: el 95 % de las muestras tardó ese tiempo o menos. Máximo {status.requests.sample_limit_per_route} por ruta. Las alertas requieren al menos 20 muestras.</small></section>
    <section className="surface-card operations-section"><h3>Trabajos pendientes</h3><dl className="operations-counts">{[["Correos en cola", "mail_pending"], ["Correos fallidos", "mail_failed"], ["Calendarios fallidos", "calendar_failed"], ["Limpiezas pendientes", "file_erasure_pending"]].map(([label, key]) => <div key={key}><dt>{label}</dt><dd>{status.queues[key]}</dd></div>)}</dl></section></>}
    {mail && <section className="surface-card operations-section"><h3><Mail size={19} />Entrega de correos</h3><p>{mail.note}</p><p className="text-xs text-[var(--muted)]">Se muestran estados e identificadores internos; no se exponen destinatarios ni contenido.</p><ul className="mail-delivery-list">{mail.items.map((row) => <li key={row.id}><div><strong>Correo #{row.id}</strong><span>{queueStates[row.queue_state] || "Estado pendiente de revisión"} · {row.attempts} intentos</span></div><span className="status-chip" data-state={row.transport_status}>{mailStates[row.transport_status] || "Sin confirmación de entrega"}</span></li>)}</ul>{!mail.items.length && <p>No hay correos registrados.</p>}<footer><span>{mail.total} registros · Página {mail.page} de {Math.max(1, Math.ceil(mail.total / mail.page_size))}</span><div><button className="button-secondary button-sm" disabled={busy || page <= 1} onClick={() => setPage(page - 1)}>Anterior</button><button className="button-secondary button-sm" disabled={busy || page * mail.page_size >= mail.total} onClick={() => setPage(page + 1)}>Siguiente</button></div></footer></section>}
  </div>;
}
