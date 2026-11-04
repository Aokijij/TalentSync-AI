import documents from "../../../backend/legal_documents/current.json";
import { LockKeyhole, ShieldCheck } from "lucide-react";
import { ConsentChoice } from "./ConsentChoice.jsx";
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
    <div className="registration-consent-choices">
      <ConsentChoice title="Tratamiento de datos personales" description={documents.data_processing_notice} checked={values.data_processing_accepted === true} onChange={(event) => onChange("data_processing_accepted", event.target.checked)} href={`${documents.privacy_path}${company ? "?rol=empresa" : ""}`} linkText="Leer Política de privacidad" />
      <ConsentChoice title="Términos de uso" description={documents.terms_notice} checked={values.terms_accepted === true} onChange={(event) => onChange("terms_accepted", event.target.checked)} href={`${documents.terms_path}${company ? "?rol=empresa" : ""}`} linkText="Leer Términos de uso" />
    </div>
    <div id="registration-legal-note" className="registration-consent-note"><LockKeyhole size={15} /><p>Guardamos la fecha y la versión de los documentos aceptados. Puedes ejercer tus derechos desde Seguridad y privacidad o por el contacto indicado en la política.</p></div>
    {error && <p role="alert" className="registration-consent-error">{error}</p>}
  </fieldset>;
}
