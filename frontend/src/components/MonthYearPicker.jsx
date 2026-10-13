import { useEffect, useId, useRef, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, X } from "lucide-react";
import { monthChoice } from "../utils/monthChoice.js";

const MONTHS = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];

export function MonthYearPicker({ label, value = "", onChange, min = "1900-01", max = new Date().toISOString().slice(0, 7), disabled = false }) {
  const id = useId(), container = useRef(null), trigger = useRef(null), yearInput = useRef(null);
  const [open, setOpen] = useState(false), [year, setYear] = useState(max.slice(0, 4));
  const minimum = Number(min.slice(0, 4)), maximum = Number(max.slice(0, 4));
  const close = () => { setOpen(false); trigger.current?.focus(); };
  useEffect(() => {
    if (!open) return;
    yearInput.current?.focus();
    const outside = (event) => { if (!container.current?.contains(event.target)) setOpen(false); };
    const escape = (event) => { if (event.key === "Escape") { event.preventDefault(); setOpen(false); trigger.current?.focus(); } };
    document.addEventListener("pointerdown", outside); document.addEventListener("keydown", escape);
    return () => { document.removeEventListener("pointerdown", outside); document.removeEventListener("keydown", escape); };
  }, [open]);
  const selected = /^\d{4}-\d{2}$/.test(value) ? `${MONTHS[Number(value.slice(5)) - 1]} de ${value.slice(0, 4)}` : "Selecciona mes y año";
  const choose = (next) => { onChange(next); close(); };
  return <div className="month-field" ref={container} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}><label id={`${id}-label`} htmlFor={`${id}-trigger`}>{label}</label><button ref={trigger} id={`${id}-trigger`} type="button" className="month-trigger" disabled={disabled} aria-labelledby={`${id}-label ${id}-value`} aria-haspopup="dialog" aria-expanded={open && !disabled} aria-controls={`${id}-calendar`} onClick={() => { setYear((value || max).slice(0, 4)); setOpen(!open); }}><span id={`${id}-value`}>{disabled ? "Trabajo actual" : selected}</span><CalendarDays size={17} /></button>
    {open && !disabled && <div className="month-calendar" id={`${id}-calendar`} role="dialog" aria-labelledby={`${id}-label`}><header><div><strong>Mes y año</strong><small>Escribe el año y elige el mes</small></div><button type="button" aria-label="Cerrar calendario" onClick={close}><X size={16} /></button></header><div className="month-year-control"><button type="button" aria-label="Año anterior" disabled={Number(year) <= minimum || !year} onClick={() => setYear(String(Number(year) - 1))}><ChevronLeft size={18} /></button><input ref={yearInput} type="number" aria-label={`Año de ${label.toLowerCase()}`} min={minimum} max={maximum} value={year} onChange={(event) => setYear(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); setYear(String(Math.max(minimum, Math.min(maximum, Number(year) || maximum)))); } }} onBlur={() => setYear(String(Math.max(minimum, Math.min(maximum, Number(year) || maximum))))} /><button type="button" aria-label="Año siguiente" disabled={Number(year) >= maximum || !year} onClick={() => setYear(String(Number(year) + 1))}><ChevronRight size={18} /></button></div><div className="month-grid">{MONTHS.map((name, index) => {
      const { value: next, disabled: unavailable } = monthChoice(year, index, min, max);
      return <button type="button" key={name} disabled={unavailable} aria-pressed={next === value} onClick={() => choose(next)}>{name}</button>;
    })}</div><footer><button type="button" disabled={!value} onClick={() => choose("")}>Borrar fecha</button><button type="button" disabled={max < min || max !== new Date().toISOString().slice(0, 7)} onClick={() => choose(max)}>Este mes</button></footer></div>}
  </div>;
}
