import { useEffect, useState } from "react";
import { ExternalLink, MapPin } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function OfficialOpportunitySources() {
  const [data, setData] = useState(null), [city, setCity] = useState(""), [error, setError] = useState("");
  useEffect(() => { const controller = new AbortController(); api.get("/learning/opportunity-sources", { signal: controller.signal }).then(({ data }) => setData(data)).catch((failure) => { if (!controller.signal.aborted) setError(getApiErrorMessage(failure)); }); return () => controller.abort(); }, []);
  const rows = data?.sources.filter((row) => !city || row.city === city || row.scope === "national") || [];
  return <section className="official-opportunities"><header><span><MapPin size={22} /></span><div><h2>Oportunidades en otras ciudades</h2><p>Becas, apoyos y formación desde fuentes oficiales.</p></div></header>{error && <p role="alert">{error}</p>}{data && <><div className="official-opportunity-filter"><label>Ciudad de interés<select className="field-control" value={city} onChange={(event) => setCity(event.target.value)}><option value="">Todas las ciudades</option>{data.sources.filter((row) => row.scope === "local").map((row) => <option key={row.id}>{row.city}</option>)}</select></label><p>Las fuentes de alcance nacional también aparecen al elegir una ciudad.</p></div><div className="official-opportunity-grid">{rows.map((row) => <article key={row.id}><small>{row.scope === "national" ? "Alcance nacional" : row.city}</small><h3>{row.name}</h3><p>{row.description}</p><a className="button-secondary button-sm" href={row.url} target="_blank" rel="noopener noreferrer">Consultar fuente oficial<ExternalLink size={14} /></a></article>)}</div><p className="official-opportunity-notice">{data.notice} · Directorio revisado: {data.reviewed_on}.</p></>}</section>;
}
