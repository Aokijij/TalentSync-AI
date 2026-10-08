import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

const sourceLabels = { dependency: "Dependencia declarada", file_extension: "Tipo de archivo", build_file: "Archivo de construcción", runtime_declaration: "Runtime declarado" };

export function ProjectAnalysisSummary({ analysis }) {
  if (!analysis) return null;
  return <details className="mt-3 rounded-lg border border-[var(--line)] p-3">
    <summary className="cursor-pointer text-sm font-semibold">Ver señales del análisis estático</summary>
    <p className="mt-2 text-xs text-[var(--muted)]">{analysis.files_considered} archivos considerados · {analysis.manifests_read} manifiestos leídos. Estas señales no validan dominio técnico.</p>
    {analysis.revision && <p className="mt-2 break-all text-xs text-[var(--muted)]">Revisión pública de GitHub: {analysis.revision}</p>}
    <ul className="mt-2 space-y-1">{analysis.signals.map((row) => <li key={row.skill} className="text-xs"><strong>{row.skill}</strong>: {row.sources.map((source) => `${sourceLabels[source.kind]} (${source.dependency || source.file})`).join(" · ")}</li>)}</ul>
  </details>;
}

export function ProjectEvidenceImporter({ onSaved }) {
  const [preview, setPreview] = useState(null);
  const [skills, setSkills] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [githubEnabled, setGithubEnabled] = useState(false);
  useEffect(() => { api.get("/matching/projects/options").then(({ data }) => setGithubEnabled(data.github_public_enabled)).catch(() => setGithubEnabled(false)); }, []);
  async function inspectRepository(event) {
    event.preventDefault(); const values = new FormData(event.currentTarget);
    setBusy(true); setError(""); setPreview(null);
    try {
      const { data } = await api.post("/matching/projects/github/preview", { url: values.get("repository"), confirm_public_access: values.has("confirm_public_access") });
      setPreview(data); setSkills(data.report.signals.map((row) => row.skill));
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function inspect(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const upload = new FormData(form);
    setBusy(true); setError(""); setPreview(null);
    try {
      const { data } = await api.post("/matching/projects/preview", upload);
      setPreview(data); setSkills(data.report.signals.map((row) => row.skill)); form.reset();
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  async function save(event) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    setBusy(true); setError("");
    try {
      const response = await api.post("/matching/projects/evidence", {
        title: data.get("title"), description: data.get("description"), url: data.get("url") || null,
        skills, preview_token: preview.preview_token, add_to_profile: data.has("add_to_profile"), confirm_ownership: data.has("confirm_ownership"),
      });
      setPreview(null); await onSaved(response.data);
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <section className="surface-card space-y-4 p-5">
    <h2 className="font-bold">Analizar un proyecto local</h2>
    <p className="text-sm text-[var(--muted)]">Sube un ZIP de tu proyecto, incluido un ZIP descargado de GitHub. Detectamos tecnologías en manifiestos y tipos de archivo. El análisis se realiza en este servidor local: no descarga enlaces, no ejecuta código y no conserva el ZIP.</p>
    <p className="text-xs text-[var(--muted)]">Máximo 8 MiB, 2.000 entradas y 32 MiB descomprimidos. Prepara el ZIP sin dependencias instaladas, archivos generados ni secretos. Se leen hasta 32 manifiestos de 256 KiB; se omiten carpetas como node_modules, .git y .venv.</p>
    <form className="flex flex-wrap items-end gap-3" onSubmit={inspect}>
      <label className="min-w-0 flex-1 text-sm">ZIP del proyecto<input className="field-control mt-1 max-w-full" required name="file" type="file" accept=".zip,application/zip,application/x-zip-compressed" /></label>
      <button className="button-secondary" disabled={busy}>{busy ? "Procesando…" : "Analizar ZIP"}</button>
    </form>
    {githubEnabled && <details className="rounded-lg border border-[var(--line)] p-4"><summary className="cursor-pointer font-semibold">Analizar un repositorio público de GitHub</summary><p className="my-3 text-sm text-[var(--muted)]">Consultaremos GitHub únicamente al enviar este formulario. Leemos el árbol de archivos y hasta 32 manifiestos; no clonamos el proyecto, ejecutamos código ni accedemos a repositorios privados. Esto no confirma tu autoría.</p><form className="space-y-3" onSubmit={inspectRepository}><label className="block text-sm">URL raíz del repositorio<input className="field-control mt-1" name="repository" type="url" required maxLength={250} placeholder="https://github.com/propietario/repositorio" /></label><label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" required name="confirm_public_access" />Autorizo consultar este repositorio público en GitHub para preparar la vista previa.</label><button className="button-secondary" disabled={busy}>Analizar repositorio público</button></form></details>}
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    {preview && <div className="space-y-4 border-t border-[var(--line)] pt-4">
      <p className="text-sm">{preview.report.files_considered} archivos considerados · {preview.report.manifests_read} manifiestos leídos · {preview.report.files_ignored} archivos omitidos</p>
      <p className="text-sm text-[var(--muted)]">{preview.report.notice}</p>
      {preview.report.warnings.map((warning) => <p key={warning} className="text-sm">{warning}</p>)}
      {!preview.report.signals.length && <p>No encontramos tecnologías compatibles con este analizador. Puedes añadir tu evidencia manualmente.</p>}
      {preview.report.revision && <p className="break-all text-xs text-[var(--muted)]">Revisión analizada: {preview.report.revision}</p>}
      {preview.report.signals.length > 0 && <form key={preview.report.fingerprint} className="space-y-4" onSubmit={save}>
        <fieldset className="space-y-3"><legend className="mb-3 font-semibold">Selecciona las tecnologías que quieres declarar</legend>
          {preview.report.signals.map((row) => <label className="flex items-start gap-3 rounded-lg border border-[var(--line)] p-3" key={row.skill}>
            <input type="checkbox" className="mt-1" checked={skills.includes(row.skill)} onChange={(event) => setSkills(event.target.checked ? [...skills, row.skill] : skills.filter((skill) => skill !== row.skill))} />
            <span className="min-w-0"><strong className="block text-sm">{row.skill}</strong><span className="block text-xs text-[var(--muted)]">{row.source_files ? `${row.source_files} archivos por extensión. ` : ""}{row.sources.map((source) => `${sourceLabels[source.kind]}: ${source.dependency || source.file}`).join(" · ")}</span></span>
          </label>)}
        </fieldset>
        <label className="block text-sm">Nombre de la evidencia<input className="field-control mt-1" name="title" required minLength={3} maxLength={160} /></label>
        <label className="block text-sm">Enlace al proyecto (opcional)<input className="field-control mt-1" name="url" type="url" defaultValue={preview.report.repository_url || ""} readOnly={Boolean(preview.report.repository_url)} /></label>
        <label className="block text-sm">Tu contribución y cómo se puede comprobar<textarea className="field-control mt-1" name="description" required minLength={10} maxLength={2000} /></label>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" name="add_to_profile" />Añadir las tecnologías seleccionadas a mis habilidades declaradas. Esto puede cambiar mi afinidad; no las convierte en habilidades verificadas.</label>
        <label className="flex items-start gap-2 text-sm"><input type="checkbox" className="mt-1" name="confirm_ownership" required />Confirmo mi participación en este proyecto y que puedo aportar esta evidencia.</label>
        <p className="text-xs text-[var(--muted)]">La vista previa vence en diez minutos. Se guarda el resumen técnico, sin nombres de archivos internos ni contenido del proyecto.</p>
        <div className="flex flex-wrap gap-3"><button className="button-primary" disabled={busy || !skills.length}>Guardar evidencia del proyecto</button><button className="button-secondary" type="button" disabled={busy} onClick={() => setPreview(null)}>Descartar vista previa</button></div>
      </form>}
    </div>}
  </section>;
}
