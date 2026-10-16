import { useId, useState } from "react";
import { Plus, X } from "lucide-react";
import { textItems, textItemKey } from "../utils/textItems.js";
import "../styles/offer-editing.css";

export function TextItemsEditor({ label, value, onChange, placeholder, help, maxItems = 20, maxLength = 100 }) {
  const id = useId(), [input, setInput] = useState(""), [error, setError] = useState("");
  const items = textItems(value);
  function add() {
    const next = input.trim();
    if (!next) return;
    if (items.some((item) => textItemKey(item) === textItemKey(next))) { setError("Este elemento ya está añadido."); return; }
    if (items.length >= maxItems) { setError(`Puedes añadir hasta ${maxItems} elementos.`); return; }
    onChange([...items, next]); setInput(""); setError("");
  }
  return <div className="text-items-editor" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) add(); }}><label htmlFor={id}>{label}</label><div className="text-items-entry"><input id={id} className="field-control" value={input} maxLength={maxLength} disabled={items.length >= maxItems} placeholder={placeholder} aria-describedby={`${id}-help`} aria-invalid={!!error} onChange={(event) => { setInput(event.target.value); setError(""); }} onKeyDown={(event) => { if (event.key === "Enter" && !event.nativeEvent.isComposing) { event.preventDefault(); add(); } }} /><button type="button" className="button-secondary" aria-label={`Añadir a ${label.toLowerCase()}`} disabled={!input.trim() || items.length >= maxItems} onClick={add}><Plus size={16} />Añadir</button></div><small id={`${id}-help`}>{help || "Escribe un elemento y pulsa Añadir o Enter."}</small>{error && <p role="status" className="text-items-error">{error}</p>}<ul aria-label={`${label}: elementos añadidos`}>{items.map((item, index) => <li key={textItemKey(item)}><span>{item}</span><button type="button" aria-label={`Quitar ${item}`} onClick={() => { onChange(items.filter((_, position) => position !== index)); setError(""); }}><X size={13} /></button></li>)}</ul>{!!items.length && <small>{items.length}/{maxItems} añadidos</small>}</div>;
}
