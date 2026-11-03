import { BriefcaseBusiness, CalendarDays, CircleDollarSign, Clock3, FileCheck2, Layers3, ListChecks } from "lucide-react";
import { CONTRACTS } from "../utils/offerQuality.js";
import { experienceLabel, minimumExperienceMonths } from "../utils/jobRequirements.js";
import { comparisonSalary } from "../utils/jobComparison.js";
import { StructuredJobText } from "./StructuredJobText.jsx";
import "../styles/external-job-content.css";

const levels = { entry: "Inicial / prácticas", junior: "Junior", mid: "Intermedio", senior: "Senior", lead: "Liderazgo" };
const order = ["information", "responsibilities", "requirements", "preferred", "conditions", "compensation", "benefits", "process"];

export function ExternalJobContent({ job }) {
  const d = job.quality_details || {}, content = job.external_content || {};
  const sections = (content.sections || []).filter((s) => s.text?.trim());
  const facts = [
    [Layers3, "Nivel del cargo", levels[d.seniority], "seniority"],
    [BriefcaseBusiness, "Experiencia mínima", minimumExperienceMonths(d) != null ? experienceLabel(d) : null, "experience_months"],
    [FileCheck2, "Tipo de contrato", CONTRACTS[d.contract_type], "contract_type"],
    [CircleDollarSign, job.salary ? "Salario en COP" : "Información salarial", job.salary || content.compensation?.status === "negotiable" ? comparisonSalary(job) : null, "salary"],
    [Clock3, "Jornada y horario", d.schedule, "schedule"],
  ];
  const found = facts.filter(([, , value]) => value).length;
  const grouped = order.map((key) => ({ key, title: sections.find((s) => s.key === key)?.title,
    text: sections.filter((s) => s.key === key).map((s) => s.text).join("\n\n") })).filter((s) => s.text);
  return <div className="external-content">
    <header className="external-content-heading"><span className="external-content-icon"><ListChecks size={23} /></span><div><p className="section-kicker">INFORMACIÓN DEL ANUNCIO</p><h2>Conoce el cargo y sus condiciones</h2><p>Organizamos el texto de la fuente para que puedas revisarlo por partes.</p></div></header>
    <div className="external-content-meta"><span><CalendarDays size={15} />{job.external_published_at ? `Publicada: ${new Date(job.external_published_at).toLocaleDateString("es-CO", { timeZone: "UTC" })}` : "Fecha original sin confirmar"}</span><span>{found} de {facts.length} condiciones identificadas</span></div>
    <dl className="external-facts">{facts.map(([Icon, label, value, key]) => <div key={key} data-known={!!value}><dt><Icon size={16} />{label}</dt><dd title={content.evidence?.[key] || undefined}>{value || "No especificado en el anuncio"}</dd></div>)}</dl>
    <p className="external-content-note">Los datos identificados proceden del anuncio. Lo que no se especifica queda pendiente de confirmar con la empresa.</p>
    {grouped.length ? grouped.map((section) => section.key === "information" && section.text.length > 1200 ?
      <details className="external-text-section external-company-context" key={section.key}><summary>{section.title}<span>Leer contexto completo</span></summary><StructuredJobText text={section.text} /></details> :
      <section className="external-text-section" key={section.key}><h3>{section.title}</h3><StructuredJobText text={section.text} /></section>) : <section className="external-text-section"><h3>Texto del anuncio</h3><StructuredJobText text={job.description} /></section>}
    {!sections.some((s) => s.key === "requirements") && job.requirements && <section className="external-text-section"><h3>Requisitos del cargo</h3><StructuredJobText text={job.requirements} /></section>}
    <footer className="external-content-footer">La publicación y la postulación se gestionan en el portal de origen. El nivel del cargo describe la experiencia solicitada; es distinto de tu compatibilidad.</footer>
  </div>;
}
