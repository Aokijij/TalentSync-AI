import documents from "../../../backend/legal_documents/current.json";
import { ExternalLink, ShieldCheck } from "lucide-react";
import "../styles/registration-consent.css";

export const registrationLegalPayload = (values) => ({
  data_processing_accepted: values.data_processing_accepted === true,
  terms_accepted: values.terms_accepted === true,
  privacy_version: documents.privacy_version,
  terms_version: documents.terms_version,
});

export function RegistrationConsent({ values, onChange, error, disabled = false, company = false }) {
  return <fieldset className="registration-consent" disabled={disabled} aria-describedby="registration-legal-note">
    <legend><ShieldCheck size={18} />Tu cuenta, con tu autorización</legend>
    <p>Lee los documentos y confirma cada decisión. Estas casillas no autorizan publicidad ni conexiones con Google Calendar.</p>
    <label><input type="checkbox" checked={values.data_processing_accepted === true} onChange={(event) => onChange("data_processing_accepted", event.target.checked)} /><span>{documents.data_processing_notice}<a href={`${documents.privacy_path}${company ? "?rol=empresa" : ""}`} target="_blank" rel="noopener noreferrer">Leer Política de privacidad<ExternalLink size={13} /></a></span></label>
    <label><input type="checkbox" checked={values.terms_accepted === true} onChange={(event) => onChange("terms_accepted", event.target.checked)} /><span>{documents.terms_notice}<a href={`${documents.terms_path}${company ? "?rol=empresa" : ""}`} target="_blank" rel="noopener noreferrer">Leer Términos de uso<ExternalLink size={13} /></a></span></label>
    <small id="registration-legal-note">Guardamos la fecha y la versión de los documentos aceptados. Puedes ejercer tus derechos desde Seguridad y privacidad o por el contacto indicado en la política.</small>
    {error && <p role="alert" className="registration-consent-error">{error}</p>}
  </fieldset>;
}
