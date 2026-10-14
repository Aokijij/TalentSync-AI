import { useState } from "react";
import { Link } from "react-router-dom";
import { Lightbulb, ArrowRight } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function VacancyCvAdvice({ jobId }) {
  const [advice, setAdvice] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState("");
  async function load() {
    setBusy(true); setError("");
    try { setAdvice((await api.get(`/profiles/me/coach/jobs/${jobId}/advice`)).data); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="surface-card p-5">
    <div className="flex flex-wrap items-center justify-between gap-4"><div><h2 className="flex items-center gap-2 font-semibold"><Lightbulb size={19} className="text-[var(--accent)]" />Consejos para tu hoja de vida</h2><p className="mt-1 text-sm text-[var(--muted)]">Qué destacar o aclarar para esta vacante.</p></div><button type="button" className="button-secondary" disabled={busy} onClick={load}>{busy ? "Consultando…" : advice ? "Actualizar consejos" : "Ver recomendaciones"}</button></div>
    {error && <p role="alert" className="mt-3 text-sm text-[var(--error)]">{error}</p>}
    {advice && <div className="mt-5 grid gap-4 md:grid-cols-2">{advice.items.map((item) => <article key={item.key} className="rounded-xl border border-[var(--line)] p-4"><h3 className="font-semibold">{item.title}</h3><p className="my-3 text-sm leading-6 text-[var(--muted)]">{item.detail}</p><Link className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)]" to={item.href}>{item.action}<ArrowRight size={14} /></Link></article>)}<p className="text-xs text-[var(--muted)] md:col-span-2">Los consejos usan tu perfil guardado. Tú decides qué editar; añade únicamente información que puedas respaldar.</p></div>}
  </section>;
}
