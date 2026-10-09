import { Bookmark, BookmarkCheck, EyeOff, RotateCcw } from "lucide-react";
import { useFeedback } from "../contexts/FeedbackContext.jsx";

export function JobInterestButtons({ job, interests }) {
  const { confirm } = useFeedback();
  if (!interests.enabled) return null;
  const state = interests.byId.get(job.id);
  return <div className="job-interest-actions">
    <button disabled={interests.busy} aria-pressed={state === true} className={state === true ? "saved" : ""} onClick={() => state === true ? interests.remove(job.id) : interests.save(job.id, true)}>{state === true ? <BookmarkCheck size={16} /> : <Bookmark size={16} />}{state === true ? "Guardada" : "Guardar"}</button>
    <button disabled={interests.busy} onClick={async () => { if (state === false) { interests.remove(job.id); return; } if (await confirm({ title: "Ocultar esta vacante", description: "Dejarás de verla en tus sugerencias. Puedes recuperarla desde la pestaña Ocultas cuando quieras.", confirmLabel: "Ocultar vacante" })) interests.save(job.id, false); }}>{state === false ? <RotateCcw size={16} /> : <EyeOff size={16} />}{state === false ? "Restaurar" : "Ocultar"}</button>
  </div>;
}

export function InterestsToggle({ interests }) {
  const { confirm } = useFeedback();
  return <div className="interest-toggle-container"><button className="interest-toggle" type="button" role="switch" aria-checked={interests.enabled} disabled={interests.busy || !interests.privacy} title="Solo usa decisiones explícitas. Al desactivar se eliminan las decisiones y los modelos experimentales que las incluyan." onClick={async () => { const enabled = !interests.enabled; if (!enabled && !await confirm({ title: "Desactivar la personalización", description: "Se borrarán las decisiones de guardar y ocultar y los modelos experimentales que las incluyan.", confirmLabel: "Desactivar", destructive: true })) return; interests.consent(enabled); }}><span className="switch-track" aria-hidden="true"><span /></span><span>Usar mis decisiones de guardar u ocultar para personalizar recomendaciones</span></button>{interests.error && <p role="alert" className="mt-2 text-xs text-[var(--error)]">{interests.error}</p>}</div>;
}
