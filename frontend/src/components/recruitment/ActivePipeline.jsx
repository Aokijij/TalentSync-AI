import { interviewState, interviewStateLabels } from "../../utils/recruitmentState.js";
import { useEffect, useState } from "react";
import { ArrowRight, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "../../api/client.js";
import { ResponseDeadlineBadge } from "../ResponseDeadlinePanel.jsx";
import { ApplicantScore } from "./ApplicantDetail.jsx";

function PipelineColumn({ jobId, stage, search, scoreFilter, order, revision, onSelect, selectedId, count, dragged, onDrag, onMove, busy }) {
  const [result, setResult] = useState(null), [page, setPage] = useState(1), [error, setError] = useState(""), [loading, setLoading] = useState(true), [retry, setRetry] = useState(0);
  useEffect(() => { setPage(1); setResult(null); }, [jobId, search, scoreFilter, order, revision]);
  useEffect(() => {
    const controller = new AbortController(); setLoading(true); setError("");
    api.get(`/applications/jobs/${jobId}/workspace`, { params: { bucket: "active", stage: stage.id, search, score_filter: scoreFilter, order, page, page_size: 8 }, signal: controller.signal, __quiet: true }).then(({ data }) => { if (!controller.signal.aborted) setResult((current) => ({ ...data, items: page === 1 ? data.items : [...(current?.items || []), ...data.items].filter((row, i, rows) => rows.findIndex((value) => value.id === row.id) === i) })); }).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [jobId, stage.id, search, scoreFilter, order, page, revision, retry]);
  return <section className={`active-pipeline-column ${dragged && dragged.pipeline_stage !== stage.id ? "can-drop" : ""}`} aria-label={stage.title} onDragOver={(event) => { if (dragged && !busy) event.preventDefault(); }} onDrop={(event) => { event.preventDefault(); if (dragged && !busy && dragged.pipeline_stage !== stage.id) void onMove(dragged, stage.id); onDrag(null); }}><header><span /><h3>{stage.title}</h3><strong>{result?.total ?? count ?? 0}</strong></header>{result?.items.map((row) => <button key={row.id} type="button" draggable={!busy} onDragStart={(event) => { event.dataTransfer.effectAllowed = "move"; event.dataTransfer.setData("text/plain", String(row.id)); onDrag(row); }} onDragEnd={() => onDrag(null)} className={`pipeline-applicant ${selectedId === row.id ? "is-selected" : ""}`} onClick={() => onSelect(row.id)}><strong>{row.candidate_name}</strong><small>{row.profession || "Consultar perfil"}</small><span className="pipeline-stage-label">{stage.title}</span>{interviewState(row) && <small className="applicant-interview-state">{interviewStateLabels[interviewState(row)]}</small>}<ResponseDeadlineBadge application={row} /><ApplicantScore row={row} /><span>Revisar candidatura<ArrowRight size={14} /></span></button>)}{loading && <p role="status">Cargando candidatos…</p>}{error && <p role="alert">{error}<button className="button-ghost" onClick={() => setRetry((value) => value + 1)}><RefreshCw size={14} />Reintentar</button></p>}{!loading && !error && !result?.total && <p className="recruitment-empty-note">Sin candidatos en esta etapa.</p>}{result && result.items.length < result.total && <button type="button" className="button-secondary button-sm" disabled={loading} onClick={() => setPage((value) => value + 1)}>Cargar más ({result.total - result.items.length})</button>}</section>;
}

export function ActivePipeline({ stages, counts, ...props }) {
  const [dragged, setDragged] = useState(null);
  const visible = stages.filter((stage) => !["hired", "rejected", "accepted"].includes(stage.id) && (stage.id !== "submitted" || counts[stage.id]));
  return <div className="active-pipeline" role="region" aria-label="Tablero del proceso activo" tabIndex={0}>{visible.map((stage) => <PipelineColumn key={stage.id} stage={stage} count={counts[stage.id]} dragged={dragged} onDrag={setDragged} {...props} />)}</div>;
}
