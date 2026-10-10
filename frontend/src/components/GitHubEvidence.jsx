import { useEffect, useState } from "react";
import { Github, Search } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";

export function GitHubEvidence({ onSaved }) {
  const [enabled, setEnabled] = useState(false), [open, setOpen] = useState(false);
  const [preview, setPreview] = useState(null), [selected, setSelected] = useState([]);
  const [busy, setBusy] = useState(false), [error, setError] = useState(""), [notice, setNotice] = useState("");
  useEffect(() => { api.get("/integrations/github/capabilities").then(({ data }) => setEnabled(data.github_public)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function inspect(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    setBusy(true); setError(""); setNotice(""); setPreview(null);
    try {
      const { data } = await api.post("/integrations/github/preview", { url: values.get("repository"), confirm_public_access: true }, { __quiet: true });
      setPreview(data); setSelected(data.report.signals.map((row) => row.skill));
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function save(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    setBusy(true); setError("");
    try {
      const { data } = await api.post("/integrations/github/evidence", { preview_token: preview.preview_token,
        title: values.get("title"), description: values.get("description"), skills: selected, kind: "repository",
        confirm_ownership: true, add_to_profile: values.has("add_to_profile") });
      await onSaved(data); setPreview(null); setNotice("Proyecto guardado como evidencia declarada. Puedes consultar su revisión y retirarlo desde tu perfil.");
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="rounded-xl border border-[var(--line)] p-4">
    <div className="flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-2"><Github size={21} /><h3 className="font-bold">Conecta un proyecto público</h3></div><button type="button" className="button-secondary button-sm" onClick={() => setOpen(!open)} aria-expanded={open}>{open ? "Cerrar" : "Consultar GitHub"}</button></div>
    <p className="mt-2 text-sm leading-6 text-[var(--muted)]">Elige un repositorio y revisa las tecnologías detectadas antes de incorporarlo a tus evidencias.</p>
    {error && <p className="mt-3 text-sm text-[var(--error)]" role="alert">{error}</p>}{notice && <p className="mt-3 text-sm" role="status">{notice}</p>}
    {open && (!enabled ? <p className="mt-3 text-sm text-[var(--muted)]">La consulta pública de GitHub está desactivada en este entorno.</p> : <>
      <form className="mt-4 space-y-3" onSubmit={inspect}><label className="block text-sm">URL del repositorio<input name="repository" className="field-control mt-1" required type="url" maxLength={250} placeholder="https://github.com/usuario/proyecto" disabled={busy} /></label>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" required disabled={busy} className="mt-1" />Autorizo consultar los archivos y manifiestos públicos de este repositorio en GitHub.</label>
        <button className="button-secondary" disabled={busy}><Search size={16} />{busy ? "Consultando…" : "Revisar tecnologías"}</button></form>
      {preview && <div className="mt-5 border-t border-[var(--line)] pt-4"><h4 className="font-bold">Resultado de la consulta</h4><p className="mt-1 break-all text-xs text-[var(--muted)]">Revisión {preview.report.revision.slice(0, 12)} · {preview.report.files_considered} archivos · {preview.report.manifests_read} manifiestos</p>
        <p className="mt-3 text-sm leading-6 text-[var(--muted)]">{preview.report.notice}</p>{preview.report.warnings.map((warning) => <p className="mt-2 text-xs" key={warning}>{warning}</p>)}
        {!preview.report.signals.length ? <p className="mt-3 text-sm">No se detectaron tecnologías compatibles. Puedes registrar el proyecto mediante el formulario de evidencia manual.</p> : <form onSubmit={save} className="mt-4 space-y-3">
          <fieldset><legend className="text-sm font-semibold">Selecciona las tecnologías relacionadas con tu aporte</legend><div className="mt-2 flex flex-wrap gap-2">{preview.report.signals.map((row) => <label key={row.skill} className="flex items-center gap-2 rounded-xl border border-[var(--line)] px-3 py-2 text-sm"><input type="checkbox" checked={selected.includes(row.skill)} disabled={busy} onChange={(event) => setSelected(event.target.checked ? [...selected, row.skill] : selected.filter((skill) => skill !== row.skill))} />{row.skill}</label>)}</div></fieldset>
          <label className="block text-sm">Nombre de tu proyecto<input className="field-control mt-1" name="title" required minLength={3} maxLength={160} defaultValue={preview.report.repository_url.split("/").at(-1)} /></label>
          <label className="block text-sm">Tu participación y el resultado<textarea className="field-control mt-1" name="description" required minLength={10} maxLength={2000} placeholder="Explica qué construiste y cómo se puede revisar tu aporte." /></label>
          <label className="flex items-start gap-2 text-sm"><input type="checkbox" required className="mt-1" />Confirmo mi participación en este proyecto y que puedo compartir esta referencia.</label>
          <label className="flex items-start gap-2 text-sm"><input name="add_to_profile" type="checkbox" className="mt-1" />Añadir también las tecnologías seleccionadas a mis habilidades declaradas.</label>
          <button className="button-primary" disabled={busy || !selected.length}>Guardar proyecto en mi perfil</button><p className="text-xs text-[var(--muted)]">La vista previa vence en 10 minutos. El repositorio seguirá alojado en GitHub.</p>
        </form>}
      </div>}
    </>)}
  </section>;
}
