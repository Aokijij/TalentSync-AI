import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, Check, CheckCircle2, Clock3, Eye, EyeOff, KeyRound, Mail, Send, ShieldCheck } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { ThemeToggle } from "../components/ThemeToggle.jsx";
import { InlineNotice } from "../components/ui/Panel.jsx";
import { accountHome } from "../utils/accountAccess.js";
import "../styles/account-mail.css";

const actions = {
  verify: { title: "Confirma tu correo", description: "Confirma que esta dirección te pertenece para completar las acciones protegidas de tu cuenta.", button: "Confirmar mi correo", done: "Tu correo está confirmado", Icon: Mail },
  email: { title: "Confirma tu nuevo correo", description: "Esta dirección será tu nuevo correo de acceso y de avisos. Al confirmar, se cerrarán tus sesiones anteriores.", button: "Confirmar nuevo correo", done: "Tu correo se actualizó", Icon: Mail },
  reset: { title: "Crea una nueva contraseña", description: "Elige una contraseña exclusiva para TalentSync. Al guardarla, se cerrarán tus sesiones anteriores.", button: "Guardar nueva contraseña", done: "Tu contraseña se actualizó", Icon: KeyRound },
};

export function AccountActionPage({ recover = false }) {
  const [params] = useSearchParams();
  const [message, setMessage] = useState(""), [error, setError] = useState("");
  const [busy, setBusy] = useState(false), [visible, setVisible] = useState(false);
  const [requestedEmail, setRequestedEmail] = useState("");
  const { user, refreshUser, accessOptions } = useAuth();
  const purpose = params.get("purpose"), token = params.get("token");
  const action = Object.hasOwn(actions, purpose) ? actions[purpose] : null;
  const valid = recover || !!(action && token?.trim());
  const company = user?.role === "company" || params.get("portal") === "company";
  const login = user?.role === "admin" ? "/acceso-administracion" : company ? "/empresa/login" : "/login";
  const Icon = message ? CheckCircle2 : recover ? KeyRound : action?.Icon || ShieldCheck;
  useEffect(() => { setMessage(""); setError(""); setVisible(false); }, [purpose, token, recover]);

  async function submit(event) {
    event.preventDefault();
    if (busy || !valid) return;
    const form = event.currentTarget, data = new FormData(form);
    setError("");
    if (!recover && purpose === "reset") {
      if (new TextEncoder().encode(data.get("password")).length > 72) { setError("La contraseña es demasiado larga. Usa hasta 72 bytes; las tildes y los símbolos pueden ocupar más de uno."); return; }
      if (data.get("password") !== data.get("confirmation")) { setError("Las contraseñas no coinciden. Revisa los dos campos."); return; }
    }
    setBusy(true);
    try {
      const response = recover
        ? await api.post("/auth/password/request", { email: String(data.get("email")).trim() }, { __quiet: true })
        : await api.post("/auth/action/confirm", { purpose, token, password: purpose === "reset" ? data.get("password") : null }, { __quiet: true });
      if (recover) setRequestedEmail(String(data.get("email")).trim());
      form.reset();
      setMessage(response.data.message || "Solicitud completada.");
      if (!recover && user) await refreshUser().catch(() => {});
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <main className={`account-mail-page ${company ? "role-company" : "role-candidate"}`}>
    <header className="account-mail-top"><Link to="/" aria-label="Inicio de TalentSync"><BrandLogo subtitle="TU CUENTA" /></Link><ThemeToggle compact /></header>
    <section className="account-mail-card" aria-labelledby="account-mail-title">
      <div className={`account-mail-symbol ${message ? "is-complete" : ""}`}><Icon size={28} aria-hidden="true" /></div>
      <p className="section-kicker">{message ? "Siguiente paso" : "Acceso y seguridad"}</p>
      <h1 id="account-mail-title">{message ? recover ? "Revisa tu correo" : action?.done : !valid ? "Revisa tu enlace" : recover ? "Recupera tu acceso" : action.title}</h1>
      <p className="account-mail-description">{message ? recover ? "Si hay una cuenta asociada a esta dirección, recibirás un enlace para crear una nueva contraseña." : purpose === "verify" ? "Puedes continuar en TalentSync con tu dirección confirmada." : "Entra de nuevo a TalentSync con tus datos actualizados." : !valid ? "El enlace está incompleto o no corresponde a una confirmación de cuenta. Abre el enlace completo del último correo que recibiste." : recover ? "Introduce el correo de tu cuenta y solicita un enlace para crear una nueva contraseña." : action.description}</p>

      {message ? <div className="account-mail-result" role="status">
        {recover ? <><div className="account-mail-recipient"><Mail size={19} aria-hidden="true" /><strong>{requestedEmail}</strong></div><ol className="account-mail-steps"><li><span>1</span>Busca el mensaje de TalentSync en tu bandeja de entrada.</li><li><span>2</span>Revisa también Spam o Correo no deseado.</li><li><span>3</span>Abre el enlace y guarda tu nueva contraseña.</li></ol><p className="account-mail-expiry"><Clock3 size={15} aria-hidden="true" />El enlace dura 30 minutos y se usa una sola vez.</p></> : <p className="account-mail-confirmed"><Check size={18} aria-hidden="true" />{message}</p>}
        {recover && <button type="button" className="button-secondary" onClick={() => { setMessage(""); setError(""); }}>Revisar dirección o volver a solicitar</button>}
        <Link className="button-primary" to={!recover && purpose === "verify" && user ? accountHome(user, accessOptions) : login}>{!recover && purpose === "verify" && user ? "Continuar a mi espacio" : "Ir al inicio de sesión"}<ArrowRight size={17} aria-hidden="true" /></Link>
      </div> : valid ? <form className="account-mail-form" onSubmit={submit} aria-busy={busy}>
        {recover && <label>Correo electrónico<input required name="email" type="email" autoComplete="email" maxLength={255} defaultValue={requestedEmail} placeholder="Introduce el correo registrado en TalentSync" className="field-control" disabled={busy} /></label>}
        {!recover && purpose === "reset" && <>
          <label>Nueva contraseña<div className="account-mail-password"><input required name="password" type={visible ? "text" : "password"} minLength={12} maxLength={72} autoComplete="new-password" placeholder="Crea una contraseña de al menos 12 caracteres" className="field-control" disabled={busy} aria-describedby="password-guidance" /><button type="button" className="button-ghost" aria-label={visible ? "Ocultar contraseña" : "Mostrar contraseña"} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={18} /> : <Eye size={18} />}</button></div></label>
          <label>Repite la nueva contraseña<input required name="confirmation" type={visible ? "text" : "password"} minLength={12} maxLength={72} autoComplete="new-password" placeholder="Escribe de nuevo la contraseña" className="field-control" disabled={busy} /></label>
          <p id="password-guidance" className="account-mail-guidance">Usa al menos 12 caracteres y hasta 72 bytes. No reutilices la contraseña de tu correo.</p>
        </>}
        {error && <InlineNotice error>{error}</InlineNotice>}
        {!recover && <p className="account-mail-expiry"><Clock3 size={16} aria-hidden="true" />Enlace personal · 30 minutos · Un solo uso</p>}
        <button disabled={busy} className="button-primary" type="submit">{busy ? "Procesando…" : recover ? "Enviar enlace de recuperación" : action.button}{recover ? <Send size={17} aria-hidden="true" /> : <ArrowRight size={17} aria-hidden="true" />}</button>
        {!recover && error && <Link className="account-mail-text-link" to={purpose === "reset" ? "/recuperar-acceso" : user ? "/seguridad#security-email" : login}>{purpose === "reset" ? "Solicitar un nuevo enlace" : "Volver a mi cuenta"}<ArrowRight size={15} aria-hidden="true" /></Link>}
      </form> : <Link className="button-primary" to={user ? "/seguridad#security-email" : "/recuperar-acceso"}>{user ? "Ir a Seguridad de cuenta" : "Recuperar acceso"}<ArrowRight size={17} aria-hidden="true" /></Link>}

      <footer className="account-mail-footer"><ShieldCheck size={17} aria-hidden="true" /><p>TalentSync nunca te pedirá tu contraseña ni códigos de acceso por correo.</p></footer>
      {!message && <Link className="account-mail-back" to={user ? accountHome(user, accessOptions) : login}><ArrowLeft size={16} aria-hidden="true" />{user ? "Volver a mi espacio" : "Volver al inicio de sesión"}</Link>}
      {import.meta.env.DEV && accessOptions?.local_mail && <details className="account-mail-development"><summary>Herramientas de desarrollo</summary><Link to="/desarrollo/correos">Abrir bandeja de pruebas</Link></details>}
    </section>
    <p className="account-mail-footnote">TalentSync · Tu acceso, bajo tu control.</p>
  </main>;
}
