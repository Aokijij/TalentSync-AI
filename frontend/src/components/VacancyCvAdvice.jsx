import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Sparkles, ArrowUpRight, ArrowRight, RefreshCw } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CoachDialog } from "./CoachDialog.jsx";

export function VacancyCvAdvice({ jobId }) {
  const [advice, setAdvice] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [open, setOpen] = useState(false);
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), [jobId]);
  async function load() {
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    setOpen(true); setBusy(true); setError(""); setAdvice(null);
    try { const { data } = await api.get(`/profiles/me/coach/jobs/${jobId}/advice`, { signal: controller.signal }); if (!controller.signal.aborted) setAdvice(data); }
    catch (failure) { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <>
    <button type="button" className="job-advice-launch" aria-haspopup="dialog" onClick={load}><span><Sparkles size={23} /></span><span><strong>Destaca tu hoja de vida</strong><small>Consejos para esta vacante</small></span><ArrowUpRight size={18} /></button>
    <CoachDialog open={open} onClose={() => setOpen(false)} title="Consejos para esta vacante" className="job-advice-dialog"><div className="job-advice-body">
      {busy && <p role="status" className="flex items-center gap-2"><RefreshCw size={18} className="animate-spin" />Revisando tu perfil…</p>}
      {error && <p role="alert">{error} <button type="button" className="button-secondary" onClick={load}>Reintentar</button></p>}
      {advice && Number(advice.job_id) === Number(jobId) && <><p className="section-kicker">PARA ESTA OPORTUNIDAD</p><h3>{advice.job_title}</h3><div className="job-advice-items">{advice.items.map((item, index) => <article key={item.key}><span>{index + 1}</span><div><h4>{item.title}</h4><p>{item.detail}</p><Link to={item.href}>{item.action}<ArrowRight size={15} /></Link></div></article>)}</div><p className="job-advice-note">Tú decides qué editar. Añade únicamente información que puedas respaldar con tu experiencia.</p></>}
    </div></CoachDialog>
  </>;
}
