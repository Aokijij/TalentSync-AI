import { ArrowRight, CalendarDays } from "lucide-react";
import { Link } from "react-router-dom";
import { dashboardDate } from "../utils/dashboardData.js";

export function DashboardStat({ icon: Icon, label, value, detail, to, tone = "accent" }) {
  return <Link className={`dashboard-stat ${tone}`} to={to}><span className="dashboard-stat-icon"><Icon size={20} /></span><div><span>{label}</span><strong>{value}</strong><small>{detail}</small></div><ArrowRight size={16} /></Link>;
}
export function DashboardSection({ title, subtitle, to, action = "Ver todo", children, className = "" }) {
  return <section className={`dashboard-panel ${className}`}><header><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{to && <Link to={to}>{action}<ArrowRight size={15} /></Link>}</header><div className="dashboard-panel-body">{children}</div></section>;
}
export function DashboardEmpty({ title, description, to, action }) {
  return <div className="dashboard-empty"><strong>{title}</strong><p>{description}</p>{to && <Link to={to}>{action}<ArrowRight size={15} /></Link>}</div>;
}
export function DashboardAgenda({ items, company = false, jobsById = new Map() }) {
  return <div className="dashboard-agenda">{items.map((row) => <Link key={row.id} to={company ? `/empresa/postulaciones?job=${row.job_id}&focus=${row.id}` : `/procesos/${row.id}`}><span><CalendarDays size={19} /></span><div><strong>{dashboardDate(row.interview_at)}</strong><p>{company ? row.candidate_name || "Candidato" : row.job_title || jobsById.get(row.job_id)?.title || "Entrevista"}</p><small>{company ? row.job_title || jobsById.get(row.job_id)?.title : row.company_name}</small></div><ArrowRight size={15} /></Link>)}</div>;
}
