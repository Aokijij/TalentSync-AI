import { useEffect, useId, useState } from "react";
import { Check, ChevronDown, Plus, Search, X } from "lucide-react";
import { textItems, textItemKey } from "../utils/textItems.js";
import "../styles/offer-editing.css";
import "../styles/text-suggestions.css";

export function TextItemsEditor({ label, value, onChange, placeholder, help, maxItems = 20, maxLength = 100, suggestions = [], suggested = suggestions.length > 0 }) {
  const id = useId(), [input, setInput] = useState(""), [error, setError] = useState(""), [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const items = textItems(value);
  const options = [...new Map(suggestions.map(item => typeof item === "string" ? { value: item, label: item, searchTerms: [] } : item).map(item => [textItemKey(item.value), item])).values()];
  const matches = options.filter(item => !items.some(selected => textItemKey(selected) === textItemKey(item.value)) && [item.label, ...(item.searchTerms || [])].some(term => textItemKey(term).includes(textItemKey(input)))).slice(0, 10);
  const expanded = suggested && open && (options.length > 0 || !!input.trim());
  useEffect(() => { if (expanded && active >= 0) document.getElementById(`${id}-option-${active}`)?.scrollIntoView({ block: "nearest" }); }, [active, expanded, id]);
  function add(raw = input) {
    const exact = options.find(item => [item.label, ...(item.searchTerms || [])].some(term => textItemKey(term) === textItemKey(raw)));
    const next = (exact?.value || raw).trim();
    if (!next) return;
    if (items.some(item => textItemKey(item) === textItemKey(next))) { setError("Este elemento ya está añadido."); return; }
    if (items.length >= maxItems) { setError(`Puedes añadir hasta ${maxItems} elementos.`); return; }
    onChange([...items, next]); setInput(""); setError(""); setOpen(false); setActive(-1);
  }
  function keyboard(event) {
    if (event.nativeEvent.isComposing) return;
    if (suggested && ["ArrowDown", "ArrowUp"].includes(event.key)) {
      event.preventDefault(); setOpen(true);
      setActive(previous => event.key === "ArrowDown" ? Math.min(previous + 1, matches.length - 1) : Math.max(previous - 1, 0));
    } else if (event.key === "Escape" && expanded) { event.preventDefault(); event.stopPropagation(); setOpen(false); setActive(-1); }
    else if (event.key === "Enter") { event.preventDefault(); add(expanded && matches[active] ? matches[active].value : input); }
  }
  return <div className="text-items-editor" onBlur={event => { if (!event.currentTarget.contains(event.relatedTarget)) { add(); setOpen(false); } }}>
    <label htmlFor={id}>{label}</label>
    <div className="text-items-entry"><div className={`text-items-input ${suggested ? "has-suggestions" : ""}`}>
      {suggested && <Search size={17} aria-hidden="true" />}
      <input id={id} role={suggested ? "combobox" : undefined} aria-autocomplete={suggested ? "list" : undefined} aria-expanded={suggested ? expanded : undefined} aria-controls={suggested ? `${id}-suggestions` : undefined} aria-activedescendant={expanded && matches[active] ? `${id}-option-${active}` : undefined} autoComplete="off" className="field-control" value={input} maxLength={maxLength} disabled={items.length >= maxItems} placeholder={placeholder} aria-describedby={`${id}-help`} aria-invalid={!!error} onFocus={() => setOpen(true)} onChange={event => { setInput(event.target.value); setError(""); setOpen(true); setActive(-1); }} onKeyDown={keyboard} />
      {suggested && <button type="button" className="text-items-toggle" aria-label={`Mostrar sugerencias de ${label.toLowerCase()}`} disabled={items.length >= maxItems} aria-expanded={expanded} onMouseDown={event => event.preventDefault()} onClick={() => { if (open) setOpen(false); else { document.getElementById(id)?.focus(); setOpen(true); } }}><ChevronDown size={16} /></button>}
    </div><button type="button" className="button-secondary text-items-add" aria-label={`Añadir a ${label.toLowerCase()}`} disabled={!input.trim() || items.length >= maxItems} onClick={() => add()}><Plus size={16} />Añadir</button></div>
    {expanded && <div className="text-suggestions-panel"><div className="text-suggestions-heading"><span>Sugerencias del catálogo</span><span>{matches.length} {matches.length === 1 ? "opción" : "opciones"}</span></div><div role="listbox" id={`${id}-suggestions`} aria-label={`Sugerencias de ${label.toLowerCase()}`}>
      {matches.map((item, index) => <button type="button" role="option" aria-selected={active === index} id={`${id}-option-${index}`} tabIndex={-1} key={item.value} onMouseDown={event => event.preventDefault()} onMouseEnter={() => setActive(index)} onClick={() => add(item.value)}><span>{item.label}</span>{active === index ? <Check size={16} /> : <Plus size={15} />}</button>)}
      {!matches.length && <p>No hay coincidencias. Puedes añadir el nombre que escribiste.</p>}
    </div><small>Selecciona una opción o escribe otro nombre y pulsa Añadir.</small></div>}
    <small id={`${id}-help`}>{help || "Escribe un elemento y pulsa Añadir o Enter."}</small>
    {error && <p role="status" className="text-items-error">{error}</p>}
    <ul aria-label={`${label}: elementos añadidos`}>{items.map((item, index) => <li key={textItemKey(item)}><span>{item}</span><button type="button" aria-label={`Quitar ${item}`} onClick={() => { onChange(items.filter((_, position) => position !== index)); setError(""); }}><X size={13} /></button></li>)}</ul>
    {!!items.length && <small>{items.length}/{maxItems} añadidos</small>}
  </div>;
}
