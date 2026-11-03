import { BookOpen, CalendarDays, ChartNoAxesCombined, ClipboardCheck, Files, GitBranch, Layers3, Search, ShieldCheck, Sparkles, UsersRound } from "lucide-react";

const features = {
  candidate: [
    [Search, "Oportunidades con contexto", "Filtra vacantes, guarda las que te interesan y compara sus condiciones antes de postularte."],
    [Sparkles, "Compatibilidad explicada", "Entiende qué coincide con tu perfil y qué habilidades necesitas reforzar. El porcentaje orienta tu búsqueda."],
    [Files, "Tu CV para cada oportunidad", "Organiza tu trayectoria y guarda versiones con nombre, selección de contenido y diseño propio."],
    [GitBranch, "Procesos que puedes seguir", "Consulta la etapa actual, los compromisos de respuesta y el historial de cada postulación."],
    [CalendarDays, "Tu agenda de entrevistas", "Revisa fecha, modalidad y acceso. Conecta Google Calendar si quieres mantener tus citas al día."],
    [BookOpen, "Aprende con un propósito", "Conecta cursos con retos por habilidad, registra tu avance y conserva tus certificados y resultados."],
  ],
  company: [
    [ClipboardCheck, "Ofertas claras desde el principio", "Define funciones, requisitos, condiciones y plazos para que el talento pueda decidir con información."],
    [UsersRound, "Una bandeja para revisar talento", "Busca, filtra y consulta las candidaturas sin abrir una pestaña para cada persona."],
    [Layers3, "Un tablero para quienes avanzan", "Separa la revisión inicial de las etapas activas y distingue las entrevistas pendientes de respuesta."],
    [CalendarDays, "Entrevistas bien coordinadas", "Gestiona modalidad, dirección o enlace, duración y reprogramaciones desde el proceso."],
    [ChartNoAxesCombined, "Evaluaciones con criterios", "Conserva las evaluaciones internas y contrasta evidencias para acompañar la decisión del equipo."],
    [ShieldCheck, "Tu equipo, con sus permisos", "Invita a las personas autorizadas, asigna responsabilidades y cuida el acceso a cada proceso."],
  ],
};

export function LandingCapabilities({ role = "candidate" }) {
  return <section className="role-capabilities public-container" id="funcionalidades" aria-labelledby="capabilities-title">
    <header className="public-section-heading"><p className="section-kicker">{role === "company" ? "UN ESPACIO PARA TU EQUIPO" : "HERRAMIENTAS PARA TU SIGUIENTE PASO"}</p><h2 id="capabilities-title">{role === "company" ? "Cada parte de la selección, en su lugar." : "Tu búsqueda conecta con lo que viene después."}</h2><p>{role === "company" ? "Desde la publicación hasta la respuesta final, con un recorrido que el equipo puede entender." : "Descubrir una oferta es el comienzo. Prepárate, demuestra lo que sabes y sigue tu proceso."}</p></header>
    <div className="role-feature-grid">{features[role].map(([Icon, title, text], index) => <article key={title}><div className="role-feature-heading"><span><Icon size={22} /></span><small>0{index + 1}</small></div><h3>{title}</h3><p>{text}</p></article>)}</div>
  </section>;
}
