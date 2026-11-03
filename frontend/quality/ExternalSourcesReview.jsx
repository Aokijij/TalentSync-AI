import { EmployerBoardImport } from "../src/components/EmployerBoardImport.jsx";
import { ExternalVacancyStatus } from "../src/components/ExternalVacancyStatus.jsx";
import { IntegrationStatus } from "../src/components/IntegrationStatus.jsx";
import { api } from "../src/api/client.js";
import { ExternalCatalogPanel } from "../src/components/ExternalCatalogPanel.jsx";
import { YouTubeLearningImport } from "../src/components/YouTubeLearningImport.jsx";
import { BrandLogo } from "../src/components/brand/BrandLogo.jsx";
import "../src/styles/learning-catalog.css";

// Isolated visual fixture: no real API, import, source query or account data.
const jobs = [{ id: "review-1", title: "Analista de datos", company: "Empresa de revisión", location: "Colombia", url: "https://example.org/review", description: "Datos sintéticos para revisar la selección." }];
if (new URLSearchParams(window.location.search).has("externalSources")) api.defaults.adapter = async (config) => {
  if (config.url.endsWith("/catalog-status")) return { data: { total: 321, active: 129, review: 190, closed: 2, target: 100, run: { state: "completed", source: "Sincronización terminada", created: 17, updated: 40, sources_checked: 8 } }, status: 200, statusText: "OK", headers: {}, config };
  if (config.url.endsWith("/catalog-refresh")) return { data: { state: "running" }, status: 200, statusText: "OK", headers: {}, config };
  if (config.url.endsWith("/sources/youtube")) return { data: { configured: true, requests_used: 2, request_limit: 100 }, status: 200, statusText: "OK", headers: {}, config };
  const response = config.url.endsWith("/preview") ? { provider: "Greenhouse", scanned: 4, items: jobs, note: "Muestra sintética. No se consulta ni importa ninguna oferta real." } : config.url.endsWith("/import") ? { created: 1, updated: 0, rejected: 0 } : config.url.endsWith("/availability/check") ? { checked: 3, verified: 1, closed: 1, unknown: 1, unavailable: 0 } : {};
  return { data: response, status: 200, statusText: "OK", headers: {}, config };
};
export function ExternalSourcesReview() {
  return <><BrandLogo /><header><p className="section-kicker">REVISIÓN VISUAL · DATOS SINTÉTICOS</p><h1 className="text-2xl font-bold">Fuentes y vigencia de las ofertas</h1></header><ExternalCatalogPanel /><YouTubeLearningImport onImported={() => {}} /><EmployerBoardImport /><ExternalVacancyStatus job={{ source_kind: "external", external_check_state: "verified", external_available: true, external_checked_at: "2026-10-29T15:00:00" }} /><IntegrationStatus rows={[
    { id: "matching", name: "Modelo de compatibilidad", operational_state: "local", implemented: true, status: "Modelo activo en la plataforma.", next_steps: "Revisar resultados con evidencias." },
    { id: "social_google", name: "Acceso social · Google", operational_state: "observed", implemented: true, configured: true, last_success_at: "2026-10-29T15:00:00Z", last_attempt_at: "2026-10-29T15:00:00Z", status: "Operación de ejemplo correcta. La aprobación pública se gestiona por separado.", next_steps: "Revisar el expediente del proveedor." },
    { id: "social_github", name: "Acceso social · GitHub", operational_state: "unverified", implemented: true, configured: true, status: "Configuración disponible; todavía no se ha completado una operación.", next_steps: "El titular puede comprobarlo cuando esté listo." },
  ]} /></>;
}
