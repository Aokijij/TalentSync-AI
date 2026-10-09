import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { LearningResourceCard } from "./LearningResourceCard.jsx";

export function VacancyLearningPanel({ jobId }) {
  const [plans, setPlans] = useState([]);
  const [showAll, setShowAll] = useState(false);
  const [data, setData] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  useEffect(() => { let current = true; setData(null); api.get("/learning/plans").then(({ data }) => { if (current) setPlans(data); }).catch((failure) => { if (current) setError(getApiErrorMessage(failure)); }); api.get(`/learning/jobs/${jobId}`).then(({ data }) => { if (current) setData(data); }).catch((failure) => { if (current) setError(getApiErrorMessage(failure)); }); return () => { current = false; }; }, [jobId]);
  return <section className="space-y-3"><h3 className="font-bold">Formación para reforzar tu perfil</h3>{error && <p role="alert" className="text-[var(--error)]">{error}</p>}{notice && <p role="status">{notice}</p>}{!data && !error && <p className="text-sm">Buscando formación para los requisitos pendientes…</p>}{data && <>
    <p className="text-sm">{data.gaps.length ? `Refuerza: ${data.gaps.map((row) => row.skill).join(", ")}.` : "Tu perfil declara todas las habilidades solicitadas. Puedes respaldarlas con evidencias o evaluaciones."}</p>
    {data.resources.length > 0 ? <div className="space-y-2">{(showAll ? data.resources : data.resources.slice(0, 2)).map((resource) => <LearningResourceCard compact key={resource.id} resource={resource} inPlan={plans.some((plan) => plan.resource?.id === resource.id)} busy={busy || plans.filter((plan) => plan.status !== "completed").length >= 3} onPlan={async (id) => { setBusy(true); setError(""); try { setPlans((await api.put(`/learning/plans/${id}`, { status: "in_progress" })).data); setNotice("Añadido a tu plan de aprendizaje"); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }} />)}</div> : data.gaps.length > 0 && <p className="text-sm text-[var(--muted)]">Todavía no hay formación revisada para estas habilidades. Busca un curso con práctica y evaluación de {data.gaps.slice(0, 3).map((row) => row.skill).join(", ")}; comprueba temario, nivel y vigencia antes de inscribirte.</p>}
    {data.resources.length > 2 && <button className="text-xs text-[var(--accent)]" onClick={() => setShowAll(!showAll)}>{showAll ? "Mostrar menos" : `Ver ${data.resources.length - 2} recursos más`}</button>}
    <p className="text-xs text-[var(--muted)]">Los recursos se relacionan por habilidades pendientes. Completar un curso no acredita automáticamente dominio ni garantiza contratación.</p><div className="flex flex-wrap gap-4 text-sm"><Link className="text-[var(--accent)]" to="/aprendizaje">Mi plan y evaluaciones</Link><Link className="text-[var(--accent)]" to="/perfil#evidencias">Respaldar habilidades en mi perfil</Link></div>
  </>}</section>;
}
