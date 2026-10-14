import { useEffect, useMemo, useState } from "react";
import { Download, Eye, RefreshCw } from "lucide-react";
import { CoachDialog } from "./CoachDialog.jsx";
import { ResumeDesignControls } from "./ResumeDesignControls.jsx";
import { api, getApiErrorMessage } from "../api/client.js";
import { getResumePalette } from "../constants/resumePalettes.js";
import { exportSections, resumeExportPayload } from "../utils/resumeExport.js";
import "../styles/resume-export.css";

export function ResumeExportDialog({ open, onClose, profile, name, photoVersion, onPhoto }) {
  const [sections, setSections] = useState(() => exportSections.map(([key]) => key));
  const [includePhoto, setIncludePhoto] = useState(true), [style, setStyle] = useState(profile.resume_style), [color, setColor] = useState(profile.resume_color);
  const [preview, setPreview] = useState(null), [busy, setBusy] = useState(false), [error, setError] = useState(""), [retry, setRetry] = useState(0);
  const payload = useMemo(() => resumeExportPayload(profile, name, { sections, includePhoto, style, color }), [profile, name, sections, includePhoto, style, color]);
  const signature = JSON.stringify(payload) + photoVersion;
  const currentPreview = preview?.signature === signature ? preview.url : null;
  useEffect(() => {
    if (!open) return;
    const controller = new AbortController(); let active = true, url;
    setBusy(true); setError(""); setPreview(null);
    const timer = setTimeout(() => {
      api.post("/profiles/me/export", payload, { responseType: "blob", signal: controller.signal, __quiet: true }).then(({ data }) => {
        if (!active) return;
        url = URL.createObjectURL(data); setPreview({ url, signature });
      }).catch(async (failure) => {
        if (!active) return;
        // JSON errors also arrive as Blob when requesting a PDF.
        try { const response = JSON.parse(await failure.response.data.text()); if (active) setError(getApiErrorMessage({ response: { data: response } })); }
        catch { if (active) setError(getApiErrorMessage(failure, "No pudimos preparar la vista previa. Intenta de nuevo.")); }
      }).finally(() => { if (active) setBusy(false); });
    }, 250);
    return () => { active = false; controller.abort(); clearTimeout(timer); if (url) URL.revokeObjectURL(url); };
  }, [open, payload, retry, photoVersion, signature]);
  function download() {
    if (busy || !currentPreview) return;
    const anchor = document.createElement("a"); anchor.href = currentPreview;
    anchor.download = `${String(name || "Candidato").replace(/[\\/:*?"<>|]/g, " ")} - HV.pdf`;
    document.body.append(anchor); anchor.click(); anchor.remove();
  }
  return <CoachDialog open={open} onClose={onClose} title="Diseña y exporta tu hoja de vida" className="resume-export-dialog">
    <div className="resume-export-workspace"><aside className="resume-export-options"><p>Elige qué compartir. Los cambios de esta ventana se aplican al PDF; tu perfil conserva su información.</p>
      <ResumeDesignControls profile={profile} photoVersion={photoVersion} style={style} color={color} onStyle={(next) => { setStyle(next); setColor(getResumePalette(next, color).id); }} onColor={setColor} onPhoto={onPhoto} />
      <fieldset className="resume-section-picker"><legend>¿Qué quieres incluir?</legend><label><input type="checkbox" checked={includePhoto} onChange={(event) => setIncludePhoto(event.target.checked)} />Foto de perfil</label>{exportSections.map(([key, label]) => <label key={key}><input type="checkbox" checked={sections.includes(key)} onChange={(event) => setSections((items) => event.target.checked ? [...items, key] : items.filter((value) => value !== key))} />{label}</label>)}</fieldset>
    </aside><section className="resume-export-preview"><header><span><Eye size={17} />Vista previa del PDF</span><small>Este es el documento que descargarás</small></header>
      {busy && <div role="status" className="resume-preview-placeholder"><RefreshCw size={25} className="animate-spin" /><p>Actualizando tu documento…</p></div>}
      {error && <div role="alert" className="resume-preview-placeholder"><p>{error}</p><button type="button" className="button-secondary" onClick={() => setRetry((value) => value + 1)}>Reintentar</button></div>}
      {currentPreview && !busy && <iframe title="Vista previa exacta de tu hoja de vida" src={currentPreview} />}
      <footer><p>Revisa el contenido y las páginas antes de descargar.</p><button type="button" className="button-primary" disabled={busy || !currentPreview} onClick={download}><Download size={17} />Descargar este PDF</button></footer>
    </section></div>
  </CoachDialog>;
}
