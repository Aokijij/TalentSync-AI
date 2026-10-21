import { LockKeyhole } from "lucide-react";
import { DatePicker } from "./DatePicker.jsx";
import { FormField } from "./ProfileFormFeedback.jsx";
import { localToday } from "../utils/calendar.js";

export function PrivateProfileDetails({ birthDate, editing, onChange }) {
  return <div className="profile-private"><div className="profile-private-note"><LockKeyhole size={18} /><p>Solo tú puedes ver esta información. No se comparte con empresas, no aparece en tu CV y no se utiliza para calcular compatibilidad.</p></div>{editing ? <FormField path="birth_date"><DatePicker label="Fecha de nacimiento (opcional)" value={birthDate || ""} max={localToday()} onChange={(day) => onChange(day || null)} /></FormField> : <dl><dt>Fecha de nacimiento</dt><dd>{birthDate ? new Date(`${birthDate}T12:00:00Z`).toLocaleDateString("es-CO", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" }) : "Sin registrar"}</dd></dl>}</div>;
}
