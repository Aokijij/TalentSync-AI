import { useId, useState } from "react";
import { MapPin, Search, X, Check } from "lucide-react";
const fold = (text) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function Autocomplete({ label, options, value, onChange, onSelect, ...props }) {
  const id = useId(), [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const matches = value.trim() ? options.filter((item) => fold(item).includes(fold(value))).slice(0, 8) : options.slice(0, 7);
  const select = (item) => { onChange(item); onSelect?.(item); setOpen(false); setActive(-1); };
  return <div className="city-combobox"><label htmlFor={id}>{label}</label><div className="city-combobox-input"><MapPin size={16} aria-hidden="true" />
    <input {...props} id={id} className="field-control" value={value} role="combobox" autoComplete="off" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
      onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
      onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); setOpen(false); setActive(-1); } if (matches.length && (event.key === "ArrowDown" || event.key === "ArrowUp")) { event.preventDefault(); setOpen(true); setActive((old) => old < 0 ? event.key === "ArrowDown" ? 0 : matches.length - 1 : (old + (event.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length); } if (event.key === "Enter" && open && active >= 0 && matches[active]) { event.preventDefault(); select(matches[active]); } }} />{value ? <button type="button" aria-label="Quitar filtro de ciudad" onClick={() => select("")}><X size={15} /></button> : <Search size={15} aria-hidden="true" />}</div>
    {open && <div className="city-combobox-menu"><p>{value ? "Ciudades coincidentes" : "Ciudades frecuentes"}</p><ul id={`${id}-list`} role="listbox">{matches.map((item, index) => <li key={item} id={`${id}-${index}`} role="option" aria-selected={active === index} onMouseDown={(event) => { event.preventDefault(); select(item); }} className={active === index ? "selected" : ""}><MapPin size={14} /><span>{item}</span>{value === item && <Check size={14} />}</li>)}</ul>{!matches.length && <small>No encontramos coincidencias. Puedes escribir otra ubicación.</small>}<small>Escribe para filtrar · ↑ ↓ para elegir</small></div>}
  </div>;
}
