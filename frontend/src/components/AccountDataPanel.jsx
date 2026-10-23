import { useEffect, useState } from "react";
import { Download, FileArchive, ShieldCheck, Trash2 } from "lucide-react";
import { Link } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { InlineNotice } from "./ui/Panel.jsx";
import { saveBlob } from "../utils/preparation.js";
import "../styles/account-controls.css";

export function AccountDataPanel({ user, onDeleted }) {
  const { confirm } = useFeedback();
  const [status, setStatus] = useState(null), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false), [action, setAction] = useState(null);
  useEffect(() => { let active = true; api.get("/account/data").then(({ data }) => { if (active) setStatus(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); }); return () => { active = false; }; }, []);
  async function submit(event) {
    event.preventDefault();
    if (busy || !action) return;
    const form = event.currentTarget, values = new FormData(form);
    const payload = { password: values.get("password"), code: values.get("code") || null };
    setBusy(true);
    if (action === "erase") {
      payload.confirmation = values.get("confirmation");
      if (!await confirm({ title: "Eliminar tu cuenta", description: "Se retirarán tu perfil, CV, postulaciones, prácticas y sesiones. La acción es permanente. Las copias ya descargadas y las copias de seguridad siguen su propio plazo de conservación.", confirmLabel: "Eliminar mi cuenta", destructive: true })) { setBusy(false); return; }
    }
    form.elements.password.value = "";
    if (form.elements.code) form.elements.code.value = "";
    setBusy(true); setError(""); setNotice("");
    try {
      if (action === "export") {
        const { data } = await api.post("/account/data/export", payload, { responseType: "blob", __quiet: true });
        saveBlob(data, "TalentSync-mis-datos.zip");
        setAction(null);
        setNotice("Copia descargada. Contiene datos personales: guárdala en un lugar privado.");
      } else {
        const { data } = await api.post("/account/data/erase", payload, { __quiet: true });
        sessionStorage.setItem("talentsync_account_erasure", JSON.stringify({ receipt: data.receipt, message: data.message }));
        await onDeleted();
      }
      form.reset();
    } catch (failure) {
      try { if (failure.response?.data instanceof Blob) failure.response.data = JSON.parse(await failure.response.data.text()); } catch { /* Generic error when the server did not return JSON. */ }
      setError(getApiErrorMessage(failure));
    } finally { setBusy(false); }
  }
  return <section id="security-data" className="security-panel account-controls"><header><FileArchive size={24} /><div><h2>Control de tus datos</h2><p>Descarga una copia o gestiona la eliminación de tu cuenta.</p></div></header>
    {error && <InlineNotice error>{error}</InlineNotice>}{notice && <InlineNotice tone="success">{notice}</InlineNotice>}
    {!status && !error && <p role="status">Consultando tus opciones…</p>}
    {status && <>
      <article className="data-export-card"><span className="data-action-icon"><Download size={23} /></span><div><h3>Tu información, disponible para ti</h3><p>Descarga un ZIP con tus datos, CV guardados y archivos disponibles.</p><small>Excluye contraseñas y notas privadas de empresas.</small></div><button type="button" className="button-primary" disabled={busy} onClick={() => { setAction("export"); setError(""); setNotice(""); }}><Download size={16} />Preparar descarga</button></article>
      {action && <form className="data-identity-form" key={action} onSubmit={submit}><fieldset disabled={busy || (action === "erase" && Boolean(status.deletion_block))}><legend><ShieldCheck size={18} />{action === "export" ? "Confirma la descarga" : "Confirma la eliminación"}</legend><p>Por tu privacidad, confirma con tu contraseña de TalentSync.</p><details className="data-password-help"><summary>¿Entras con Google o GitHub y no tienes contraseña?</summary><p>Establece una desde <Link to="/recuperar-acceso">Recuperar acceso</Link> y vuelve a esta pantalla.</p></details>{action === "erase" && <InlineNotice tone="warning">{status.deletion_block || status.note}</InlineNotice>}<div className="account-credential-grid"><label>Contraseña actual<input className="field-control" name="password" type="password" autoComplete="current-password" required /></label>{user.mfa_enabled && <label>Código de autenticador o recuperación<input className="field-control" name="code" autoComplete="one-time-code" required /></label>}{action === "erase" && <label>Escribe ELIMINAR<input className="field-control" name="confirmation" pattern="ELIMINAR" required autoComplete="off" /></label>}</div><footer><button type="button" className="button-secondary" disabled={busy} onClick={() => { setAction(null); setError(""); }}>Cancelar</button><button className={action === "erase" ? "button-secondary account-erase" : "button-primary"} disabled={busy}>{action === "export" ? <Download size={17} /> : <Trash2 size={17} />}{busy ? "Procesando…" : action === "export" ? "Descargar copia ZIP" : "Eliminar mi cuenta"}</button></footer></fieldset></form>}
      <article className="data-danger-zone"><div><h3>Eliminar mi cuenta</h3><p>Retira tu perfil y tus datos, y cierra todas tus sesiones. Es permanente.</p>{status.deletion_block && <small>{status.deletion_block}</small>}</div><button type="button" className="button-ghost account-erase" disabled={busy || !!status.deletion_block} onClick={() => { setAction("erase"); setError(""); setNotice(""); }}><Trash2 size={16} />Solicitar eliminación</button></article>
    </>}

  </section>;
}
