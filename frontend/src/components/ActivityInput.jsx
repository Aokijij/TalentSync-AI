import { ArrowDown, ArrowUp, Check } from "lucide-react";

export function activityComplete(item, value) {
  if (item.type === "number") return value !== undefined && value !== "";
  if (["order", "matching"].includes(item.type)) return Array.isArray(value) && value.length === (item.terms?.length || item.choices.length) && value.every((index) => index >= 0);
  if (item.type === "multi_select") return Array.isArray(value) && value.length > 0;
  return Number.isInteger(value);
}
export function describeAnswer(item, value) {
  if (value === undefined || value === "") return "Sin responder";
  if (Array.isArray(value)) return value.map((index, position) => `${item.terms?.[position] ? item.terms[position] + ": " : ""}${item.choices[index] || "Sin relacionar"}`).join(" → ");
  return item.type === "number" ? String(value) : item.choices[value] || "Sin responder";
}
export function ActivityInput({ item, value, onChange, disabled = false }) {
  if (item.type === "number") return <label className="block max-w-sm text-sm font-semibold">Tu cálculo<input className="field-control mt-2 text-lg" aria-label="Resultado del cálculo" inputMode="decimal" type="number" step="any" disabled={disabled} value={value ?? ""} onChange={(event) => onChange(event.target.value)} /><span className="mt-2 block font-normal text-[var(--muted)]">Escribe la cantidad sin separadores de miles.</span></label>;
  if (item.type === "matching") return <div className="space-y-3">{item.terms.map((term, index) => <label className="activity-match" key={term}><strong>{term}</strong><select className="field-control" value={value?.[index] ?? -1} disabled={disabled} onChange={(event) => { const next = value ? [...value] : item.terms.map(() => -1); next[index] = Number(event.target.value); onChange(next); }}><option value={-1}>Relaciona con…</option>{item.choices.map((choice, position) => <option value={position} key={choice}>{choice}</option>)}</select></label>)}</div>;
  if (item.type === "order") {
    const order = value || item.choices.map((_, index) => index);
    const move = (index, direction) => { const next = [...order]; [next[index], next[index + direction]] = [next[index + direction], next[index]]; onChange(next); };
    return <div className="space-y-3"><p className="text-sm text-[var(--muted)]">Usa las flechas para decidir qué ocurre primero. Confirma tu orden cuando esté listo.</p><ol className="space-y-2">{order.map((position, index) => <li className="activity-order" key={position}><span className="activity-number">{index + 1}</span><p className="flex-1 text-sm">{item.choices[position]}</p><button className="button-secondary !p-2" aria-label={`Subir ${item.choices[position]}`} disabled={disabled || index === 0} onClick={() => move(index, -1)}><ArrowUp size={16} /></button><button className="button-secondary !p-2" aria-label={`Bajar ${item.choices[position]}`} disabled={disabled || index === order.length - 1} onClick={() => move(index, 1)}><ArrowDown size={16} /></button></li>)}</ol><button className="button-secondary" disabled={disabled} onClick={() => onChange([...order])}><Check size={16} />{value ? "Orden seleccionado" : "Confirmar este orden"}</button></div>;
  }
  return <fieldset className="space-y-3"><legend className="sr-only">{item.prompt}</legend>{item.choices.map((choice, index) => {
    const multiple = item.type === "multi_select", checked = multiple ? (value || []).includes(index) : value === index;
    return <label className={`activity-choice ${checked ? "selected" : ""}`} key={choice}><input type={multiple ? "checkbox" : "radio"} name={item.id} checked={checked} disabled={disabled} onChange={() => onChange(multiple ? checked ? value.filter((key) => key !== index) : [...(value || []), index] : index)} /><span>{choice}</span></label>;
  })}</fieldset>;
}
