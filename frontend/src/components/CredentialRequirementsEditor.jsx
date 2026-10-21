import { useId } from "react";
import { DRIVING_CATEGORIES } from "../constants/credentials.js";
import { AcademicStudyFields } from "./AcademicStudyFields.jsx";

export function CredentialRequirementsEditor({ value = {}, onChange }) {
  const id = useId(), categories = value.driving_categories || [];
  return <section className="credential-requirements-editor"><h3>Documentos para el cargo (opcional)</h3><p className="credential-note">Solicita solo documentos necesarios para las funciones del cargo. Si completas ambos apartados, se solicitan los dos.</p>
    <fieldset><legend>Licencia de conducción · categorías aceptadas en Colombia</legend><div className="credential-categories">{DRIVING_CATEGORIES.map((category) => <label key={category} htmlFor={`${id}-${category}`}><input id={`${id}-${category}`} type="checkbox" checked={categories.includes(category)} onChange={(event) => onChange({ ...value, driving_categories: event.target.checked ? [...categories, category] : categories.filter((item) => item !== category) })} />{category}</label>)}</div><p className="credential-note">Sin selección no se exige licencia. Basta con una categoría marcada; selecciona todas las que admitirías.</p></fieldset>
    <AcademicStudyFields label="Tarjeta profesional para" value={value.professional_cards || []} maxLength={160} onChange={(professional_cards) => onChange({ ...value, professional_cards })} placeholder="Ej. Ingeniería civil" help="Añade la profesión que debe figurar en la tarjeta. Las sugerencias ayudan a escribir el nombre; no validan el documento." />
    <p className="credential-note">Sin profesiones añadidas no se exige tarjeta. Si añades varias, se acepta cualquiera de ellas; no se sustituyen por carreras afines automáticamente.</p>
  </section>;
}
