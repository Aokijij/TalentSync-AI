import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Check, FilePenLine, RotateCcw, ShieldCheck } from "lucide-react";
import { useAuth } from "../hooks/useAuth.js";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { companyWelcomeState } from "../utils/welcome.js";
import "../styles/welcome.css";

export function CompanyWelcomePage() {
  const { user, accessOptions } = useAuth();
  const [organization, setOrganization] = useState(null), [error, setError] = useState(""), [revision, setRevision] = useState(0);
  useEffect(() => {
    let active = true; setError("");
    api.get("/organization/me").then(({ data }) => { if (active) setOrganization(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure, "No pudimos consultar el estado de tu organización.")); });
    return () => { active = false; };
  }, [revision]);
  const state = organization ? companyWelcomeState(organization, user, accessOptions) : null;
  const steps = state ? [
    { title: "Confirma tu correo", done: !!user.email_verified, label: user.email_verified ? "Confirmado" : "Pendiente", text: user.email_verified ? "Tu cuenta tiene el correo confirmado." : "Confirma el correo de esta cuenta desde Seguridad para continuar con las acciones protegidas.", to: "/seguridad#security-email", action: "Revisar mi correo" },
    { title: "Prepara la organización", done: state.submitted, label: state.submitted ? "Solicitud presentada" : "Por presentar", text: state.owner ? "Completa los datos y soportes desde Organización y equipo. Puedes volver a consultarlos y corregirlos allí." : "El propietario de la empresa presenta y corrige la solicitud. Tu acceso conserva los permisos que te asignó.", to: "/empresa/equipo#verificacion", action: state.owner ? "Revisar solicitud" : "Consultar organización" },
    { title: "Consulta la revisión", done: organization.verification_status === "verified", label: state.reviewLabel, text: state.reviewText, to: "/empresa/equipo#verificacion", action: "Ver estado y respuesta" },
    { title: "Prepara tu primera publicación", done: false, label: state.ready ? "Acceso habilitado" : "Con requisitos pendientes", text: state.ready ? "Puedes preparar y revisar una oferta. Su publicación también exige completar las condiciones y la revisión de calidad." : organization.verification_status === "suspended" ? "La empresa debe resolver la suspensión antes de retomar la actividad." : "Puedes preparar una oferta en borrador. Para publicarla deben cumplirse los requisitos de cuenta, organización y calidad.", to: organization.verification_status === "suspended" ? "/empresa/equipo#verificacion" : "/empresa/calidad?nueva=1", action: state.ready ? "Preparar una vacante" : organization.verification_status === "suspended" ? "Revisar suspensión" : "Preparar un borrador" },
  ] : [];
  return <div className="space-y-6 company-welcome"><PageHeader kicker="TU PRIMERA CONTRATACIÓN" title="Prepara tu espacio de empresa" description="Consulta lo que ya está listo y el siguiente paso para empezar a publicar." actions={<Link className="button-secondary" to="/empresa">Ir a mi panel<ArrowRight size={16} /></Link>} />
    {error && <div className="welcome-alert" role="alert"><p>{error}</p><button type="button" className="button-secondary" onClick={() => setRevision((current) => current + 1)}><RotateCcw size={16} />Reintentar</button></div>}
    {!organization && !error && <p role="status">Consultando tu organización…</p>}
    {state && <div className="welcome-layout"><section className="welcome-panel" aria-labelledby="company-welcome-title"><header><span className="public-demo-icon"><ShieldCheck size={22} /></span><div><h2 id="company-welcome-title">{organization.name}</h2><p>El estado viene de tu organización. Cada paso conserva su propia comprobación.</p></div></header><ol className="welcome-checklist">{steps.map((step, index) => <li key={step.title}><span className={`welcome-step-icon ${step.done ? "is-done" : ""}`} aria-label={step.done ? "Completado" : `Paso ${index + 1}`}>{step.done ? <Check size={17} /> : index + 1}</span><div className="welcome-step-copy"><div className="welcome-step-title"><h3>{step.title}</h3><span>{step.label}</span></div><p>{step.text}</p>{!step.done && <Link className={index === 3 ? "button-primary" : "button-secondary button-sm"} to={step.to}>{step.action}<ArrowRight size={15} /></Link>}</div></li>)}</ol></section>
    <aside className="welcome-aside">{organization.feedback && <section className="welcome-panel"><h2>Respuesta de administración</h2><p className="whitespace-pre-wrap break-words">{organization.feedback}</p><Link className="button-secondary" to="/empresa/equipo#verificacion">Revisar la solicitud<ArrowRight size={16} /></Link></section>}<section className="welcome-panel"><FilePenLine size={25} className="text-[var(--accent)]" /><h2>Una oferta clara desde el principio</h2><p>El formulario te acompaña por condiciones, responsabilidades, requisitos y proceso. Guarda un borrador antes de publicar.</p><ul className="welcome-summary">{[["Condiciones", "Salario fijo, modalidad y horario."], ["Requisitos", "Habilidades y experiencia necesarias para el trabajo."], ["Proceso", "Etapas y compromisos de respuesta que tu equipo pueda cumplir."]].map(([title, text]) => <li key={title}><Check size={17} /><div><strong>{title}</strong><span>{text}</span></div></li>)}</ul></section><section className="welcome-panel"><h2>Tu acceso también cuenta</h2><p>{state.mfaReady ? "Tu configuración actual no tiene pendiente el requisito de autenticador." : "Activa el autenticador desde Seguridad. La verificación de la empresa no sustituye la protección de tu cuenta."}</p><Link className="button-secondary" to="/seguridad">Revisar seguridad<ArrowRight size={16} /></Link><small>Presentar un NIT o completar el formulario no valida automáticamente la existencia legal de una empresa.</small></section></aside></div>}
  </div>;
}
