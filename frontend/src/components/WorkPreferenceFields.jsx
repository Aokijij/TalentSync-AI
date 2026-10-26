import { useId } from "react";
import { Autocomplete } from "./Autocomplete.jsx";
import { CurrencyInput } from "./CurrencyInput.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
import { OCCUPATIONS } from "../constants/occupations.js";
import "../styles/search-settings.css";

const cities = [...new Set(Object.values(COLOMBIA_LOCATIONS).flat())].sort((a, b) => a.localeCompare(b, "es"));
const availability = { immediate: "Disponibilidad inmediata", two_weeks: "Disponible en 15 días", one_month: "Disponible en un mes", negotiable: "A convenir" };
export function WorkPreferenceFields({ value, onChange, includeCareer = false }) {
  const id = useId();
  return <div className="work-preference-fields">
    {includeCareer && <><label>Cargo o área de interés<input className="field-control" aria-label="Cargo o área de interés" list={id} maxLength={160} value={value.profession || ""} onChange={(event) => onChange("profession", event.target.value)} placeholder="Indica el cargo o área que quieres explorar" /><datalist id={id}>{OCCUPATIONS.map((occupation) => <option key={occupation} value={occupation} />)}</datalist><small>Se guarda como tu profesión en Mi perfil.</small></label><div><Autocomplete label="Ciudad" options={cities} value={value.location || ""} onChange={(city) => onChange("location", city)} maxLength={160} placeholder="Busca y elige tu ciudad" /><small>Tu ciudad de residencia; podrás explorar ofertas de otras ubicaciones.</small></div></>}
    <label>Sector profesional<select className="field-control" value={value.preferred_sector || ""} onChange={(event) => onChange("preferred_sector", event.target.value)}><option value="">Sin preferencia definida</option>{JOB_SECTORS.map((sector) => <option key={sector} value={sector}>{sector}</option>)}{value.preferred_sector && !JOB_SECTORS.includes(value.preferred_sector) && <option value={value.preferred_sector}>{value.preferred_sector}</option>}</select></label>
    <label>Disponibilidad<select className="field-control" value={value.availability || ""} onChange={(event) => onChange("availability", event.target.value)}><option value="">Sin preferencia definida</option>{Object.entries(availability).map(([key, label]) => <option key={key} value={key}>{label}</option>)}{value.availability && !availability[value.availability] && <option value={value.availability}>{value.availability}</option>}</select></label>
    <label>Modalidad<select aria-label="Modalidad" className="field-control" value={value.preferred_modality || ""} onChange={(event) => onChange("preferred_modality", event.target.value)}><option value="">Sin preferencia definida</option><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option>{value.preferred_modality && !["remote", "hybrid", "onsite"].includes(value.preferred_modality) && <option value={value.preferred_modality}>{value.preferred_modality}</option>}</select></label>
    <label>Aspiración mensual en COP<CurrencyInput aria-label="Aspiración mensual en COP" value={value.desired_salary ?? ""} onChange={(salary) => onChange("desired_salary", salary)} placeholder="Indica el importe mensual que buscas" maxLength={18} /><small>Opcional. Deja el campo vacío si aún no la has definido.</small></label>
  </div>;
}
