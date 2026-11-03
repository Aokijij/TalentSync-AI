import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, RefreshCw, Search, ShieldCheck } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import "../styles/external-catalog.css";

export function ExternalCatalogPanel({ onChanged }) {
  const [status, setStatus] = useState(null), [error, setError] = useState(""), [busy, setBusy] = useState(false);
  const [keywords, setKeywords] = useState("servicio al cliente, administración, ventas, tecnología");
  const load = useCallback(async () => {
    try { setStatus((await api.get("/admin/jobs/catalog-status")).data); setError(""); }
    catch (failure) { setError(getApiErrorMessage(failure)); }
  }, []);
  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (status?.run?.state !== "running") return;
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load, status?.run?.state]);
  async function synchronize(event) {
    event.preventDefault(); setBusy(true); setError("");
    try {
      await api.post("/admin/jobs/catalog-refresh", { keywords, location: "Colombia" }, { __quiet: true });
      setStatus((previous) => ({ ...previous, run: { state: "running", source: "Preparando fuentes" } }));
      await onChanged?.();
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  const running = status?.run?.state === "running";
  return <section className="external-catalog-panel"><header><span className="external-catalog-symbol"><ShieldCheck size={25} /></span><div><p className="section-kicker">CATÁLOGO EXTERNO · COLOMBIA</p><h2>Más oportunidades, con información útil</h2><p>Las fuentes se sincronizan y las ofertas se comprueban automáticamente. Los registros guardados y las vacantes disponibles se muestran por separado.</p></div><span className="external-catalog-badge">Meta: {status?.target || 100} disponibles</span></header>
    <div className="external-catalog-metrics">{[["Registros guardados", status?.total], ["Disponibles", status?.active], ["En revisión", status?.review], ["Cerradas", status?.closed]].map(([label, value]) => <div key={label}><strong>{value ?? "—"}</strong><span>{label}</span></div>)}</div>
    <form onSubmit={synchronize}><label>Áreas para la búsqueda<input className="field-control" value={keywords} onChange={(event) => setKeywords(event.target.value)} minLength={2} maxLength={240} required placeholder="Ventas, salud, logística, tecnología…" /></label><button className="button-primary" disabled={busy || running}><RefreshCw size={17} className={running ? "animate-spin" : ""} />{running ? "Sincronizando en segundo plano" : "Actualizar catálogo"}</button></form>
    {status?.run?.source && <div role="status" className="external-catalog-progress">{running ? <RefreshCw size={18} /> : <CheckCircle2 size={18} />}<div><strong>{status.run.source}</strong><p>{status.run.created || 0} nuevas · {status.run.updated || 0} actualizadas · {status.run.sources_checked || 0} consultas completadas</p></div></div>}
    {!!status?.run?.errors?.length && <details><summary>{status.run.errors.length} fuentes necesitan reintento</summary><ul>{status.run.errors.map((row, index) => <li key={index}>{row.source}: {row.message}</li>)}</ul></details>}
    {error && <p role="alert" className="text-[var(--error)]">{error}</p>}
    <footer><Search size={17} /><p>Una oferta incompleta queda en revisión. La formación y experiencia no informadas conservan ese estado; no se inventan requisitos. Las fuentes originales mantienen la postulación.</p><button type="button" className="button-secondary button-sm" onClick={load}>Actualizar estado</button></footer>
  </section>;
}
