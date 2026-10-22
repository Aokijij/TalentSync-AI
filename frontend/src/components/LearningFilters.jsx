import "../styles/learning-filters.css";
import { ChevronDown, RotateCcw, Search, SlidersHorizontal, X } from "lucide-react";
import { certificateCosts, courseModalities, enrollmentStatuses, learningLanguages, learningLevels } from "../utils/learningPresentation.js";

export function LearningFilters({ value, onChange, resources = [], resultCount }) {
  const change = (key, next) => onChange({ ...value, [key]: next });
  const providers = [...new Set(resources.map((row) => row.provider).filter(Boolean))].sort((a, b) => a.localeCompare(b, "es"));
  const languages = [...new Set(resources.flatMap((row) => row.details?.languages || []))].sort();
  const options = [
    ["provider", "Proveedor", [["all", "Todos los proveedores"], ...providers.map((name) => [name, name])]],
    ["cost", "Acceso al curso", [["all", "Cualquier coste"], ["free", "Gratuito"], ["paid", "De pago"], ["unknown", "Por confirmar"]]],
    ["level", "Nivel", [["all", "Todos los niveles"], ...Object.entries(learningLevels)]],
    ["language", "Idioma", [["all", "Cualquier idioma"], ...languages.map((code) => [code, learningLanguages([code])])]],
    ["origin", "Origen", [["all", "Todos los orígenes"], ["local", "TalentSync"], ["external", "Proveedores externos"]]],
    ["kind", "Formato", [["all", "Todos los formatos"], ["project", "Laboratorio / práctica"], ["course", "Curso o ruta"], ["workshop", "Taller"], ["documentation", "Documentación"]]],
    ["enrollment", "Inscripciones", [["all", "Cualquier disponibilidad"], ...Object.entries(enrollmentStatuses)]],
    ["modality", "Modalidad", [["all", "Cualquier modalidad"], ...Object.entries(courseModalities)]],
    ["certificate", "Certificado", [["all", "Cualquier certificado"], ...Object.entries(certificateCosts)]],
  ];
  const active = options.filter(([key]) => value[key] && value[key] !== "all").map(([key, title, items]) => ({ key, label: `${title}: ${items.find(([id]) => id === value[key])?.[1] || value[key]}` }));
  if (value.query?.trim()) active.unshift({ key: "query", label: `Búsqueda: ${value.query.trim()}` });
  const extraCount = active.filter(({ key }) => !["query", "provider", "cost"].includes(key)).length;
  const render = ([key, title, items]) => <label key={key} className="course-filter-field"><span>{title}</span><select className="field-control" value={value[key] || "all"} onChange={(event) => change(key, event.target.value)}>{items.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select></label>;
  const remove = (key) => { const next = { ...value }; delete next[key]; onChange(next); };
  return <section className="course-filter-panel" aria-label="Filtros de formación">
    <header className="course-filter-heading"><span className="course-filter-icon"><SlidersHorizontal size={19} /></span><h3>Filtros de formación</h3>{resultCount !== undefined && <span className="course-filter-results" role="status" aria-live="polite"><strong>{resultCount}</strong>{resultCount === 1 ? "recurso" : "recursos"}</span>}{active.length > 0 && <button type="button" className="course-filter-reset" onClick={() => onChange({})}><RotateCcw size={14} />Limpiar filtros<span>{active.length}</span></button>}</header>
    <div className="course-filter-main"><label className="course-filter-field course-filter-search"><span>Qué quieres aprender</span><div><Search size={18} aria-hidden="true" /><input type="search" className="field-control" value={value.query || ""} placeholder="Ej. Excel, análisis de datos o atención al cliente" onChange={(event) => change("query", event.target.value)} />{value.query && <button type="button" aria-label="Borrar búsqueda" onClick={() => remove("query")}><X size={15} /></button>}</div></label>{render(options[0])}<div className="course-filter-cost" role="group" aria-label="Acceso al curso"><span>Acceso al curso</span><div>{[["all", "Todos"], ["free", "Gratuitos"], ["paid", "De pago"], ["unknown", "Por confirmar"]].map(([key, label]) => <button type="button" key={key} aria-pressed={(value.cost || "all") === key} onClick={() => change("cost", key)}>{label}</button>)}</div></div></div>
    {active.length > 0 && <div className="course-filter-tags" role="group" aria-label="Filtros activos">{active.map(({ key, label }) => <button type="button" key={key} title={label} aria-label={`Quitar filtro ${label}`} onClick={() => remove(key)}><span>{label}</span><X size={13} /></button>)}</div>}
    <details className="course-filter-advanced"><summary><SlidersHorizontal size={15} /><span>Más filtros<small>Nivel, idioma, formato y condiciones</small></span>{extraCount > 0 && <em>{extraCount} activos</em>}<ChevronDown className="course-filter-chevron" size={17} /></summary><div className="course-filter-groups"><fieldset><legend>Cómo quieres aprender</legend><div>{options.filter(([key]) => ["level", "language", "kind", "modality"].includes(key)).map(render)}</div></fieldset><fieldset><legend>Disponibilidad y certificado</legend><div>{options.filter(([key]) => ["origin", "enrollment", "certificate"].includes(key)).map(render)}</div></fieldset></div></details>
  </section>;
}
