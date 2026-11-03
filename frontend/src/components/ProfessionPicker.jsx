import { useId, useState } from "react";
import { BriefcaseBusiness, Check, ChevronDown, Search } from "lucide-react";
import { OCCUPATIONS } from "../constants/occupations.js";
import "../styles/profession-picker.css";

const key = (value) => value.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es").replace(/[-–_]/g, "");
export function ProfessionPicker({ value = "", onChange, onBlur, label = "Profesión o cargo de interés", required = false, error, id: suppliedId }) {
  const generated = useId(), id = suppliedId || generated;
  const [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const terms = key(value).split(/\s+/).filter(Boolean);
  const matches = OCCUPATIONS.filter((item) => terms.every((term) => key(item).includes(term))).slice(0, 9);
  const exact = OCCUPATIONS.some((item) => key(item) === key(value.trim()));
  const choose = (item) => { onChange(item); setOpen(false); setActive(-1); };
  return <div className="profession-picker"><label htmlFor={id}>{label}{required && <span aria-hidden="true"> *</span>}</label>
    <div className="profession-picker-control"><BriefcaseBusiness size={18} aria-hidden="true" /><input id={id} value={value} required={required} maxLength={160} autoComplete="off" role="combobox" aria-expanded={open} aria-controls={`${id}-options`} aria-autocomplete="list" aria-activedescendant={open && active >= 0 ? `${id}-option-${active}` : undefined} aria-describedby={`${id}-help`} aria-invalid={!!error} placeholder="Busca tu profesión o escribe el cargo que te interesa" onFocus={() => setOpen(true)} onClick={() => setOpen(true)} onBlur={() => { setOpen(false); onBlur?.(); }} onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }} onKeyDown={(event) => {
      if (event.key === "Escape") { setOpen(false); setActive(-1); }
      if (["ArrowDown", "ArrowUp"].includes(event.key) && matches.length) { event.preventDefault(); setOpen(true); setActive((old) => old < 0 ? 0 : (old + (event.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length); }
      if (event.key === "Enter" && open) { event.preventDefault(); choose(active >= 0 ? matches[active] : value.trim()); }
    }} /><button type="button" className="profession-picker-toggle" aria-label="Mostrar sugerencias de profesión" aria-expanded={open} aria-controls={`${id}-options`} onPointerDown={(event) => event.preventDefault()} onClick={() => setOpen((old) => !old)}><ChevronDown size={16} aria-hidden="true" /></button>
    {open && <div className="profession-picker-menu"><p><Search size={14} />{value ? "Cargos relacionados" : "Explora profesiones de todos los sectores"}</p><ul id={`${id}-options`} role="listbox">{matches.map((item, index) => <li key={item} id={`${id}-option-${index}`} role="option" aria-selected={active === index || value === item} onPointerDown={(event) => { event.preventDefault(); choose(item); }} className={active === index ? "is-active" : ""}><BriefcaseBusiness size={16} /><span>{item}</span>{value === item && <Check size={16} />}</li>)}</ul>{value.trim() && !exact && <button type="button" onPointerDown={(event) => event.preventDefault()} onClick={() => choose(value.trim())}>Usar «{value.trim()}»<Check size={15} /></button>}<small>↑ ↓ para recorrer · Enter para elegir · También puedes escribir tu propio cargo.</small></div>}
    </div><small id={`${id}-help`}>{error || "Elige una sugerencia o conserva tu propio texto. No necesitas tener un título universitario."}</small>
  </div>;
}
