import { useEffect, useId, useState } from "react";
import { Check, ChevronDown, Languages, Plus, Trash2 } from "lucide-react";
import { LANGUAGE_NAMES, LANGUAGE_LEVELS, languageLevelLabel } from "../constants/languages.js";

export function LanguagesEditor({ value = [], onChange, editing = true, required = false }) {
  const change = (index, field, next) => onChange(value.map((item, i) => i === index ? { ...item, [field]: next } : item));
  return (
    <div className="space-y-3">
      <p className="text-xs leading-5 text-[var(--muted)]">{editing ? (required ? "Añade solo los idiomas necesarios para el cargo y el nivel mínimo solicitado." : "Registra tu nivel real. Se comparará con el nivel mínimo que solicite cada empresa.") : (required ? "Idiomas y niveles mínimos solicitados para el cargo." : "Idiomas y niveles registrados en el perfil.")}</p>
      {value.map((item, index) => editing ? (
        <div key={index} className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-3 sm:p-4">
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="inline-flex items-center gap-2 text-xs font-bold"><Languages size={16} className="text-[var(--accent)]" />Idioma {index + 1}</span>
            <button type="button" className="button-secondary button-sm !px-2" aria-label={`Eliminar idioma ${index + 1}`} onClick={() => onChange(value.filter((_, i) => i !== index))}><Trash2 size={15} /><span className="hidden sm:inline">Eliminar</span></button>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <LanguagePicker label={`Idioma ${index + 1}`} displayLabel="Idioma" value={item.name} onChange={(next) => change(index, "name", next)} options={LANGUAGE_NAMES.map((name) => ({ value: name, label: name }))} searchable />
            <LanguagePicker label={`Nivel del idioma ${index + 1}`} displayLabel={required ? "Nivel mínimo solicitado" : "Mi nivel de dominio"} value={item.level} onChange={(next) => change(index, "level", next)} options={Object.entries(LANGUAGE_LEVELS).map(([key, label]) => ({ value: key, label }))} />
          </div>
        </div>
      ) : <p key={index} className="rounded-lg border border-[var(--line)] px-3 py-2 text-sm"><span className="font-semibold capitalize">{item.name}</span> · {languageLevelLabel(item.level)}</p>)}
      {!value.length && <p className="text-sm text-[var(--muted)]">{required ? "Sin requisitos de idioma registrados." : "No has registrado idiomas."}</p>}
      {editing && <button className="button-secondary button-sm" type="button" onClick={() => onChange([...value, { name: "", level: "B1" }])} disabled={value.length >= 20}><Plus size={15} />Añadir idioma</button>}
    </div>
  );
}

function LanguagePicker({ label, displayLabel, value, onChange, options, searchable = false }) {
  const id = useId();
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const normalize = (text) => text.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const filtered = options.filter((item) => !searchable || normalize(item.label).includes(normalize(query)));
  useEffect(() => {
    if (open) document.getElementById(`${id}-option-${active}`)?.scrollIntoView({ block: "nearest" });
  }, [active, id, open]);
  const select = (next) => { onChange(next); setOpen(false); setQuery(""); };
  const keyboard = (event) => {
    if (event.key === "Escape") { event.preventDefault(); setOpen(false); setQuery(""); }
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      setOpen(true);
      setActive((previous) => !open ? (event.key === "ArrowDown" ? 0 : filtered.length - 1) : Math.max(0, Math.min(filtered.length - 1, previous + (event.key === "ArrowDown" ? 1 : -1))));
    }
    if (event.key === "Enter") {
      event.preventDefault();
      if (open && filtered[active]) select(filtered[active].value);
      else if (open && searchable && query.trim()) select(query.trim());
      else setOpen(true);
    }
  };
  const accessibility = { role: "combobox", "aria-expanded": open, "aria-controls": `${id}-list`, "aria-activedescendant": open && filtered[active] ? `${id}-option-${active}` : undefined, "aria-label": label };
  return (
    <div className="relative min-w-0" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) { setOpen(false); setQuery(""); } }}>
      <label htmlFor={id} className="mb-1.5 block text-xs font-semibold text-[var(--muted)]">{displayLabel}</label>
      <div className="relative">
        {searchable ? <input id={id} {...accessibility} aria-autocomplete="list" className="field-control !pr-10" value={open ? query : value} placeholder={open ? "Busca o escribe otro idioma" : "Seleccionar idioma"} maxLength={60} autoComplete="off" onFocus={() => { setOpen(true); setQuery(""); setActive(0); }} onChange={(event) => { setQuery(event.target.value); onChange(event.target.value); setActive(0); setOpen(true); }} onKeyDown={keyboard} /> : <button id={id} type="button" {...accessibility} className="field-control flex items-center justify-between gap-2 text-left" onClick={() => { setOpen(!open); setActive(Math.max(0, options.findIndex((item) => item.value === value))); }} onKeyDown={keyboard}>{options.find((item) => item.value === value)?.label || "Seleccionar nivel"}<ChevronDown size={16} className="shrink-0 text-[var(--muted)]" /></button>}
        {searchable && <ChevronDown size={16} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" />}
      </div>
      {open && <div className="absolute z-50 mt-2 w-full rounded-xl border border-[var(--line)] bg-[var(--surface)] p-1.5 shadow-xl">
        <div id={`${id}-list`} role="listbox" aria-label={displayLabel} className="max-h-52 overflow-y-auto overscroll-contain">
          {filtered.map((item, index) => <button key={item.value} id={`${id}-option-${index}`} role="option" aria-selected={value === item.value} tabIndex={-1} type="button" className={`flex w-full items-center justify-between gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-[var(--ink-strong)] ${searchable ? "capitalize" : ""} ${active === index ? "bg-[var(--surface-hover)]" : ""} hover:bg-[var(--surface-hover)]`} onMouseDown={(event) => event.preventDefault()} onMouseEnter={() => setActive(index)} onClick={() => select(item.value)}>{item.label}{value === item.value && <Check size={16} className="shrink-0 text-[var(--accent)]" />}</button>)}
          {!filtered.length && <p className="px-3 py-2 text-xs leading-5 text-[var(--muted)]">Se guardará «{query.trim()}» como otro idioma. Elige su nivel de dominio.</p>}
        </div>
      </div>}
    </div>
  );
}
