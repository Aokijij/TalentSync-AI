import { useState } from "react";
import { Check, Plus } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function LearningSkillsButton({ plan, onChanged }) {
  const [busy, setBusy] = useState(false), [added, setAdded] = useState(false), [error, setError] = useState("");
  if (!plan.resource || plan.status !== "completed") return null;
  const complete = plan.skills_added || added;
  return <div className="learning-skills-choice"><button type="button" className="button-secondary button-sm" disabled={busy || complete} onClick={async () => { setBusy(true); setError(""); try { await api.post(`/learning/plans/${plan.resource.id}/skills`); setAdded(true); await onChanged?.(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); } }}>{complete ? <Check size={15} /> : <Plus size={15} />}{complete ? "Habilidades en tu perfil" : "Añadir habilidades a mi perfil"}</button><p>{plan.resource.skills.join(" · ")} · Habilidades declaradas por ti.</p>{error && <p role="alert" className="text-[var(--error)]">{error}</p>}</div>;
}
