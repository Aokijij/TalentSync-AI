import { useState } from "react";
import { CheckCircle2, Plus, Sparkles } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { skillName } from "../utils/skillNames.js";

export function CourseSkillClaim({ plan, onSaved }) {
  const { confirm, notify } = useFeedback();
  const remaining = plan.remaining_skills || (plan.skills_added ? [] : plan.resource.skills);
  const [selected, setSelected] = useState([]), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const chosen = selected.filter((skill) => remaining.includes(skill));
  async function add() {
    if (!chosen.length || !await confirm({ title: "Añadir habilidades a tu perfil", description: `Confirmas que ahora sabes utilizar: ${chosen.map(skillName).join(", ")}. Se añadirán como declaradas por ti. No son una certificación ni un resultado de los retos.`, confirmLabel: "Añadir habilidades" })) return;
    setBusy(true); setError("");
    try {
      const { data } = await api.post(`/learning/plans/${plan.resource.id}/skills`, { skills: chosen, confirm: true }, { __quiet: true });
      await onSaved(data, true); setSelected([]);
      notify("Se incorporaron como habilidades declaradas por ti.", { title: "Habilidades añadidas" });
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section className="course-skill-claim"><header><span className="learning-area-icon"><Sparkles size={23} /></span><div><p className="section-kicker">LO QUE APRENDISTE</p><h3>{remaining.length ? "Lleva tus habilidades al perfil" : "Tus habilidades ya están en el perfil"}</h3><p>{remaining.length ? "Selecciona solo las que ahora sabes utilizar. Puedes añadirlas aunque el curso no tenga certificado." : "Puedes seguir practicándolas con los retos del curso. Sus resultados se guardan por separado."}</p></div></header>
    {remaining.length ? <><fieldset disabled={busy}><legend className="sr-only">Habilidades aprendidas en el curso</legend><div className="course-skill-options">{remaining.map((skill) => <label key={skill} className={chosen.includes(skill) ? "is-selected" : ""}><input type="checkbox" checked={chosen.includes(skill)} onChange={(event) => setSelected((current) => event.target.checked ? [...current, skill] : current.filter((item) => item !== skill))} /><span>{skillName(skill)}</span></label>)}</div></fieldset><footer><span>{chosen.length} {chosen.length === 1 ? "habilidad seleccionada" : "habilidades seleccionadas"}</span><button className="button-primary course-flow-button" disabled={busy || !chosen.length} onClick={add}><Plus size={17} />{busy ? "Añadiendo…" : "Añadir a mi perfil"}</button></footer></> : <p className="course-skills-done"><CheckCircle2 size={18} />Ya están incluidas en tu perfil.</p>}
    {error && <p role="alert" className="welcome-alert">{error}</p>}
  </section>;
}
