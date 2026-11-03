import { useState } from "react";
import { CheckCircle2, FileBadge, Plus } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";

export function CourseEvidence({ plan, onChanged }) {
  const { notify } = useFeedback();
  const [saved, setSaved] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const added = saved || plan.evidence_added;
  async function add() {
    setBusy(true); setError("");
    try {
      await api.post(`/learning/plans/${plan.resource.id}/evidence`, {}, { __quiet: true });
      setSaved(true); await onChanged?.();
      notify("La formación aparece en tus evidencias con su proveedor y habilidades.", { title: "Formación añadida" });
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="course-training-evidence"><FileBadge size={23} /><div><h3>Respalda tu formación</h3><p>Puedes mostrar este curso y sus habilidades aunque no tengas certificado. Se identifica como formación declarada por ti.</p></div><button className="button-secondary" disabled={busy || added} onClick={add}>{added ? <CheckCircle2 size={17} /> : <Plus size={17} />}{added ? "En tus evidencias" : busy ? "Añadiendo…" : "Añadir formación a evidencias"}</button>{error && <p role="alert">{error}</p>}</section>;
}
