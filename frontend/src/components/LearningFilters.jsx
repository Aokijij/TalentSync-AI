import { RotateCcw } from "lucide-react";
import { certificateCosts, courseModalities, enrollmentStatuses, learningLanguages, learningLevels } from "../utils/learningPresentation.js";

export function LearningFilters({ value, onChange, resources = [] }) {
  const change = (key, next) => onChange({ ...value, [key]: next });
  const providers = [...new Set(resources.map((row) => row.provider).filter(Boolean))].sort((a, b) => a.localeCompare(b, "es"));
  const languages = [...new Set(resources.flatMap((row) => row.details?.languages || []))].sort();
  const options = [
    ["provider", "Proveedor", [["all", "Todos los proveedores"], ...providers.map((name) => [name, name])]],
    ["cost", "Acceso al curso", [["all", "Cualquier coste"], ["free", "Gratuito"], ["paid", "De pago"], ["unknown", "Por confirmar"]]],
    ["level", "Nivel", [["all", "Todos los niveles"], ...Object.entries(learningLevels)]],
    ["language", "Idioma del contenido", [["all", "Cualquier idioma"], ...languages.map((code) => [code, learningLanguages([code])])]],
    ["origin", "Origen", [["all", "Todos los orígenes"], ["local", "TalentSync"], ["external", "Proveedores externos"]]],
    ["kind", "Formato", [["all", "Todos los formatos"], ["project", "Laboratorio / práctica"], ["course", "Curso o ruta"], ["workshop", "Taller"], ["documentation", "Documentación"]]],
    ["enrollment", "Inscripciones", [["all", "Cualquier disponibilidad"], ...Object.entries(enrollmentStatuses)]],
    ["modality", "Modalidad", [["all", "Cualquier modalidad"], ...Object.entries(courseModalities)]],
    ["certificate", "Certificado", [["all", "Cualquier certificado"], ...Object.entries(certificateCosts)]],
  ];
  const activeCount = Object.values(value).filter((item) => item && item !== "all").length;
  const render = ([key, title, items]) => <label key={key} className="filter-field">{title}<select className="field-control" value={value[key] || "all"} onChange={(event) => change(key, event.target.value)}>{items.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select></label>;
  return <section className="learning-filter-panel" aria-label="Filtros de formación"><div className="learning-filter-primary"><label className="filter-field">Buscar formación<input className="field-control" value={value.query || ""} placeholder="Título, habilidad o proveedor" onChange={(event) => change("query", event.target.value)} /></label>{options.slice(0, 2).map(render)}</div>
    {activeCount > 0 && <div className="filter-reset-row"><button type="button" className="filter-reset-button" onClick={() => onChange({})}><RotateCcw size={15} aria-hidden="true" />Limpiar filtros<span aria-label={`${activeCount} filtros activos`}>{activeCount}</span></button></div>}
    <details className="learning-extra-filters"><summary>Más filtros · nivel, idioma, modalidad y certificado</summary><div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{options.slice(2).map(render)}</div></details>
  </section>;
}
