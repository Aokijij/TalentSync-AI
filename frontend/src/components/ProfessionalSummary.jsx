import { useEffect, useRef, useState } from "react";
import { Check, LoaderCircle, PencilLine, RefreshCw, Sparkles } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { summaryInput } from "../utils/professionalSummary.js";
import { CoachDialog } from "./CoachDialog.jsx";

export function ProfessionalSummary({ profile, editing, onChange, onEdit }) {
  const [generating, setGenerating] = useState(false);
  return <div className="professional-summary">
    <div className="professional-summary-actions"><button type="button" className="button-secondary button-sm" onClick={onEdit}><PencilLine size={15} />{editing ? "Escribir mi texto" : "Editar mi texto"}</button><button type="button" className="summary-ai-button" aria-haspopup="dialog" onClick={() => setGenerating(true)}><Sparkles size={16} />Generar con IA local</button></div>
    {editing ? <label className="professional-summary-field">Tu resumen profesional<textarea id="professional-summary-text" className="field-control" rows={6} maxLength={3000} value={profile.experience || ""} onChange={(event) => onChange(event.target.value)} placeholder="Cuenta qué haces, en qué tienes experiencia y qué puedes aportar. Usa tus propias palabras." /><span><small>El texto que elijas se conservará al guardar tu perfil.</small><small>{(profile.experience || "").length}/3000</small></span></label> : <p className="professional-summary-text">{profile.experience || "Preséntate con tus propias palabras o prepara una propuesta con la IA local a partir de tu perfil."}</p>}
    {editing && <p className="professional-summary-save-note"><Check size={14} />Pulsa «Guardar cambios» en tu perfil cuando termines.</p>}
    {generating && <SummaryGenerationDialog profile={profile} onClose={() => setGenerating(false)} onApply={(text) => { onChange(text); onEdit(); setGenerating(false); }} />}
  </div>;
}

function SummaryGenerationDialog({ profile, onClose, onApply }) {
  const [tone, setTone] = useState("professional"), [proposal, setProposal] = useState(""), [busy, setBusy] = useState(false), [error, setError] = useState(""), [source, setSource] = useState("");
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);
  const data = summaryInput(profile), currentSource = JSON.stringify(data), outdated = source && source !== currentSource;
  async function generate() {
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    setBusy(true); setError("");
    try {
      const response = await api.post("/profiles/me/summary/generate", { tone, profile: data }, { signal: controller.signal, timeout: 120000, __skipRetry: true });
      if (!controller.signal.aborted) { setProposal(response.data.text); setSource(currentSource); }
    } catch (failure) { if (!controller.signal.aborted) setError(getApiErrorMessage(failure, "No pudimos generar la propuesta. Tu resumen se conserva.")); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <CoachDialog open title="Un nuevo resumen para tu perfil" className="summary-generation-dialog" onClose={onClose}><div className="summary-generation-body">
    <p className="summary-generation-intro">La IA local redactará una propuesta con tu profesión, funciones, formación y habilidades. Puedes editarla antes de usarla.</p>
    <fieldset className="summary-tone-picker" disabled={busy}><legend>¿Cómo quieres presentarte?</legend>{[["professional", "Completo", "Un párrafo con tus fortalezas y trayectoria"], ["concise", "Breve", "Una presentación directa y compacta"]].map(([value, title, description]) => <label key={value} className={tone === value ? "selected" : ""}><input type="radio" name="summary-tone" checked={tone === value} onChange={() => setTone(value)} /><span><strong>{title}</strong><small>{description}</small></span></label>)}</fieldset>
    <button type="button" className="button-primary summary-generate-action" disabled={busy} onClick={generate}>{busy ? <LoaderCircle size={17} className="animate-spin" /> : proposal ? <RefreshCw size={17} /> : <Sparkles size={17} />}{busy ? "Redactando con IA local…" : proposal ? "Generar otra versión" : "Generar propuesta"}</button>
    {busy && <p role="status" className="summary-generation-status">El modelo se ejecuta en este equipo. Puede tardar un momento; tu texto actual se conserva.</p>}
    {error && <p role="alert" className="summary-generation-error">{error}</p>}
    {proposal && <label className="professional-summary-field summary-proposal">Propuesta editable<textarea className="field-control" aria-label="Propuesta de resumen profesional" value={proposal} rows={7} maxLength={3000} disabled={busy} onChange={(event) => setProposal(event.target.value)} /><span><small>Revisa que cada frase refleje tu experiencia real.</small><small>{proposal.length}/3000</small></span></label>}
    {outdated && <p role="alert" className="summary-generation-error">Tu perfil cambió. Genera una nueva propuesta para usar la información actualizada.</p>}
    <footer><p>Se incorporará al borrador de tu perfil. Después podrás guardar los cambios.</p><div><button type="button" className="button-secondary" onClick={onClose}>Cancelar</button><button type="button" className="button-primary" disabled={busy || !proposal.trim() || !!outdated} onClick={() => onApply(proposal.trim())}><Check size={16} />Usar este texto</button></div></footer>
  </div></CoachDialog>;
}
