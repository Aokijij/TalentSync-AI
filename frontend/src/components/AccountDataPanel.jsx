import { useEffect, useState } from "react";
import { Download, FileArchive, Trash2 } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { InlineNotice } from "./ui/Panel.jsx";
import { saveBlob } from "../utils/preparation.js";
import "../styles/account-controls.css";

export function AccountDataPanel({ user, onDeleted }) {
  const { confirm } = useFeedback();
  const [status, setStatus] = useState(null), [error, setError] = useState(""), [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false), [action, setAction] = useState("export");
  useEffect(() => { let active = true; api.get("/account/data").then(({ data }) => { if (active) setStatus(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); }); return () => { active = false; }; }, []);
  async function submit(event) {
    event.preventDefault();
    if (busy) return;
    const form = event.currentTarget, values = new FormData(form);
    const payload = { password: values.get("password"), code: values.get("code") || null };
    setBusy(true);
    if (action === "erase") {
      payload.confirmation = values.get("confirmation");
      if (!await confirm({ title: "Eliminar tu cuenta", description: "Se retirarán tu perfil, CV, postulaciones, prácticas y sesiones. La acción es permanente. Las copias ya descargadas y las copias de seguridad siguen su propio plazo de conservación.", confirmLabel: "Eliminar mi cuenta", destructive: true })) { setBusy(false); return; }
    }
    setBusy(true); setError(""); setNotice("");
    try {
      if (action === "export") {
        const { data } = await api.post("/account/data/export", payload, { responseType: "blob", __quiet: true });
        saveBlob(data, "TalentSync-mis-datos.zip");
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
    {status && <><div className="account-action-options" role="group" aria-label="Acción sobre tus datos"><button type="button" disabled={busy} aria-pressed={action === "export"} onClick={() => { setAction("export"); setError(""); setNotice(""); }}><Download size={20} /><strong>Descargar mis datos</strong><span>JSON, CV guardados y archivos disponibles.</span></button><button type="button" disabled={busy} aria-pressed={action === "erase"} onClick={() => { setAction("erase"); setError(""); setNotice(""); }}><Trash2 size={20} /><strong>Eliminar mi cuenta</strong><span>Retira tus datos y cierra todas tus sesiones.</span></button></div>
    {action === "erase" && <InlineNotice tone="warning">{status.deletion_block || status.note}</InlineNotice>}
    <form onSubmit={submit}><fieldset disabled={busy || (action === "erase" && Boolean(status.deletion_block))}><legend>Confirma tu identidad</legend><p>Utiliza tu contraseña de TalentSync. Si accedes con Google y no tienes contraseña, crea una mediante Recuperar acceso.</p><div className="account-credential-grid"><label>Contraseña actual<input className="field-control" name="password" type="password" autoComplete="current-password" required /></label>{user.mfa_enabled && <label>Código de autenticador o recuperación<input className="field-control" name="code" autoComplete="one-time-code" required /></label>}{action === "erase" && <label>Escribe ELIMINAR<input className="field-control" name="confirmation" pattern="ELIMINAR" required autoComplete="off" /></label>}</div><footer><span>{action === "export" ? "La copia excluye contraseñas y notas privadas de empresas." : "Esta acción es permanente."}</span><button className={action === "erase" ? "button-secondary account-erase" : "button-primary"} disabled={busy}>{action === "export" ? <Download size={17} /> : <Trash2 size={17} />}{busy ? "Procesando…" : action === "export" ? "Descargar copia ZIP" : "Eliminar mi cuenta"}</button></footer></fieldset></form></>}
  </section>;
}
