import { useId, useState } from "react";
import { Check, CircleAlert, FilePenLine, Globe2, Pause, Save, Send, ShieldCheck, XCircle } from "lucide-react";
import "../styles/external-publication.css";
import { api, getApiErrorMessage } from "../api/client.js";

const states = { active: "Publicada", draft: "Borrador", paused: "Pausada", closed: "Cerrada" };
export function ExternalJobPublication({ data, busy, setBusy, onError, onSaved }) {
  const group = useId();
  const [status, setStatus] = useState(data.status in states ? data.status : "draft"), [note, setNote] = useState("");
  const [manual, setManual] = useState(false);
  const current = data.status === "active" ? data.external_available ? "Visible en el catálogo" : data.moderation_status === "held" ? "Retirada por administración" : "En revisión, todavía no visible" : states[data.status] || data.status;
  const blockers = (data.review?.checks || []).slice(1).filter(row => !row.passed);
  async function submit(event) {
    event.preventDefault(); setBusy(true); onError("");
    try {
      const { data: updated } = await api.patch(`/admin/jobs/${data.id}/catalog-status`, { status, revision: data.moderation_revision, note: note.trim(), ...(status === "active" && manual ? { manual_verification: { confirmed_open: true, source_url: data.external_url, note: note.trim() } } : {}) }, { __skipRetry: true });
      await onSaved(updated);
    } catch (error) { onError(getApiErrorMessage(error)); } finally { setBusy(false); }
  }
  return <form className="admin-editorial-form external-publication" onSubmit={submit}>
    <header><span className="publication-icon"><Globe2 size={23} /></span><div><h4>Publicación en TalentSync</h4><p>Elige cómo se mostrará esta oferta en el catálogo.</p></div></header>
    <div className="publication-current"><span>Estado actual</span><strong>{current}</strong></div>
    <fieldset className="publication-options" disabled={busy}><legend>Estado en TalentSync</legend><div>{[
      ["active", Globe2, "Visible en el catálogo y las recomendaciones"], ["draft", FilePenLine, "Guardar para seguir completando"], ["paused", Pause, "Ocultar temporalmente del catálogo"], ["closed", XCircle, "Finalizar su publicación en TalentSync"],
    ].map(([value, Icon, description]) => <label key={value} data-selected={status === value}><input type="radio" name={group} aria-label={states[value]} checked={status === value} onChange={() => setStatus(value)} /><span className="publication-choice-icon"><Icon size={20} /></span><span><strong>{states[value]}</strong><small>{description}</small></span><span className="publication-choice-check">{status === value && <Check size={12} />}</span></label>)}</div></fieldset>
    {status === "active" && blockers.length > 0 && <div className="publication-pending"><CircleAlert size={20} /><div><strong>Antes de publicar</strong><ul>{blockers.map(row => <li key={row.label}>{row.label.includes("Vigencia") ? "Falta confirmar que la oferta siga abierta en la fuente." : row.label.includes("Fecha de publicación") ? "Revisa la fecha original y añade al menos tres habilidades distintas." : row.label.includes("Funciones") ? "Completa las funciones y los requisitos de la oferta." : row.label.includes("plazo") ? "Revisa la fecha de cierre de la oferta." : row.label}</li>)}</ul><p>Completa el contenido pendiente. Para la vigencia, utiliza Comprobar fuente o registra abajo tu revisión manual.</p></div></div>}

    {status === "active" && <section className="publication-manual-review"><div><ShieldCheck size={21} /><div><h5>Revisión manual de la fuente</h5><p>Si la comprobación automática no confirma la vigencia, puedes revisarla directamente.</p></div></div><a className="button-secondary button-sm" href={data.external_url} target="_blank" rel="noreferrer">Abrir oferta original ↗</a><label><input type="checkbox" checked={manual} disabled={busy} onChange={event => setManual(event.target.checked)} /><span>He abierto la oferta original y confirmado que sigue recibiendo postulaciones.</span></label><small>Se registrarán tu cuenta, la fecha y el motivo. La revisión es válida durante 72 horas; las comprobaciones automáticas continúan y un cierre confirmado retira la oferta.</small>{data.external_verification_method === "manual" && data.external_manual_verified_until && <p role="status">Revisión manual vigente hasta {new Date(`${data.external_manual_verified_until.replace(/Z$/, "")}Z`).toLocaleString("es-CO")}.</p>}</section>}
    {data.external_manual_note && <div className="publication-current"><span>Última revisión manual · Cuenta #{data.external_manual_verified_by}</span><p>{data.external_manual_note}</p></div>}
    <label>Motivo de la decisión<textarea className="field-control" rows={3} minLength={status === "active" && manual ? 20 : 5} maxLength={2000} required placeholder={status === "active" && manual ? "Describe cómo confirmaste que la oferta original sigue abierta (mínimo 20 caracteres)" : "Explica qué revisaste y por qué eliges este estado"} disabled={busy} value={note} onChange={event => setNote(event.target.value)} /></label>
    <footer><div><strong>{status === "active" ? "La publicación conserva los controles de la fuente" : "La oferta quedará fuera del catálogo"}</strong><small>Podrás seguir editando su contenido. La decisión se guarda en el historial.</small></div><button type="submit" className="button-primary" disabled={busy}>{status === "active" ? <Send size={16} /> : <Save size={16} />}{busy ? "Guardando…" : status === "active" ? "Publicar vacante" : "Guardar estado"}</button></footer>
  </form>;
}
