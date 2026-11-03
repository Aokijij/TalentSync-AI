import { useId, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Clock3, Mail, Pencil, Send, X } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { InlineNotice } from "./ui/Panel.jsx";
import "../styles/security-access.css";

export function SecurityEmailPanel({ user, localMail = false }) {
  const [editing, setEditing] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(""), [message, setMessage] = useState("");
  const [recipient, setRecipient] = useState("");
  const formId = useId();
  async function verify() {
    setBusy(true); setError(""); setMessage("");
    try { const { data } = await api.post("/account/verify-email", {}, { __quiet: true }); setRecipient(user.email); setMessage(data.message); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget, fields = new FormData(form);
    setBusy(true); setError(""); setMessage("");
    const payload = { email: String(fields.get("email")).trim(), password: fields.get("password") };
    form.elements.password.value = "";
    try { const { data } = await api.post("/account/change-email", payload, { __quiet: true }); setRecipient(payload.email); setMessage(data.message); setEditing(false); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section id="security-email" className="security-panel security-email-panel">
    <header><span className="security-panel-icon"><Mail size={22} aria-hidden="true" /></span><div><h2>Correo electrónico</h2><p>Tu dirección para entrar y recibir avisos de tus procesos.</p></div></header>
    <div className="security-email-summary"><div><strong>{user.email}</strong><span className={`security-email-state ${user.email_verified ? "is-verified" : ""}`}>{user.email_verified && <CheckCircle2 size={14} aria-hidden="true" />}{user.email_verified ? "Correo confirmado" : "Pendiente de confirmar"}</span></div><button type="button" className="button-secondary" disabled={busy} aria-expanded={editing} aria-controls={editing ? formId : undefined} onClick={() => { setEditing(!editing); setError(""); }}><Pencil size={15} aria-hidden="true" />Cambiar correo</button></div>
    {error && <InlineNotice error>{error}</InlineNotice>}{message && <InlineNotice title="Revisa tu correo" tone="success"><p>{message}</p><p className="security-email-recipient">Destino: <strong>{recipient}</strong></p><p>Revisa también Spam o Correo no deseado. El enlace dura 30 minutos y se usa una sola vez.</p></InlineNotice>}
    {!user.email_verified && !editing && <div className={`security-email-verification ${message ? "is-requested" : ""}`}>{!message && <><span className="security-panel-icon"><Mail size={21} aria-hidden="true" /></span><div><h3>Confirma que este correo es tuyo</h3><p>Te llegará un enlace personal a esta dirección. Ábrelo para completar la confirmación.</p><span><Clock3 size={13} aria-hidden="true" />Válido durante 30 minutos</span></div></>}<button type="button" className={message ? "button-secondary" : "button-primary"} disabled={busy} onClick={verify}><Send size={16} aria-hidden="true" />{busy ? "Solicitando…" : message ? "Volver a solicitar" : "Enviar confirmación"}</button></div>}
    {editing && <form id={formId} className="security-email-edit" onSubmit={submit}>
      <div><h3>Elige tu nuevo correo</h3><p>El cambio se completa al confirmar el enlace que recibirás.</p></div>
      <label>Nuevo correo<input className="field-control" name="email" required type="email" autoComplete="email" placeholder="Introduce la dirección de correo" maxLength={255} disabled={busy} /></label>
      <label>Contraseña actual<input className="field-control" name="password" required type="password" autoComplete="current-password" disabled={busy} /></label>
      <footer><button type="button" className="button-secondary" disabled={busy} onClick={() => { setEditing(false); setError(""); }}><X size={16} aria-hidden="true" />Cancelar</button><button disabled={busy} className="button-primary">{busy ? "Solicitando…" : "Enviar enlace de confirmación"}<ArrowRight size={16} aria-hidden="true" /></button></footer>
    </form>}
    {import.meta.env.DEV && localMail && <details className="security-mail-development"><summary>Herramientas de desarrollo</summary><p>Los mensajes de prueba se guardan en este equipo y no se envían.</p><Link to="/desarrollo/correos">Abrir bandeja de pruebas <ArrowRight size={14} /></Link></details>}
  </section>;
}
