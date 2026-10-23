import { useId, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, CheckCircle2, Mail, Pencil, Send } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { InlineNotice } from "./ui/Panel.jsx";
import "../styles/security-access.css";

export function SecurityEmailPanel({ user, localMail = false }) {
  const [editing, setEditing] = useState(false), [busy, setBusy] = useState(false);
  const [error, setError] = useState(""), [message, setMessage] = useState("");
  const formId = useId();
  async function verify() {
    setBusy(true); setError(""); setMessage("");
    try { const { data } = await api.post("/account/verify-email", {}, { __quiet: true }); setMessage(data.message); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function submit(event) {
    event.preventDefault();
    const form = event.currentTarget, fields = new FormData(form);
    setBusy(true); setError(""); setMessage("");
    const payload = { email: String(fields.get("email")).trim(), password: fields.get("password") };
    form.elements.password.value = "";
    try { const { data } = await api.post("/account/change-email", payload, { __quiet: true }); setMessage(data.message); setEditing(false); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section id="security-email" className="security-panel security-email-panel">
    <header><span className="security-panel-icon"><Mail size={22} aria-hidden="true" /></span><div><h2>Correo electrónico</h2><p>Tu dirección para entrar y recibir avisos de tus procesos.</p></div></header>
    <div className="security-email-summary"><div><strong>{user.email}</strong><span className={`security-email-state ${user.email_verified ? "is-verified" : ""}`}>{user.email_verified && <CheckCircle2 size={14} aria-hidden="true" />}{user.email_verified ? "Correo confirmado" : "Pendiente de confirmar"}</span></div><button type="button" className="button-secondary" disabled={busy} aria-expanded={editing} aria-controls={editing ? formId : undefined} onClick={() => { setEditing(!editing); setError(""); }}><Pencil size={15} aria-hidden="true" />Cambiar correo</button></div>
    {error && <InlineNotice error>{error}</InlineNotice>}{message && <InlineNotice tone="success">{message}</InlineNotice>}
    {!user.email_verified && <button type="button" className="button-secondary" disabled={busy} onClick={verify}><Send size={15} />{busy ? "Enviando…" : "Enviar confirmación"}</button>}
    {editing && <form id={formId} className="security-email-edit" onSubmit={submit}>
      <div><h3>Elige tu nuevo correo</h3><p>El cambio se completa al confirmar el enlace que recibirás.</p></div>
      <label>Nuevo correo<input className="field-control" name="email" required type="email" autoComplete="email" placeholder="nombre@correo.com" maxLength={255} disabled={busy} /></label>
      <label>Contraseña actual<input className="field-control" name="password" required type="password" autoComplete="current-password" disabled={busy} /></label>
      <footer><button type="button" className="button-secondary" disabled={busy} onClick={() => { setEditing(false); setError(""); }}>Cancelar</button><button disabled={busy} className="button-primary">{busy ? "Solicitando…" : "Enviar enlace de confirmación"}<ArrowRight size={16} aria-hidden="true" /></button></footer>
    </form>}
    {localMail && <details className="security-mail-development"><summary>Correo de prueba</summary><p>En este entorno los mensajes se guardan en la bandeja local.</p><Link to="/desarrollo/correos">Abrir bandeja local <ArrowRight size={14} /></Link></details>}
  </section>;
}
