import { useId, useRef, useState } from "react";
import { ChevronDown, Clock3 } from "lucide-react";
import "../styles/time-picker.css";

const pad = (value) => String(value).padStart(2, "0");
export function TimePicker({ label, value = "", onChange }) {
  const id = useId(), root = useRef(null), trigger = useRef(null), [open, setOpen] = useState(false);
  const hour = value ? Number(value.slice(0, 2)) : null, minute = value ? Number(value.slice(3)) : 0;
  const chooseHour = (next) => onChange(`${pad(next)}:${pad(Math.floor(minute / 5) * 5)}`);
  const chooseMinute = (next) => { onChange(`${pad(hour ?? 0)}:${pad(next)}`); setOpen(false); trigger.current?.focus(); };
  const move = (event, type, number, max, step) => {
    if (!["ArrowRight", "ArrowLeft", "ArrowUp", "ArrowDown"].includes(event.key)) return;
    event.preventDefault();
    const next = (number + (["ArrowLeft", "ArrowUp"].includes(event.key) ? -step : step) + max) % max;
    if (type === "hour") chooseHour(next);
    else onChange(`${pad(hour ?? 0)}:${pad(next)}`);
    root.current?.querySelector(`[data-${type}="${next}"]`)?.focus();
  };
  return <div ref={root} className="time-picker" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }} onKeyDown={(event) => { if (event.key === "Escape") { setOpen(false); trigger.current?.focus(); } }}><label id={`${id}-label`}>{label}</label><button ref={trigger} type="button" className="time-picker-trigger field-control" aria-labelledby={`${id}-label ${id}-value`} aria-haspopup="dialog" aria-expanded={open} onClick={() => { setOpen((current) => !current); if (!open) requestAnimationFrame(() => root.current?.querySelector('[data-hour][tabindex="0"]')?.focus()); }}><Clock3 size={17} /><strong id={`${id}-value`}>{value || "Elegir hora"}</strong><small>24 h</small><ChevronDown size={15} /></button>{open && <div role="dialog" aria-label={`Seleccionar ${label.toLowerCase()}`} className="time-picker-popover"><div><strong>Hora</strong><span>00–23</span></div><div className="time-hour-grid" role="group" aria-label="Horas">{Array.from({ length: 24 }, (_, number) => <button type="button" key={number} data-hour={number} tabIndex={(hour ?? 0) === number ? 0 : -1} aria-pressed={hour === number} onKeyDown={(event) => move(event, "hour", number, 24, 1)} onClick={() => chooseHour(number)}>{pad(number)}</button>)}</div><div><strong>Minutos</strong><span>Cada 5 minutos</span></div><div className="time-minute-grid" role="group" aria-label="Minutos">{Array.from({ length: 12 }, (_, index) => index * 5).map((number) => <button type="button" key={number} data-minute={number} disabled={hour === null} tabIndex={Math.floor(minute / 5) * 5 === number ? 0 : -1} aria-pressed={minute === number} onKeyDown={(event) => move(event, "minute", number, 60, 5)} onClick={() => chooseMinute(number)}>{pad(number)}</button>)}</div><p>Elige la hora y confirma los minutos.</p></div>}</div>;
}
