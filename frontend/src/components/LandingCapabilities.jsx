import { useState } from "react";
import { BookOpen, ShieldCheck, UsersRound } from "lucide-react";
import { platformGuide } from "../constants/platformGuide.js";
import { WorkspaceTabs } from "./ui/Panel.jsx";
import "../styles/platform-guide.css";

export function LandingCapabilities() {
  const [role, setRole] = useState("candidate");
  return <>
    <section className={`public-capabilities public-container role-${role}`} aria-labelledby="capabilities-title" id="funcionalidades"><header className="public-section-heading"><p className="section-kicker">UN ESPACIO PARA CADA ROL</p><h2 id="capabilities-title">Conoce todo lo que puedes hacer.</h2><p>Explora las herramientas del candidato, la empresa y los equipos autorizados de administración.</p></header><WorkspaceTabs id="public-roles" label="Funcionalidades por rol" value={role} onChange={setRole} items={[["candidate", "Candidatos", BookOpen], ["company", "Empresas", UsersRound], ["admin", "Administración", ShieldCheck]]} /><div role="tabpanel" id={`public-roles-panel-${role}`} aria-labelledby={`public-roles-tab-${role}`} className="public-capability-grid">{platformGuide[role].map((item) => <article key={item.id}><h3>{item.title}</h3><p>{item.summary}</p></article>)}</div></section>
    <section className="public-differences public-container" aria-labelledby="differences-title"><header className="public-section-heading"><p className="section-kicker">MÁS ALLÁ DE ENCONTRAR UNA VACANTE</p><h2 id="differences-title">Lo que distingue tu recorrido en TalentSync.</h2><p>La búsqueda conecta con preparación, evidencias y seguimiento para que cada decisión tenga más contexto.</p></header><ol>{[
      ["01", "Seguimiento con compromisos de respuesta", "Consulta etapa, historial y plazos. Los atrasos se señalan y los procesos pueden pausarse sin convertir el vencimiento en un rechazo automático."],
      ["02", "Compatibilidad que puedes contrastar", "Revisa motivos y requisitos en lugar de quedarte con un porcentaje. Distingue lo declarado de los fundamentos evaluados; la puntuación no es una probabilidad de contratación."],
      ["03", "Aprendizaje con resultados separados", "Organiza cursos, resuelve prácticas y conserva sus correcciones. Una práctica, un curso finalizado y un certificado aportado tienen significados distintos."],
      ["04", "Contrataciones con condiciones claras", "Las ofertas pasan por criterios de calidad. La empresa organiza candidaturas, entrevistas y decisiones; administración revisa organizaciones y el catálogo."],
    ].map(([number, title, text]) => <li key={number}><span>{number}</span><div><h3>{title}</h3><p>{text}</p></div></li>)}</ol></section>
  </>;
}
