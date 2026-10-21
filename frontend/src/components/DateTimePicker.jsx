import { DatePicker } from "./DatePicker.jsx";
import { TimePicker } from "./TimePicker.jsx";

export function DateTimePicker({ label, value = "", onChange }) {
  const [date, time = "09:00"] = value.split("T");
  return <fieldset className="date-time-picker"><legend>{label}</legend><div><DatePicker label="Fecha" value={date} onChange={(day) => onChange(day ? `${day}T${time.slice(0, 5)}` : "")} /><fieldset disabled={!date}><TimePicker label="Hora" value={date ? time.slice(0, 5) : ""} onChange={(time) => onChange(`${date}T${time}`)} /></fieldset></div><small>Elige primero el día y después la hora.</small></fieldset>;
}
