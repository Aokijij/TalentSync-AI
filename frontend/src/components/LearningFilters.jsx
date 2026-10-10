import { learningLanguages, learningLevels } from "../utils/learningPresentation.js";

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
  ];
  return <div className="surface-card space-y-3 p-4"><label className="block text-sm">Buscar formación<input className="field-control mt-1" value={value.query || ""} placeholder="Título, habilidad o proveedor" onChange={(event) => change("query", event.target.value)} /></label>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{options.map(([key, title, items]) => <label key={key} className="min-w-0 text-sm">{title}<select className="field-control mt-1" value={value[key] || "all"} onChange={(event) => change(key, event.target.value)}>{items.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select></label>)}</div>
    {Object.values(value).some((item) => item && item !== "all") && <button className="button-secondary button-sm" onClick={() => onChange({})}>Limpiar filtros</button>}
  </div>;
}
