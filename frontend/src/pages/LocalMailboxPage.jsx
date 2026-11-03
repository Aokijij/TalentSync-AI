import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";

export function LocalMailboxPage() {
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  async function load() {
    try { const { data } = await api.get("/dev/mailbox"); setMessages(data); setError(""); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
  }
  useEffect(() => { load(); }, []);
  return <main className="mx-auto max-w-4xl space-y-5 p-6">
    <div className="surface-card p-6"><p className="section-kicker">Solo desarrollo local</p><h1 className="mt-2 text-2xl font-bold">Bandeja de correo</h1>
      <p className="mt-2 text-sm text-[var(--muted)]">Estos mensajes permanecen en la base local. No se envían a destinatarios reales. Los enlaces contienen credenciales temporales.</p>
      <div className="mt-4 flex gap-4"><button className="button-secondary" onClick={load}>Actualizar</button><Link className="button-secondary" to="/login">Volver</Link></div>
    </div>
    {error && <p role="alert">{error}</p>}
    {!messages.length && !error && <p>No hay mensajes todavía.</p>}
    {messages.map((message) => {
      const raw = message.body.match(/https?:\/\/[^\s]+/)?.[0];
      let action = null;
      try { const url = new URL(raw); if (["localhost", "127.0.0.1"].includes(url.hostname) && ["/cuenta/confirmar", "/equipo/invitacion"].includes(url.pathname)) action = url.pathname + url.search; } catch { /* No action link. */ }
      return <article className="surface-card p-5" key={message.id}><p className="text-xs text-[var(--muted)]">Para: {message.recipient}</p><h2 className="mt-2 font-bold">{message.subject}</h2><p className="mt-3 whitespace-pre-wrap break-all text-sm">{message.body}</p>{action && <Link className="button-primary mt-4 inline-flex" to={action}>{action.startsWith("/equipo/invitacion") ? "Abrir invitación al equipo" : "Abrir confirmación"}</Link>}</article>;
    })}
  </main>;
}
