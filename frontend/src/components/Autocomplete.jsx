import "../styles/city-autocomplete.css";
import { useId, useState } from "react";
import { MapPin, Search, X, Check } from "lucide-react";
import { citySuggestions } from "../utils/citySuggestions.js";

export function Autocomplete({ label, options, value, onChange, onSelect, ...props }) {
  const id = useId(), [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const matches = citySuggestions(options, value);
  const select = (item) => { onChange(item); onSelect?.(item); setOpen(false); setActive(-1); };
  return <div className="city-combobox"><label htmlFor={id}>{label}</label><div className="city-combobox-input"><MapPin size={16} aria-hidden="true" />
    <input {...props} id={id} className="field-control" value={value} role="combobox" autoComplete="off" aria-autocomplete="list" aria-expanded={open} aria-controls={`${id}-list`} aria-activedescendant={open && active >= 0 ? `${id}-${active}` : undefined}
      onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
      onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); setOpen(false); setActive(-1); } if (matches.length && (event.key === "ArrowDown" || event.key === "ArrowUp")) { event.preventDefault(); setOpen(true); setActive((old) => old < 0 ? event.key === "ArrowDown" ? 0 : matches.length - 1 : (old + (event.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length); } if (event.key === "Enter" && open) { event.preventDefault(); if (matches.length && (active >= 0 || value.trim())) select(matches[Math.max(0, active)] || matches[0]); } }} />{value ? <button type="button" disabled={props.disabled} aria-label="Limpiar ciudad" onClick={() => select("")}><X size={15} /></button> : <Search size={15} aria-hidden="true" />}</div>
    {open && <div className="city-combobox-menu"><p>{value ? "Ciudades coincidentes" : "Ciudades frecuentes"}</p><ul id={`${id}-list`} role="listbox">{matches.map((item, index) => <li key={item} id={`${id}-${index}`} role="option" aria-selected={active === index} onPointerDown={(event) => { event.preventDefault(); select(item); }} className={active === index ? "selected" : ""}><MapPin size={14} /><span>{item}</span>{value === item && <Check size={14} />}</li>)}</ul>{!matches.length && <small>No encontramos coincidencias. Busca y elige una ciudad del catálogo.</small>}<small>Escribe para filtrar · ↑ ↓ para elegir · Enter para confirmar</small></div>}
  </div>;
}
