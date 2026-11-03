import { bulletKeyDown } from "../utils/bulletEditing.js";
import { AutoResizeTextarea } from "./AutoResizeTextarea.jsx";
import { isOngoing, selectCurrentEmployment } from "../utils/profileStatus.js";
import { useState } from "react";
import { Autocomplete } from "./Autocomplete.jsx";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
import { MonthYearPicker } from "./MonthYearPicker.jsx";
import { Plus, Trash2 } from "lucide-react";
import { experiencePeriod, recentExperiences } from "../utils/experienceDates.js";

const commutingCities = Object.entries(COLOMBIA_LOCATIONS).flatMap(([department, cities]) => cities.map((city) => `${city}, ${department}`)).sort((a, b) => a.localeCompare(b, "es"));

export function ExperienceFields({ items, editing, onChange }) {
  const update = (index, patch) => onChange(items.map((item, i) => i === index ? { ...item, ...patch } : item));
  const month = new Date().toISOString().slice(0, 7);
  return <div className="space-y-4">{editing && items.filter(isOngoing).length > 1 && <p role="alert" className="rounded-lg border border-[var(--warning)] p-3 text-sm text-[var(--warning)]">Hay varios trabajos marcados como actuales. Selecciona el que corresponde y completa las fechas de los anteriores antes de guardar.</p>}{(editing ? items : recentExperiences(items)).map((item, index) => {
    const current = item.is_current === true || /^(presente|actualidad|actual)$/i.test(item.end_year || "");
    return <article className="experience-entry" key={index}>{editing ? <>
      <div className="grid gap-4 sm:grid-cols-2">{[["role", "Cargo"], ["company", "Empresa"]].map(([key, label]) => <label className="text-sm" key={key}>{label}<input className="field-control mt-1" value={item[key] || ""} maxLength={160} onChange={(event) => update(index, { [key]: event.target.value })} /></label>)}
        <MonthYearPicker label="Mes y año de inicio" max={month} value={item.start_date || ""} onChange={(value) => update(index, { start_date: value, start_year: value.slice(0, 4) })} />
        <MonthYearPicker label="Mes y año de finalización" disabled={current} min={item.start_date || "1900-01"} max={month} value={current ? "" : item.end_date || ""} onChange={(value) => update(index, { end_date: value, end_year: value.slice(0, 4) })} />
      </div><label className="mobility-choice mt-3"><input type="checkbox" checked={current} onChange={(event) => onChange(selectCurrentEmployment(items, index, event.target.checked))} /><span>Trabajo actualmente aquí</span></label>
      {item.start_year && !item.start_date && <p className="mt-2 text-xs text-[var(--muted)]">Registro anterior: {experiencePeriod(item)}. Completa los meses para precisar la duración; no se han supuesto fechas nuevas.</p>}
      <label className="mt-3 block text-sm">Responsabilidades y resultados<AutoResizeTextarea onKeyDown={(event) => bulletKeyDown(event, (description) => update(index, { description }))} id={`experience-description-${index}`} className="field-control mt-1" rows={3} maxLength={3000} value={item.description || ""} onChange={(event) => update(index, { description: event.target.value })} /></label>
      <button type="button" className="mt-3 inline-flex items-center gap-2 text-sm text-[var(--error)]" onClick={() => onChange(items.filter((_, i) => i !== index))}><Trash2 size={14} />Eliminar experiencia</button>
    </> : <><h3 className="font-bold">{item.role}</h3><p className="mt-1 text-sm font-semibold text-[var(--accent)]">{item.company}</p><p className="mt-1 text-xs text-[var(--muted)]">{experiencePeriod(item)}</p>{item.description && <p className="mt-3 whitespace-pre-line text-sm text-[var(--muted)]">{item.description}</p>}</>}</article>;
  })}{!items.length && <p className="text-sm text-[var(--muted)]">Añade tus cargos y fechas o importa tu hoja de vida.</p>}{editing && <button type="button" className="button-secondary button-sm" onClick={() => onChange([...items, { role: "", company: "", start_date: "", end_date: "", is_current: false, description: "" }])}><Plus size={16} />Añadir experiencia</button>}<p className="text-xs text-[var(--muted)]">Solo puedes marcar un empleo como actual. Al elegir otro, revisa la fecha de finalización del anterior. Se cuentan meses calendario. Los cargos simultáneos no duplican la experiencia total; las fechas que solo tienen año siguen siendo aproximadas.</p></div>;
}

export function MobilityFields({ value = {}, editing, onChange }) {
  const [cityQuery, setCityQuery] = useState("");
  const addCity = (city) => {
    if (!commutingCities.includes(city) || (value.commuting_cities || []).length >= 20) return;
    onChange({ ...value, commuting_cities: [...new Set([...(value.commuting_cities || []), city])] });
    setCityQuery("");
  };
  const choices = [["willing_to_relocate", "¿Aceptarías cambiar de ciudad?"], ["willing_to_travel", "¿Puedes realizar viajes de trabajo?"]];
  return <div className="mt-4 space-y-3 border-t border-[var(--line)] pt-4"><h3 className="text-sm font-bold">Ciudad y movilidad</h3>{choices.map(([key, label]) => <label className="block text-sm" key={key}>{label}{editing ? <select className="field-control mt-1" value={value[key] == null ? "" : String(value[key])} onChange={(event) => onChange({ ...value, [key]: event.target.value === "" ? null : event.target.value === "true" })}><option value="">Por confirmar</option><option value="true">Sí</option><option value="false">No</option></select> : <strong className="ml-2">{value[key] == null ? "Por confirmar" : value[key] ? "Sí" : "No"}</strong>}</label>)}<div className="space-y-2">{editing ? <><Autocomplete label="Otras ciudades donde puedes asistir habitualmente" options={commutingCities} value={cityQuery} onChange={setCityQuery} onSelect={addCity} placeholder="Busca y elige una ciudad" maxLength={120} /><small className="text-[var(--muted)]">Selecciona una ciudad de la lista. Puedes añadir hasta 20.</small></> : <h4 className="text-sm">Otras ciudades donde puedes asistir habitualmente</h4>}<div className="mobility-city-chips">{(value.commuting_cities || []).map((city) => <span key={city}>{city}{editing && <button type="button" aria-label={`Quitar ${city}`} onClick={() => onChange({ ...value, commuting_cities: value.commuting_cities.filter((item) => item !== city) })}><Trash2 size={13} /></button>}</span>)}{!value.commuting_cities?.length && <small className="text-[var(--muted)]">Sin ciudades adicionales</small>}</div></div><p className="text-xs text-[var(--muted)]">Poder viajar no significa aceptar desplazamientos diarios. Estos datos ayudan a revisar ofertas híbridas y presenciales.</p></div>;
}
