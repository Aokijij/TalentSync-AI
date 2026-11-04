import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowDown, ArrowRight, BriefcaseBusiness, CalendarDays, Check, CheckCheck, ChevronRight, CircleCheck, Compass, Files, GitBranch, Mail, ShieldCheck, Sparkles, UsersRound } from "lucide-react";
import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { ThemeToggle } from "../components/ThemeToggle.jsx";
import { LandingCapabilities } from "../components/LandingCapabilities.jsx";
import { publicLegal } from "../constants/publicLegal.js";
import "../styles/welcome.css";
import "../styles/public-legal.css";
import "../styles/role-landing.css";

const requirements = ["Excel", "Análisis de datos", "Comunicación"];
const copy = {
  candidate: {
    kicker: "TU TALENTO TIENE UN SIGUIENTE PASO",
    title: <>Encuentra tu lugar.<br /><em>Avanza con claridad.</em></>,
    lead: "Conoce las oportunidades que conectan con tu perfil, prepara tu postulación y sigue cada etapa. Tu trayectoria merece más que quedarse en un archivo.",
    action: "Crear mi perfil", registration: "/registro", login: "/login",
    pillars: [[Files, "Tu trayectoria", "Un perfil que reúne lo que puedes aportar."], [Sparkles, "Tu preparación", "Habilidades, formación y evidencias conectadas."], [GitBranch, "Tu recorrido", "Postulaciones e entrevistas con seguimiento."]],
    differenceTitle: "Algo más que enviar tu hoja de vida.",
    differences: [["Entiende tus oportunidades", "La compatibilidad se acompaña de motivos y requisitos que puedes contrastar; no es una promesa de contratación."], ["Aprende desde una brecha concreta", "Relaciona las habilidades que buscas reforzar con cursos y retos. Tu progreso conserva su contexto."], ["Sigue el hilo de cada proceso", "Etapas, fechas, cambios y comunicaciones en un recorrido. Un plazo vencido no se convierte automáticamente en rechazo."]],
    steps: [["Da contexto a tu talento", "Completa tu perfil o sube el CV y revisa la información extraída."], ["Elige con información", "Compara ofertas, prepara tu versión del CV y confirma la postulación."], ["Acompaña tu siguiente paso", "Revisa avances, prepara la entrevista y continúa tu formación."]],
  },
  company: {
    kicker: "CONTRATA CON UN PROCESO QUE SE ENTIENDE",
    title: <>Encuentra talento.<br /><em>Construye tu equipo.</em></>,
    lead: "Publica oportunidades claras, organiza las candidaturas y coordina las decisiones del equipo. Cada persona, cada entrevista y cada respuesta tienen su lugar.",
    action: "Registrar mi empresa", registration: "/empresa/registro", login: "/empresa/login",
    pillars: [[BriefcaseBusiness, "Ofertas claras", "Requisitos y condiciones desde el principio."], [UsersRound, "Talento organizado", "Revisión inicial y procesos activos separados."], [CalendarDays, "Un equipo coordinado", "Entrevistas, evaluaciones y próximos pasos."]],
    differenceTitle: "Menos desorden. Más contexto para decidir.",
    differences: [["Revisa el volumen sin perder el foco", "Una bandeja para las nuevas candidaturas y un tablero para las personas que avanzan."], ["Contrasta señales, conserva el criterio", "La compatibilidad ayuda a priorizar evidencias. La decisión de selección corresponde a tu equipo."], ["Comunica cada siguiente paso", "Gestiona las etapas, los compromisos de respuesta y las entrevistas con un historial compartido del proceso."]],
    steps: [["Presenta tu empresa", "Registra la organización y completa la información necesaria para su revisión."], ["Prepara una buena oferta", "Explica qué necesita el rol, sus condiciones y cómo será el proceso."], ["Lleva la selección en equipo", "Revisa talento, coordina entrevistas y comunica las decisiones."]],
  },
};

export function LandingPage({ informational = false, role = "candidate" }) {
  const company = role === "company", content = copy[role];
  useEffect(() => {
    const previous = document.title;
    document.title = "TalentSync";
    window.scrollTo(0, 0);
    return () => { document.title = previous; };
  }, [company]);
  return <div className={`public-site role-landing role-${role}`}>
    <a className="app-skip-link" href="#public-content">Saltar al contenido</a>
    <header className="public-header public-container"><Link to={company ? "/empresas" : "/"} aria-label="TalentSync, inicio"><BrandLogo subtitle={company ? "PARA EMPRESAS" : "TU SIGUIENTE PASO"} /></Link>
      <nav aria-label="Elige tu espacio" className="role-audience-nav"><Link to="/candidatos" aria-current={!company ? "page" : undefined}><Compass size={16} />Para candidatos</Link><Link to="/empresas" aria-current={company ? "page" : undefined}><BriefcaseBusiness size={16} />Para empresas</Link></nav>
      <nav aria-label="Navegación pública" className="role-public-tools">{informational ? <a className="role-header-contact" href={`mailto:${publicLegal.email}`}>Contacto<ArrowRight size={15} /></a> : <Link className="role-header-contact" to={content.login}>Iniciar sesión<ArrowRight size={15} /></Link>}<ThemeToggle compact /></nav>
    </header>
    <main id="public-content" tabIndex={-1}>
      <section className="public-hero public-container" aria-labelledby="public-title"><div className="public-hero-copy"><p className="section-kicker">{content.kicker}</p><h1 id="public-title">{content.title}</h1><p className="public-lead">{content.lead}</p>
        <div className="public-hero-actions">{informational ? <a className="button-primary" href="#funcionalidades">{company ? "Conocer las herramientas" : "Explorar mi recorrido"}<ArrowRight size={18} /></a> : <Link className="button-primary" to={content.registration}>{content.action}<ArrowRight size={18} /></Link>}<a className="button-secondary" href="#como-funciona">Cómo funciona<ArrowDown size={16} /></a></div>
        {informational ? <p className="role-availability"><span aria-hidden="true" />Estamos preparando la apertura de cuentas. Puedes conocer las herramientas y contactarnos.</p> : <p className="public-hero-note"><ShieldCheck size={16} />Tú eliges qué compartir y qué conexiones autorizar.</p>}
        <div className="role-hero-bottom"><span><CheckCheck size={16} />{company ? "Criterios claros" : "Oportunidades con contexto"}</span><span><ShieldCheck size={16} />{company ? "Accesos por rol" : "Control sobre tus datos"}</span></div>
      </div>{company ? <CompanyPreview /> : <CandidatePreview />}</section>
      <section className="role-pillars public-container" aria-label={company ? "Tu espacio de contratación" : "Tu espacio profesional"}>{content.pillars.map(([Icon, title, text]) => <article key={title}><span><Icon size={22} /></span><div><h2>{title}</h2><p>{text}</p></div></article>)}</section>
      <LandingCapabilities role={role} />
      <section className="role-differences public-container" aria-labelledby="differences-title"><div><p className="section-kicker">LO QUE HACE DIFERENTE A TALENTSYNC</p><h2 id="differences-title">{content.differenceTitle}</h2><p>{company ? "Un proceso compartido para que el equipo pueda concentrarse en las personas y sus evidencias." : "Conecta la búsqueda con tu preparación y con lo que ocurre después de postularte."}</p><Link to={company ? "/candidatos" : "/empresas"}>Conocer el espacio de {company ? "candidatos" : "empresas"}<ArrowRight size={16} /></Link></div><ol>{content.differences.map(([title, text], index) => <li key={title}><span>0{index + 1}</span><div><h3>{title}</h3><p>{text}</p></div></li>)}</ol></section>
      <section id="como-funciona" className="role-process public-container" aria-labelledby="process-title"><header className="public-section-heading"><p className="section-kicker">UN RECORRIDO CON DIRECCIÓN</p><h2 id="process-title">{company ? "De la necesidad al próximo integrante." : "Del primer interés al siguiente encuentro."}</h2></header><ol>{content.steps.map(([title, text], index) => <li key={title}><span>0{index + 1}</span><h3>{title}</h3><p>{text}</p></li>)}</ol></section>
      <section className="role-final-cta public-container"><div><p className="section-kicker">{company ? "TU PRÓXIMO EQUIPO EMPIEZA AQUÍ" : "TU SIGUIENTE PASO CUENTA"}</p><h2>{company ? "Dale claridad a tu próxima contratación." : "Haz visible lo que puedes aportar."}</h2><p>{informational ? "Escríbenos si quieres conocer más sobre TalentSync." : "Comienza con lo que necesitas hoy y completa el resto mientras avanzas."}</p></div>{informational ? <a className="button-primary" href={`mailto:${publicLegal.email}`}><Mail size={18} />Hablar con TalentSync<ArrowRight size={17} /></a> : <Link className="button-primary" to={content.registration}>{content.action}<ArrowRight size={17} /></Link>}</section>
    </main><footer className="public-footer public-container"><BrandLogo size="sm" subtitle="" /><p>{company ? "Talento, decisiones y procesos con contexto." : "Tu perfil, tus oportunidades y tu siguiente paso."}</p><Link to={company ? "/privacidad?rol=empresa" : "/privacidad"}>Privacidad</Link><Link to={company ? "/terminos?rol=empresa" : "/terminos"}>Términos de uso</Link><a href={`mailto:${publicLegal.email}`}>Contacto<ChevronRight size={14} /></a></footer>
  </div>;
}

function CandidatePreview() {
  const [demo, setDemo] = useState({ skills: ["Excel"], change: null });
  const skills = demo.skills, percentage = Math.round(skills.length / requirements.length * 100);
  function toggle(skill) {
    setDemo((current) => {
      const selected = current.skills.includes(skill);
      const next = selected ? current.skills.filter((item) => item !== skill) : [...current.skills, skill];
      return { skills: next, change: { skill, selected: !selected, delta: Math.round(next.length / requirements.length * 100) - Math.round(current.skills.length / requirements.length * 100) } };
    });
  }
  return <section className="role-preview candidate-preview" aria-labelledby="demo-title"><header><span className="role-preview-icon"><Sparkles size={22} /></span><div><p className="section-kicker">EXPLORA LA COMPATIBILIDAD</p><h2 id="demo-title">Lo que sabes tiene contexto.</h2></div><span className="role-demo-label">Demostración</span></header><div className="role-demo-job"><div><span>Oportunidad de ejemplo</span><h3>Analista de operaciones</h3><p>Organiza información, prepara reportes y comparte resultados con el equipo.</p></div><span className="role-demo-job-icon"><BriefcaseBusiness size={23} /></span></div><fieldset><legend>Prueba seleccionando habilidades</legend><div className="public-demo-choices">{requirements.map((skill) => <label key={skill}><input type="checkbox" checked={skills.includes(skill)} onChange={() => toggle(skill)} /><span>{skill}</span></label>)}</div></fieldset><div className="role-demo-match" aria-live="polite"><div><strong>{percentage}<small> %</small></strong><span>Compatibilidad ilustrativa · {skills.length} de {requirements.length} requisitos cubiertos</span></div><div className="public-demo-progress" role="progressbar" aria-label="Compatibilidad ilustrativa" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percentage}><span style={{ width: `${percentage}%` }} /></div>{demo.change && <p className="role-demo-change">{demo.change.delta > 0 ? "+" : ""}{demo.change.delta} puntos al {demo.change.selected ? "incluir" : "retirar"} {demo.change.skill}.</p>}<p><CircleCheck size={16} />{skills.length === 3 ? "Revisa las evidencias que respaldan cada habilidad." : "Identifica qué podrías reforzar para esta oportunidad."}</p></div><footer>Datos ficticios. Cada requisito tiene el mismo peso en este ejemplo. No calcula una probabilidad de contratación.</footer></section>;
}

function CompanyPreview() {
  const [stage, setStage] = useState(0), stages = ["En revisión", "Entrevista", "Decisión"];
  return <section className="role-preview company-preview" aria-labelledby="company-demo-title"><header><span className="role-preview-icon"><GitBranch size={22} /></span><div><p className="section-kicker">UN PROCESO CON CONTEXTO</p><h2 id="company-demo-title">Todo el equipo, en la misma etapa.</h2></div><span className="role-demo-label">Demostración</span></header><div className="company-demo-job"><BriefcaseBusiness size={20} /><div><span>Vacante de ejemplo</span><h3>Analista de operaciones</h3></div><small>Proceso activo</small></div><div className="company-demo-flow" role="group" aria-label="Explorar etapas de ejemplo">{stages.map((item, index) => <button type="button" key={item} aria-pressed={stage === index} onClick={() => setStage(index)}><span>{index < stage ? <Check size={14} /> : index + 1}</span>{item}</button>)}</div><article className="company-demo-person"><span className="company-demo-avatar">01</span><div><small>Candidatura de ejemplo</small><h3>Perfil de ejemplo 01</h3><span className="company-demo-stage">{stages[stage]}</span></div><div className="company-demo-next" aria-live="polite"><strong>{["Revisa sus evidencias", "Coordina el encuentro", "Comunica el siguiente paso"][stage]}</strong><p>{["Perfil y respuestas en un panel de revisión.", "Fecha, modalidad y acceso para ambas partes.", "Evaluación y respuesta en el historial."][stage]}</p></div></article><div className="company-demo-note"><CalendarDays size={19} /><div><strong>{stage === 1 ? "La entrevista tiene su propio espacio" : "Cada avance conserva su contexto"}</strong><p>{stage === 1 ? "Programada, realizada o pendiente de respuesta." : "Tu equipo puede consultar las comunicaciones del proceso."}</p></div></div><footer>Recorrido ilustrativo con datos ficticios. Esta demostración no modifica procesos ni envía avisos.</footer></section>;
}
