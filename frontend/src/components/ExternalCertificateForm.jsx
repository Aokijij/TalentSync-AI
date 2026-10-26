import { useState } from "react";
import { Award, Building2, CheckCircle2, ExternalLink, FilePenLine, Link2, Save, X } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import "../styles/learning-paths.css";
import "../styles/learning-catalog.css";

export function ExternalCertificateForm({ plan, onChanged }) {
  const { confirm, notify } = useFeedback();
  const [open, setOpen] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState(""), [saved, setSaved] = useState(null), [dirty, setDirty] = useState(false);
  const certificate = saved || plan.certificate, provider = plan.resource?.provider;
  if (!plan.resource?.url || !plan.progress?.course_completed || plan.status !== "completed") return null;
  if (!certificate && plan.resource.details?.certificate_cost === "none") return <section className="certificate-panel"><header><Award size={24} /><div><h3>Formación sin certificado anunciado</h3><p>Consulta en {provider} si dispone de otras opciones de acreditación.</p></div></header></section>;
  async function close() {
    if (!dirty || await confirm({ title: "Descartar cambios del certificado", description: "Los datos que todavía no guardaste se perderán.", confirmLabel: "Descartar cambios", destructive: true })) { setOpen(false); setDirty(false); setError(""); }
  }
  async function save(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget); setBusy(true); setError("");
    try {
      const { data } = await api.post(`/learning/plans/${plan.resource.id}/certificate`, { name: values.get("name"), credential_url: values.get("credential_url"), year: Number(values.get("year")), certificate_id: values.get("certificate_id") || "", has_certificate: values.has("has_certificate") }, { __quiet: true });
      setSaved(data.certificate); setOpen(false); setDirty(false);
      notify("El documento se ha añadido a tu perfil con su proveedor y enlace.", { title: "Certificado guardado" }); await onChanged?.();
    } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <section className={`certificate-panel external-certificate certificate-v4 ${certificate ? "certificate-supplied" : ""}`}>
    <header><span className="learning-area-icon">{certificate ? <CheckCircle2 size={25} /> : <Award size={25} />}</span><div><p className="section-kicker">TU FORMACIÓN</p><h3>{certificate ? "Tu certificado" : "Añade el certificado que recibiste"}</h3><p>{certificate ? `${certificate.name} · ${certificate.issuer || provider} · ${certificate.year}` : `Conserva el documento emitido por ${provider} y su enlace de consulta.`}</p></div>{open ? <button type="button" className="button-secondary certificate-close" disabled={busy} aria-label="Cerrar formulario del certificado" onClick={close}><X size={18} /></button> : <span className="learning-tag">{certificate ? "Aportado por ti" : "Opcional"}</span>}</header>
    {!open && <div className="certificate-panel-actions">{certificate && <a className="button-primary button-sm" href={certificate.url} target="_blank" rel="noopener noreferrer"><ExternalLink size={16} />Ver certificado</a>}<button type="button" className={`${certificate ? "button-secondary" : "button-primary"} certificate-add-action`} onClick={() => setOpen(true)}><FilePenLine size={17} />{certificate ? "Editar datos" : "Aportar certificado"}</button>{certificate ? <Link className="button-ghost certificate-profile-link" to="/perfil#profile-certifications">Ver en mi perfil<ExternalLink size={14} /></Link> : <a className="certificate-profile-link" href={plan.resource.url} target="_blank" rel="noopener noreferrer">Consultar proveedor<ExternalLink size={14} /></a>}</div>}
    {open && <form onSubmit={save} onChange={() => setDirty(true)}>
      <div className="certificate-provider-strip"><Building2 size={21} /><label>Proveedor o entidad emisora<input aria-label="Proveedor o entidad emisora" value={provider} readOnly /></label><CheckCircle2 size={17} aria-hidden="true" /></div>
      <fieldset disabled={busy} className="certificate-fields"><legend className="sr-only">Datos del certificado</legend>
        <label className="certificate-name">Nombre del certificado<input className="field-control" name="name" defaultValue={certificate?.name || plan.resource.title} placeholder="Escribe el nombre que aparece en tu documento" required minLength={3} maxLength={160} /></label>
        <label>Año de expedición<input className="field-control" name="year" type="number" defaultValue={certificate?.year || new Date().getFullYear()} min={1970} max={new Date().getFullYear()} required /></label>
        <label className="wide">Enlace del certificado<span className="certificate-url-input"><Link2 size={17} /><input className="field-control" name="credential_url" aria-label="Enlace del certificado" type="url" pattern="https://.*" defaultValue={certificate?.url || ""} placeholder="Pega el enlace público de tu certificado" required maxLength={1000} aria-describedby="certificate-url-help" /></span><small id="certificate-url-help">Enlace HTTPS al documento o a su verificación, distinto al enlace del curso.</small></label>
        <details className="certificate-id-details"><summary>Añadir identificador de credencial <span>(opcional)</span></summary><label>Identificador de credencial<input className="field-control" name="certificate_id" defaultValue={certificate?.certificate_id || ""} placeholder="Escribe el código de credencial que incluye el documento" maxLength={120} /></label></details>
        <label className="certificate-confirm"><input type="checkbox" name="has_certificate" required /><span>Confirmo que {provider} me expidió este certificado y que el enlace corresponde a mi documento.</span></label>
      </fieldset>
      <p className="certificate-scope">Se incorpora como documento aportado por ti, sin verificación de autenticidad por TalentSync.</p>
      {error && <p role="alert" className="welcome-alert">{error}</p>}
      <footer><button type="button" className="button-secondary" disabled={busy} onClick={close}>Cancelar</button><button className="button-primary" disabled={busy}><Save size={17} />{busy ? "Guardando…" : "Guardar certificado"}</button></footer>
    </form>}
  </section>;
}
