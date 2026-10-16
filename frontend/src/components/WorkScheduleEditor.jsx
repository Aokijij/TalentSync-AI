import { CalendarDays, Clock3 } from "lucide-react";
import { EMPTY_WORK_SCHEDULE, WORK_DAYS, scheduleHours, scheduleSummary } from "../utils/workSchedule.js";
import "../styles/work-schedule.css";

export function WorkScheduleEditor({ details, onChange }) {
  const value = details.work_schedule || { ...EMPTY_WORK_SCHEDULE, mode: details.schedule ? "custom" : "fixed" };
  const hours = scheduleHours(value);
  const change = (changes) => {
    const next = { ...value, ...changes };
    onChange({ ...details, work_schedule: next, schedule: next.mode === "custom" ? details.schedule : scheduleSummary(next) });
  };
  return <section className="work-schedule-editor"><header><CalendarDays size={19} /><div><h3>Jornada y horario <span>Opcional</span></h3><p>Selecciona los días y las horas, o describe una jornada flexible.</p></div></header>
    <div className="schedule-modes" role="group" aria-label="Tipo de horario">{[["fixed", "Horario fijo"], ["rotating", "Por turnos"], ["flexible", "Flexible"], ["custom", "Escribir horario"]].map(([key, label]) => <button type="button" key={key} aria-pressed={value.mode === key} onClick={() => change({ mode: key })}>{label}</button>)}</div>
    {value.mode === "custom" ? <label>Describe la jornada<textarea className="field-control" rows={2} maxLength={300} value={details.schedule || ""} onChange={(event) => onChange({ ...details, work_schedule: value, schedule: event.target.value })} placeholder="Ej. Lunes a viernes, de 8:00 a 17:00, con una hora de descanso" /></label> : <>
      <div className="schedule-presets"><span>Días de trabajo</span>{[["Lun–vie", ["mon", "tue", "wed", "thu", "fri"]], ["Lun–sáb", ["mon", "tue", "wed", "thu", "fri", "sat"]], ["Fin de semana", ["sat", "sun"]]].map(([label, days]) => <button type="button" key={label} onClick={() => change({ days })}>{label}</button>)}</div>
      <div className="schedule-days" role="group" aria-label="Días de trabajo">{WORK_DAYS.map(([key, label, short]) => <button type="button" key={key} aria-label={label} aria-pressed={value.days.includes(key)} onClick={() => change({ days: value.days.includes(key) ? value.days.filter((item) => item !== key) : [...value.days, key] })}><b>{short}</b><span>{label.slice(0, 3)}</span></button>)}</div>
      {value.mode === "fixed" && <div className="schedule-times"><label><Clock3 size={14} />Hora de entrada<input className="field-control" type="time" value={value.start} onChange={(event) => change({ start: event.target.value })} /></label><label>Hora de salida<input className="field-control" type="time" value={value.end} onChange={(event) => change({ end: event.target.value })} /></label><label>Descanso<select className="field-control" value={value.break_minutes} onChange={(event) => change({ break_minutes: Number(event.target.value) })}>{[0, 15, 30, 45, 60, 90, 120, 180, 240].map((number) => <option key={number} value={number}>{number ? `${number} minutos` : "Sin descuento"}</option>)}</select></label></div>}
      <label>{value.mode === "rotating" ? "Rotación y franjas de los turnos" : "Aclaraciones (opcional)"}<input className="field-control" maxLength={120} value={value.notes} onChange={(event) => change({ notes: event.target.value })} placeholder={value.mode === "rotating" ? "Ej. Rotación semanal entre turnos de mañana y tarde" : "Ej. La hora de entrada se puede acordar"} /></label>
      {value.mode === "fixed" && value.start && value.end && (value.start === value.end || hours == null && value.days.length > 0) && <p role="status" className="schedule-error">Revisa las horas y el descanso: la jornada debe tener una duración positiva.</p>}
      {(details.schedule || hours != null) && <div className="schedule-summary"><strong>Así se verá en la oferta</strong><p>{details.schedule}</p>{hours != null && <div><span>{hours} horas semanales estimadas, sin descansos</span>{hours >= 1 && hours <= 80 && <button type="button" onClick={() => onChange({ ...details, weekly_hours: hours })}>Usar estas horas</button>}</div>}</div>}
    </>}
  </section>;
}
