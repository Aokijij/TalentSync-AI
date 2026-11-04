import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight, BookOpen, Building2, CheckCircle2, FilePenLine, LockKeyhole, Mail, RotateCcw } from "lucide-react";
import { useAuth } from "../hooks/useAuth.js";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { companyWelcomeState } from "../utils/welcome.js";
import "../styles/welcome.css";

export function CompanyWelcomePage() {
  const { user, accessOptions } = useAuth(), location = useLocation();
  const [organization, setOrganization] = useState(null), [error, setError] = useState(""), [revision, setRevision] = useState(0);
  useEffect(() => {
    const controller = new AbortController(); setError("");
    api.get("/organization/access", { signal: controller.signal }).then(({ data }) => { if (!controller.signal.aborted) setOrganization(data); }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure, "No pudimos consultar tu organización.")); });
    return () => controller.abort();
  }, [revision]);
  const state = organization ? companyWelcomeState(organization, user, accessOptions) : null;
  const internal = organization?.verification_required === false;
  const active = organization?.active !== false;
  const next = !user.email_verified ? { title: "Confirma el correo de tu cuenta", text: "Abre Seguridad y solicita el enlace de confirmación. Después podrás continuar con la protección de tu acceso.", to: "/seguridad#security-email", action: "Confirmar mi correo" }
    : state && !state.mfaReady ? { title: "Protege tu acceso empresarial", text: "Configura el autenticador con tu contraseña, escanea el código QR y confirma los seis dígitos. Es el paso necesario para abrir las funciones de contratación.", to: "/seguridad#security-mfa", action: "Configurar autenticador" }
    : !active ? { title: "Tu permiso de equipo necesita revisión", text: "Consulta el motivo y solicita al propietario que revise tu acceso.", to: "/empresa/equipo", action: "Consultar mi acceso" }
    : state && !state.allowed ? { title: organization.verification_status === "suspended" ? "Revisa la suspensión de tu organización" : "Completa la revisión de la empresa", text: state.reviewText, to: "/empresa/equipo#verificacion", action: state.submitted ? "Consultar revisión" : "Preparar la solicitud" }
    : { title: "Tu espacio está preparado para trabajar", text: "Revisa las ofertas, consulta sus requisitos y prepara los procesos del equipo. Cada vacante conserva su revisión de calidad antes de publicarse.", to: "/empresa", action: "Entrar al panel" };
  return <div className="company-welcome space-y-5">
    <PageHeader kicker="INICIO · EMPRESA" title="Prepara tu espacio de empresa" description="Tu acceso, tu organización y el siguiente paso, en un solo lugar." actions={<Link className="button-secondary" to="/guia"><BookOpen size={16} />Guía de uso</Link>} />
    {error && <div className="welcome-alert" role="alert"><p>{error}</p><button type="button" className="button-secondary" onClick={() => setRevision(v => v + 1)}><RotateCcw size={16} />Reintentar</button></div>}
    {!organization && !error && <p role="status">Consultando tu organización…</p>}
    {state && <>
      <section className="company-next-step surface-card" aria-labelledby="company-next-title"><span className="company-start-icon">{state.ready && active ? <CheckCircle2 size={27} /> : <LockKeyhole size={27} />}</span><div><p className="section-kicker">{organization.name || organization.company_name || "Tu organización"} · {state.ready && active ? "Acceso habilitado" : "Siguiente paso"}</p><h2 id="company-next-title">{next.title}</h2><p>{next.text}</p>{location.state?.accessStep && !state.mfaReady && <p className="company-start-note" role="status">La sección que elegiste requiere completar primero la protección del acceso.</p>}</div><Link className="button-primary" to={next.to}>{next.action}<ArrowRight size={16} /></Link></section>
      <div className="company-start-grid">
        <section className="surface-card company-start-panel"><h2>Estado de preparación</h2><div className="company-start-checks">{[
          { title: "Correo de acceso", icon: Mail, done: user.email_verified, text: user.email_verified ? "Correo confirmado" : "Pendiente de confirmar", to: "/seguridad#security-email" },
          { title: "Autenticador", icon: LockKeyhole, done: state.mfaReady, text: state.mfaReady ? "Protección preparada" : "Configuración pendiente", to: "/seguridad#security-mfa" },
          { title: internal ? "Espacio interno" : "Organización", icon: Building2, done: state.allowed, text: internal ? organization.verification_status === "internal_approved" ? "Revisión interna aprobada" : "Habilitado por administración" : state.reviewLabel, to: "/empresa/equipo#verificacion" },
          { title: "Publicación", icon: FilePenLine, done: state.ready && active, text: state.ready && active ? "Puedes revisar y publicar ofertas" : "Completa los pasos pendientes", to: state.mfaReady ? "/empresa/calidad?nueva=1" : "/seguridad#security-mfa" },
        ].map(({ title, icon: Icon, done, text, to }) => <Link className="company-start-check" key={title} to={to} data-done={!!done}><Icon size={19} /><div><strong>{title}</strong><span>{text}</span></div>{done && <CheckCircle2 size={16} />}</Link>)}</div>{internal && <p className="company-start-note">Este espacio utiliza una identificación interna. Su habilitación no equivale a una verificación legal de una empresa.</p>}</section>
        <section className="surface-card company-start-panel"><h2>Tu organización</h2><p>{internal ? "Puedes solicitar una revisión operativa de TalentSync, con el enlace de la plataforma y los datos de su responsable. No necesitas inventar un NIT ni un registro mercantil." : state.owner ? "Presenta la solicitud con la identidad y los soportes reales de la empresa. Aquí podrás consultar la respuesta y las correcciones." : "El propietario presenta los soportes. Tu acceso conserva los permisos del equipo."}</p><div className="company-start-actions"><Link className="button-secondary" to={state.mfaReady ? "/empresa/equipo#verificacion" : "/seguridad#security-mfa"}>{internal ? "Revisar espacio interno" : "Consultar verificación"}<ArrowRight size={16} /></Link>{state.mfaReady && <Link className="button-secondary" to="/empresa/perfil">Ver ficha de empresa</Link>}</div>{organization.feedback && <details className="company-start-feedback"><summary>Respuesta de administración</summary><p>{organization.feedback}</p></details>}</section>
      </div>
      <section className="surface-card company-start-shortcuts"><div><h2>Empieza por una oferta clara</h2><p>Condiciones, responsabilidades, habilidades y etapas del proceso.</p></div><Link className="button-secondary" to={state.mfaReady ? "/empresa/calidad?nueva=1" : "/seguridad#security-mfa"}>Preparar un borrador<ArrowRight size={16} /></Link><Link className="button-secondary" to="/guia">Cómo usar TalentSync<BookOpen size={16} /></Link></section>
    </>}
  </div>;
}
