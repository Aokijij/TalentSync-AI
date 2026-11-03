import { ArrowRight, FileText, Archive, CheckCircle2, Clock3, X } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { AreaIcon } from "./LearningVisuals.jsx";
import { CoursePlanWorkspace } from "./CoursePlanWorkspace.jsx";
import "../styles/learning-paths.css";
import "../styles/course-flow.css";

export function LearningPlanBoard({ plans, onSaved, onReload, onExplore, initialResourceId, onReturn }) {
  const { confirm } = useFeedback();
  const [leaving, setLeaving] = useState(false), [selected, setSelected] = useState(null), [showCompleted, setShowCompleted] = useState(!!initialResourceId);
  useEffect(() => { const initial = plans.find((row) => row.resource?.id === initialResourceId); if (initial?.resource?.url && !initial.resource.retired) setSelected(initial.id); }, [initialResourceId, plans]);
  const plan = plans.find((row) => row.id === selected);
  async function remove(row) {
    if (!await confirm({ title: "Retirar este recurso del plan", description: "Se retirará el recurso y su borrador. Tus resultados y evidencias ya publicadas se conservan.", confirmLabel: "Retirar recurso", destructive: true })) return;
    setLeaving(true);
    try { const { data } = await api.delete(`/learning/plans/${row.resource.id}`, { params: { version: row.version } }); await onSaved(data, false); }
    catch { /* Global feedback displays the server error. */ } finally { setLeaving(false); }
  }
  if (plan?.resource?.url && !plan.resource.retired) return <CoursePlanWorkspace plan={plan} onSaved={onSaved} onReload={onReload} onClose={() => { setShowCompleted(!!plan.progress?.course_completed); setSelected(null); onReturn?.(); }} />;
  const visible = plans.filter((row) => showCompleted ? row.status === "completed" : row.status !== "completed");
  return <section className="space-y-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-xl font-bold">Tu siguiente avance</h2><div className="plan-state-switch" role="group" aria-label="Estado de Mi plan">{[[false, "En marcha", Clock3], [true, "Finalizados", CheckCircle2]].map(([value, label, Icon]) => <button key={label} className={showCompleted === value ? "is-selected" : ""} aria-pressed={showCompleted === value} onClick={() => setShowCompleted(value)}><Icon size={17} /><span>{label}</span><strong>{plans.filter((row) => value ? row.status === "completed" : row.status !== "completed").length}</strong></button>)}</div></div>
    {!visible.length && <div className="learning-empty"><FileText size={34} /><h3 className="text-lg font-bold">{showCompleted ? "Tus cursos terminados aparecerán aquí" : "Organiza tu siguiente aprendizaje"}</h3><p>Añade cursos a tu plan y practica sus habilidades con los retos asignados.</p><button className="button-primary" onClick={onExplore}>Explorar cursos<ArrowRight size={16} /></button></div>}
    <div className="learning-catalog-grid plan-resource-grid">{visible.map((row) => <article className="learning-resource" key={row.id}><div className="flex justify-between gap-3"><span className="learning-area-icon">{row.resource?.url && !row.resource.retired ? <AreaIcon area={row.resource.category} /> : <Archive size={22} />}</span><span className="learning-tag">{!row.resource?.url || row.resource.retired ? "Recurso retirado" : row.progress?.course_completed ? "Finalizado por ti" : "En marcha"}</span></div><h3 className="text-lg font-bold">{row.resource?.title || "Recurso archivado"}</h3>{row.resource?.url && !row.resource.retired && <p className="plan-card-provider">{row.resource.provider}</p>}<p className="text-sm text-[var(--muted)]">{row.resource?.url && !row.resource.retired ? row.progress?.course_completed ? row.certificate ? "Certificado aportado. Revisa las habilidades incorporadas a tu perfil." : row.resource.details?.certificate_cost === "none" ? "Formación finalizada sin certificado anunciado. Incorpora lo aprendido a tu perfil." : "Incorpora tus habilidades y aporta el certificado si lo recibiste." : "Continúa la formación y practica sus habilidades con los retos asignados." : "Esta práctica ya no forma parte del catálogo. Sus resultados anteriores se conservan en Mis resultados. Puedes retirarla para liberar espacio en tu plan."}</p><div className="plan-card-actions">{row.resource?.url && !row.resource.retired && <button className="button-primary button-sm" onClick={() => setSelected(row.id)}>{row.progress?.course_completed ? "Revisar curso finalizado" : "Gestionar curso"}<ArrowRight size={16} /></button>}<button className="plan-remove-action" disabled={leaving} onClick={() => remove(row)}><X size={15} />Retirar del plan</button></div></article>)}</div>
  </section>;
}
