import { Clock3, Flag, GraduationCap, ShieldCheck, Target } from "lucide-react";
import { CONTRACTS, LEVELS, salaryLabel } from "../utils/offerQuality.js";

export function OfferConditions({ job, preview = false }) {
  const d = job.quality_details;
  if (!d) return null;
  return <section className="offer-public space-y-5">
    <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="font-bold">Condiciones claras desde el inicio</h2>{job.quality_summary?.level === "A" && <span className="offer-public-badge" title="Cumple los criterios de claridad y coherencia de TalentSync. No garantiza condiciones laborales."><ShieldCheck size={15} />Oferta Nivel A · {job.quality_summary.score}/100</span>}</div>
    <dl className="offer-public-grid">{[["Salario fijo", salaryLabel(job)], ["Contrato", CONTRACTS[d.contract_type] || "Por completar"], ["Jornada y horario", d.schedule || "Por completar"], ["Nivel y experiencia", `${LEVELS[d.seniority] || "Por completar"}${d.experience_years != null ? ` · ${d.experience_years === 0 ? "Admite personas sin experiencia" : `${d.experience_years} años mínimos`}` : ""}`]].map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl>
    {d.variable_pay && <p className="offer-public-variable"><strong>Pago variable: </strong>{d.variable_pay}</p>}
    {!!d.missions?.length && <div className="offer-public-missions"><h3><Target size={17} />Tus primeras misiones</h3>{d.missions.map((row, index) => <article key={index}><span>{row.days} días desde el ingreso</span><h4>{row.outcome || "Resultado por completar"}</h4><p><strong>Cómo se evaluará: </strong>{row.measure || "Por completar"}</p>{row.skill && <small>Habilidad relacionada: {row.skill}</small>}</article>)}</div>}
    {!!d.learnable_skills?.filter((value) => value.trim()).length && <div className="offer-public-learnable"><GraduationCap size={19} /><div><h3>La empresa ofrece acompañamiento para aprender</h3><p>{d.learnable_skills.filter((value) => value.trim()).join(", ")}</p></div></div>}
    <div className="offer-public-process"><h3><Flag size={17} />Así será la selección</h3><div><span><Clock3 size={15} />{d.process_days != null ? `${d.process_days} días estimados desde la postulación` : "Duración por completar"}</span><span>{d.interview_count != null ? `${d.interview_count} entrevistas previstas` : "Entrevistas por completar"}</span><span>Respuesta por avance: {job.response_days || 7} días</span></div>{!!job.pipeline_stages?.length && <p>{job.pipeline_stages.map((row) => row.title).join(" → ")}</p>}<small>{preview ? "Estos datos se publicarán al guardar y publicar la oferta." : `Condiciones declaradas por la empresa · versión ${job.quality_revision || 1}. Los cambios se notifican a las personas con procesos en curso.`}</small></div>
  </section>;
}
