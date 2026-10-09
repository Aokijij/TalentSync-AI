import { ShieldCheck, Clock3, Flag, BriefcaseBusiness, Info } from "lucide-react";

export function TrustCard({ data }) {
  const measured = data.score != null;
  return <section className="surface-card trust-summary">
    <div className="trust-heading"><span className="trust-symbol"><ShieldCheck size={28} /></span><div><p className="section-kicker">Comportamiento en TalentSync</p><h2 className="mt-1 text-xl font-bold">{data.company_name || data.name}</h2></div><span className="status-chip">{data.visibility_reduced ? "Requiere atención" : "Visibilidad normal"}</span></div>
    <div className="trust-score"><strong>{measured ? data.score : "—"}<small>{measured ? " / 100" : " Aún sin valoración"}</small></strong><p>{measured ? "Índice basado en procesos medidos y hechos confirmados." : "La valoración aparecerá cuando haya suficientes procesos medidos."}</p></div>
    <div className="trust-metrics">{[[BriefcaseBusiness, data.measured_processes, "Procesos medidos"], [Clock3, data.missed_deadlines, "Plazos vencidos"], [Flag, data.confirmed_incidents, "Incidencias confirmadas"]].map(([Icon, value, label]) => <div key={label}><Icon size={19} /><strong>{value}</strong><span>{label}</span></div>)}</div>
    <details className="text-xs text-[var(--muted)]"><summary className="inline-flex cursor-pointer items-center gap-2"><Info size={15} />Cómo se calcula esta valoración</summary><p className="mt-3 leading-6">{data.notice}</p></details>
  </section>;
}
