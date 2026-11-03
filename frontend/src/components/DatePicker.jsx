import { useEffect, useId, useRef, useState } from "react";
import { CalendarDays, ChevronLeft, ChevronRight, X } from "lucide-react";
import { calendarDays, localToday, shiftDate, shiftMonth } from "../utils/calendar.js";

const months = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"];
const fullDate = (day) => new Date(`${day}T12:00:00Z`).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

export function DatePicker({ label, value, defaultValue = "", onChange, name, min = "1900-01-01", max = "2100-12-31", disabled = false, id: controlId, ...controlProps }) {
  const generatedId = useId(), id = controlId || generatedId, root = useRef(null), trigger = useRef(null);
  const [internal, setInternal] = useState(defaultValue), [open, setOpen] = useState(false), [month, setMonth] = useState((value || defaultValue || localToday()).slice(0, 7));
  const [placement, setPlacement] = useState("");
  const selected = value === undefined ? internal : value, today = localToday();
  const allowed = (day) => day >= min && day <= max;
  const close = () => { setOpen(false); trigger.current?.focus(); };
  const choose = (day) => { setInternal(day); onChange?.(day); close(); };
  const toggle = () => {
    const rect = root.current.getBoundingClientRect();
    setPlacement(`${window.innerHeight - rect.bottom < 380 && rect.top > 380 ? "is-above" : ""} ${rect.left + 320 > window.innerWidth - 24 ? "align-right" : ""}`);
    setMonth((selected || today).slice(0, 7)); setOpen(!open);
  };
  useEffect(() => {
    if (!open) return;
    const outside = (event) => { if (!root.current?.contains(event.target)) setOpen(false); };
    document.addEventListener("pointerdown", outside);
    root.current?.querySelector(`[data-day="${selected || today}"]`)?.focus();
    return () => document.removeEventListener("pointerdown", outside);
  }, [open, selected, today]);
  const move = (event, day) => {
    const shifts = { ArrowLeft: -1, ArrowRight: 1, ArrowUp: -7, ArrowDown: 7 };
    if (!(event.key in shifts)) return;
    event.preventDefault(); const next = shiftDate(day, shifts[event.key]);
    if (!allowed(next)) return;
    setMonth(next.slice(0, 7));
    requestAnimationFrame(() => root.current?.querySelector(`[data-day="${next}"]`)?.focus());
  };
  const days = calendarDays(month), year = Number(month.slice(0, 4));
  return <div className="date-picker" ref={root} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }} onKeyDown={(event) => { if (event.key === "Escape") { event.preventDefault(); close(); } }}><label id={`${id}-label`} htmlFor={`${id}-trigger`}>{label}</label>{name && <input type="hidden" name={name} value={selected || ""} disabled={disabled} />}<button {...controlProps} ref={trigger} id={`${id}-trigger`} type="button" className="date-picker-trigger field-control" disabled={disabled} aria-labelledby={`${id}-label ${id}-value`} aria-haspopup="dialog" aria-expanded={open} onClick={toggle}><span id={`${id}-value`}>{selected ? fullDate(selected) : "Selecciona una fecha"}</span><CalendarDays size={18} /></button>
    {open && <div className={`date-picker-panel ${placement}`} role="dialog" aria-labelledby={`${id}-label`}><header><strong>Elige una fecha</strong><button type="button" aria-label="Cerrar calendario" onClick={close}><X size={17} /></button></header><div className="date-picker-navigation"><button type="button" aria-label="Mes anterior" disabled={shiftMonth(month, -1) < min.slice(0, 7)} onClick={() => setMonth(shiftMonth(month, -1))}><ChevronLeft size={19} /></button><select aria-label="Mes" value={Number(month.slice(5)) - 1} onChange={(event) => setMonth(`${year}-${String(Number(event.target.value) + 1).padStart(2, "0")}`)}>{months.map((label, index) => <option key={label} value={index}>{label}</option>)}</select><select aria-label="Año" value={year} onChange={(event) => setMonth(`${event.target.value}-${month.slice(5)}`)}>{Array.from({ length: Number(max.slice(0, 4)) - Number(min.slice(0, 4)) + 1 }, (_, index) => Number(min.slice(0, 4)) + index).map((year) => <option key={year}>{year}</option>)}</select><button type="button" aria-label="Mes siguiente" disabled={shiftMonth(month, 1) > max.slice(0, 7)} onClick={() => setMonth(shiftMonth(month, 1))}><ChevronRight size={19} /></button></div>
    <table className="date-picker-days"><thead><tr>{["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"].map((day) => <th key={day} scope="col">{day}</th>)}</tr></thead><tbody>{Array.from({ length: 6 }, (_, week) => <tr key={week}>{days.slice(week * 7, week * 7 + 7).map((day) => <td key={day}><button type="button" data-day={day} className={day.slice(0, 7) !== month ? "other-month" : ""} aria-label={fullDate(day)} aria-pressed={day === selected} aria-current={day === today ? "date" : undefined} disabled={!allowed(day)} onKeyDown={(event) => move(event, day)} onClick={() => choose(day)}>{Number(day.slice(-2))}</button></td>)}</tr>)}</tbody></table><footer><button type="button" disabled={!selected} onClick={() => choose("")}>Borrar fecha</button><button type="button" disabled={!allowed(today)} onClick={() => choose(today)}>Hoy</button></footer></div>}
  </div>;
}
