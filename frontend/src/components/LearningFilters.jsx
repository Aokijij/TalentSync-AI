export function LearningFilters({ value, onChange }) {
  const change = (key, next) => onChange({ ...value, [key]: next });
  return <div className="surface-card grid gap-3 p-4 sm:grid-cols-2 xl:grid-cols-4"><label className="text-sm">Buscar formación<input className="field-control mt-1" value={value.query || ""} placeholder="Título, habilidad o proveedor" onChange={(event) => change("query", event.target.value)} /></label>
    {[["origin", "Origen", [["all", "Todos los orígenes"], ["local", "TalentSync"], ["external", "Proveedores externos"]]], ["cost", "Coste", [["all", "Cualquier coste"], ["free", "Gratuito"], ["paid", "De pago"], ["unknown", "Por confirmar"]]], ["kind", "Formato", [["all", "Todos los formatos"], ["project", "Laboratorio / práctica"], ["course", "Curso"], ["workshop", "Taller"], ["documentation", "Documentación"]]]].map(([key, title, options]) => <label key={key} className="text-sm">{title}<select className="field-control mt-1" value={value[key] || "all"} onChange={(event) => change(key, event.target.value)}>{options.map(([id, label]) => <option value={id} key={id}>{label}</option>)}</select></label>)}
  </div>;
}
