import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { ChevronDown, Link2 } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { GitHubEvidence } from "./GitHubEvidence.jsx";
import { CodewarsEvidence } from "./CodewarsEvidence.jsx";
import { programmingEvidenceRelevant } from "../utils/evidenceContext.js";

export function ProfileEvidence({ profile, onChanged }) {
  const { confirm } = useFeedback();
  const location = useLocation();
  useEffect(() => { if (location.hash === "#evidencias") document.getElementById("evidencias")?.scrollIntoView({ block: "start" }); }, [location.hash]);
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [toolsActivated, setToolsActivated] = useState(false);
  const programmingRelevant = programmingEvidenceRelevant(profile, rows);
  useEffect(() => { api.get("/matching/evidence").then(({ data }) => setRows(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  return <details className="surface-card p-5" id="evidencias" open={location.hash === "#evidencias" ? true : undefined}>
    <summary className="cursor-pointer font-bold">Evidencias de mi experiencia · {rows.length}</summary>
    <div className="mt-4 space-y-4">
      <p className="text-sm text-[var(--muted)]">Relaciona un logro, una muestra de trabajo o una certificación con tus habilidades. Se muestran junto a los requisitos de las vacantes y, con tu permiso, a las empresas de tus procesos. Los enlaces se conservan sin descargar archivos.</p>
      {error && <p role="alert" className="text-[var(--error)]">{error}</p>}
      {message && <p role="status">{message} <Link className="text-[var(--accent)]" to="/recomendaciones">Ver compatibilidad actualizada</Link></p>}
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={(event) => {
        event.preventDefault(); const form = event.currentTarget; const data = new FormData(form);
        act(async () => {
          const response = await api.post("/matching/evidence", {
            title: data.get("title"), kind: data.get("kind"), url: data.get("url") || null,
            skills: data.get("skills").split(",").map((skill) => skill.trim()).filter(Boolean),
            description: data.get("description"), add_to_profile: data.has("add_to_profile"),
          });
          setRows(response.data); await onChanged?.(); form.reset();
          setMessage(data.has("add_to_profile") ? "Evidencia vinculada. Las habilidades declaradas se incorporaron al perfil y se usarán al recalcular las recomendaciones." : "Evidencia vinculada a tus habilidades. Puedes verla al desplegar la compatibilidad de una vacante.");
        });
      }}>
        <div className="sm:col-span-2">
          <h3 className="font-semibold">Agrega un logro, trabajo o certificado</h3>
          <p className="mt-1 text-sm text-[var(--muted)]">Puede ser una mejora en tu trabajo, una muestra de tu portafolio o un certificado de formación.</p>
        </div>
        <label>Logro o muestra de trabajo<input className="field-control mt-1" name="title" required minLength={3} maxLength={160} placeholder="Ej.: Mejora del inventario mensual" /></label>
        <label>Tipo<select className="field-control mt-1" name="kind"><option value="experience">Logro laboral</option><option value="portfolio">Portafolio</option><option value="certificate">Certificado externo</option><option value="project">Proyecto</option>{(programmingRelevant || toolsActivated) && <option value="repository">Repositorio</option>}</select></label>
        <label>Enlace (opcional)<input className="field-control mt-1" name="url" type="url" /></label>
        <label>Habilidades demostradas, separadas por comas<input className="field-control mt-1" name="skills" required placeholder="Inventarios, atención al cliente…" /></label>
        <label className="sm:col-span-2">Tu aporte, resultado y cómo comprobarlo<textarea className="field-control mt-1" name="description" required minLength={10} maxLength={2000} placeholder="Describe qué hiciste, el resultado y una referencia que pueda revisarse." /></label>
        <label className="flex items-start gap-2 text-sm sm:col-span-2"><input type="checkbox" name="add_to_profile" />Incorporar también estas habilidades declaradas a mi perfil para calcular compatibilidad.</label>
        <p className="text-xs text-[var(--muted)] sm:col-span-2">Aportar una evidencia no equivale a verificar una habilidad. Retirarla no elimina las habilidades de tu perfil; puedes editarlas en el perfil.</p>
        <button className="button-primary" disabled={busy}>Guardar evidencia</button>
      </form>
      <details className="group rounded-xl border border-[var(--line)]" onToggle={(event) => { if (event.currentTarget.open) setToolsActivated(true); }}>
        <summary className="flex cursor-pointer list-none items-center gap-3 rounded-xl p-4 focus-visible:outline-2 focus-visible:outline-[var(--accent)] [&::-webkit-details-marker]:hidden">
          <Link2 className="h-5 w-5 shrink-0 text-[var(--muted)]" aria-hidden="true" />
          <span className="min-w-0 flex-1">
            <span className="block text-sm font-semibold">{programmingRelevant ? "Conectar GitHub o Codewars" : "Otras fuentes de evidencia"}</span>
            <span className="mt-1 block text-xs text-[var(--muted)]">Opcional · Proyectos y práctica de programación</span>
          </span>
          <ChevronDown className="h-4 w-4 shrink-0 text-[var(--muted)] transition-transform group-open:rotate-180" aria-hidden="true" />
        </summary>
        {toolsActivated && <div className="space-y-3 border-t border-[var(--line)] p-4">
          <p className="text-sm text-[var(--muted)]">Si usas estas plataformas, puedes elegir qué proyectos o retos relacionar con tus habilidades.</p>
          <GitHubEvidence onSaved={async (data) => { setRows(data); await onChanged?.(); }} />
          <CodewarsEvidence onSaved={async (data) => { setRows(data); await onChanged?.(); }} />
        </div>}
      </details>
      {rows.map((row) => <article className="border-t border-[var(--line)] pt-3" key={row.id}>
        <h3 className="font-semibold">{row.title}</h3><p className="text-sm">{row.description}</p>
        <p className="mt-1 text-xs text-[var(--muted)]">{row.skills.join(", ")} · Evidencia declarada{row.add_to_profile ? " · Incorporada al perfil" : ""}</p>
        {row.analysis?.origin === "github_public" && <p className="mt-1 text-xs text-[var(--muted)]">GitHub · revisión {row.analysis.revision.slice(0, 12)} · Tecnologías detectadas mediante análisis estático; autoría sin verificar</p>}
        {row.analysis?.origin === "codewars_public" && <p className="mt-1 text-xs leading-5 text-[var(--muted)]">Codewars · {row.analysis.overall.rank} · {row.analysis.completed_challenges.toLocaleString("es-CO")} retos resueltos · Consulta: {new Date(row.analysis.fetched_at).toLocaleDateString("es-CO")} · Cuenta declarada; titularidad sin verificar</p>}
        <div className="mt-2 flex gap-3">{row.url && <a className="text-sm text-[var(--accent)]" href={row.url} target="_blank" rel="noopener noreferrer">Abrir referencia</a>}
          <button className="text-sm text-[var(--muted)]" disabled={busy} onClick={async () => { if (await confirm({ title: "Retirar esta evidencia", description: "La referencia dejará de aparecer en tu perfil. Tus habilidades declaradas se conservan.", confirmLabel: "Retirar evidencia" })) act(async () => { await api.delete(`/matching/evidence/${row.id}`); setRows(rows.filter((item) => item.id !== row.id)); setMessage("Referencia retirada; tus habilidades del perfil se conservan."); }); }}>Retirar</button>
        </div>
      </article>)}
    </div>
  </details>;
}
