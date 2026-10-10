import { useRef, useState } from "react";
import { ArrowRight, FilePenLine, RotateCcw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { offerPayload } from "../utils/offerQuality.js";

export function OfferWritingAssistant({ draft, disabled, onApply, onStep }) {
  const [result, setResult] = useState(null), [source, setSource] = useState("");
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [applied, setApplied] = useState([]);
  const request = useRef(0);
  const payload = { ...offerPayload(draft), ...(draft.id ? { job_id: draft.id } : {}) };
  const fingerprint = JSON.stringify(payload);
  const stale = !!result && fingerprint !== source;
  async function prepare() {
    const revision = ++request.current;
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/hiring/quality/writing", payload, { __quiet: true });
      if (revision === request.current) { setResult(data); setSource(fingerprint); setApplied([]); }
    } catch (failure) { if (revision === request.current) setError(getApiErrorMessage(failure)); }
    finally { if (revision === request.current) setBusy(false); }
  }
  return <section className="surface-card offer-writing">
    <h3><FilePenLine size={19} />Redacción guiada</h3><p>Convierte las misiones y habilidades que definiste en un borrador claro para este cargo.</p>
    <button type="button" className="button-secondary button-sm" disabled={disabled || busy} onClick={prepare}>{result ? <RotateCcw size={15} /> : <FilePenLine size={15} />}{busy ? "Preparando…" : result ? "Preparar de nuevo" : "Preparar borradores"}</button>
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    {stale && <p role="status" className="offer-writing-status">La oferta cambió. Prepara de nuevo para trabajar con los datos actuales.</p>}
    {result && <><p className="text-xs text-[var(--muted)]">{result.notice}</p>{result.proposals.map((proposal) => <article key={proposal.field}>
      <h4>{proposal.label}</h4><p>{proposal.basis}</p>
      <details><summary>Comparar con el texto actual</summary><p className="whitespace-pre-line">{proposal.original || "Sin texto registrado."}</p></details>
      <label className="block text-sm">Borrador editable<textarea className="field-control mt-2" rows={6} value={proposal.text} disabled={disabled || busy || stale || applied.includes(proposal.field)} onChange={(event) => setResult((current) => ({ ...current, proposals: current.proposals.map((row) => row.field === proposal.field ? { ...row, text: event.target.value } : row) }))} /></label>
      <button type="button" className="button-secondary button-sm" disabled={disabled || busy || stale || !proposal.text.trim() || applied.includes(proposal.field)} onClick={() => { onApply(proposal.field, proposal.text); setSource(JSON.stringify({ ...payload, [proposal.field]: proposal.text })); setApplied((current) => [...current, proposal.field]); }}><ArrowRight size={15} />{applied.includes(proposal.field) ? "Aplicado al borrador" : "Aplicar este texto"}</button>
    </article>)}{result.questions.map((question) => <button className="offer-writing-question" type="button" key={question.text} onClick={() => onStep(question.step)}>{question.text}<ArrowRight size={16} /></button>)}</>}
  </section>;
}
