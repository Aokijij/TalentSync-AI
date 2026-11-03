import "../styles/offer-editing.css";
import { useRef, useState } from "react";
import { ArrowRight, Check, FilePenLine, RotateCcw, Sparkles } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { offerPayload } from "../utils/offerQuality.js";

export function OfferWritingAssistant({ draft, disabled, onApply, onStep }) {
  const [result, setResult] = useState(null), [source, setSource] = useState(""), [field, setField] = useState("description");
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [applied, setApplied] = useState({});
  const request = useRef(0);
  const payload = { ...offerPayload(draft), ...(draft.id ? { job_id: draft.id } : {}) };
  const fingerprint = JSON.stringify(payload), stale = !!result && fingerprint !== source;
  const proposal = result?.proposals.find((row) => row.field === field) || result?.proposals[0];
  async function prepare() {
    const revision = ++request.current; setBusy(true); setError("");
    try {
      const { data } = await api.post("/hiring/quality/writing", payload, { __quiet: true });
      if (revision === request.current) { setResult(data); setSource(fingerprint); setApplied({}); }
    } catch (failure) { if (revision === request.current) setError(getApiErrorMessage(failure)); }
    finally { if (revision === request.current) setBusy(false); }
  }
  function apply(text, restoring = false) {
    onApply(proposal.field, text); setSource(JSON.stringify({ ...payload, [proposal.field]: text }));
    setApplied((current) => { const next = { ...current }; if (restoring) delete next[proposal.field]; else next[proposal.field] = text; return next; });
  }
  const blocked = disabled || busy || stale;
  const hasText = !!(draft.description.trim() || draft.requirements.trim());
  return <section className="surface-card writing-workspace"><header><span><Sparkles size={23} /></span><div><h3>Presenta tu vacante con claridad</h3><p>Recibe propuestas para explicar las funciones y los requisitos con frases claras. Puedes revisarlas, editarlas y elegir qué aplicar.</p></div><button type="button" className="button-secondary button-sm" disabled={disabled || busy || !hasText} onClick={prepare}>{result ? <RotateCcw size={15} /> : <FilePenLine size={15} />}{busy ? "Preparando propuestas…" : result ? "Revisar de nuevo" : "Revisar mis textos"}</button></header>
    {!result && <><div className="writing-benefits"><span>Funciones concretas</span><span>Requisitos fáciles de entender</span><span>Propuestas editables</span></div>{!hasText && <p className="writing-start">Escribe primero las responsabilidades o los conocimientos solicitados para preparar una propuesta.</p>}</>}
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}{stale && <p role="status" className="offer-writing-status">Has cambiado el borrador. Pulsa Revisar de nuevo para trabajar con la información actual.</p>}
    {result && <><p className="writing-notice">{result.notice}</p>{!!result.proposals.length && <nav className="workspace-tabs" aria-label="Texto que quieres mejorar">{result.proposals.map((row) => <button key={row.field} type="button" className={proposal?.field === row.field ? "active" : ""} aria-pressed={proposal?.field === row.field} onClick={() => setField(row.field)}>{row.field === "description" ? "Responsabilidades" : "Requisitos"}{applied[row.field] && <Check size={14} />}</button>)}</nav>}
      {proposal && <article className="writing-proposal"><div className="writing-changes"><h4>Cambios propuestos</h4><ul>{proposal.changes?.map((change) => <li key={change}><Check size={14} /><span>{change}</span></li>)}</ul><details><summary>Ver el texto anterior</summary><p className="whitespace-pre-line">{proposal.original || "Sin texto registrado."}</p></details></div><div className="writing-editor"><label htmlFor={`writing-${proposal.field}`}>Tu texto revisado · edítalo antes de aplicarlo</label><textarea id={`writing-${proposal.field}`} className="field-control" rows={11} value={proposal.text} disabled={blocked} onChange={(event) => setResult((current) => ({ ...current, proposals: current.proposals.map((row) => row.field === proposal.field ? { ...row, text: event.target.value } : row) }))} /><footer><button type="button" className="button-primary button-sm" disabled={blocked || !proposal.text.trim() || draft[proposal.field] === proposal.text} onClick={() => apply(proposal.text)}><ArrowRight size={15} />{draft[proposal.field] === proposal.text ? "Aplicado al borrador" : "Aplicar este texto"}</button>{applied[proposal.field] && <button type="button" className="writing-undo" disabled={blocked} onClick={() => apply(proposal.original || "", true)}><RotateCcw size={14} />Restaurar texto anterior</button>}</footer><p>Al aplicarlo, el texto pasa al formulario. Después guarda el borrador o publica la oferta.</p></div></article>}
      {!!result.questions.length && <div className="writing-questions"><h4>Detalles que harían tu oferta más clara</h4>{result.questions.map((question) => <button className="offer-writing-question" type="button" key={question.text} onClick={() => onStep(question.step)}>{question.text}<ArrowRight size={16} /></button>)}</div>}
    </>}
  </section>;
}
