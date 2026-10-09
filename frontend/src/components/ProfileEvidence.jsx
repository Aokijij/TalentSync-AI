import { useEffect, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";

export function ProfileEvidence({ onChanged }) {
  const { confirm } = useFeedback();
  const location = useLocation();
  useEffect(() => { if (location.hash === "#evidencias") document.getElementById("evidencias")?.scrollIntoView({ block: "start" }); }, [location.hash]);
  const [rows, setRows] = useState([]);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
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
        <label>Logro o muestra de trabajo<input className="field-control mt-1" name="title" required minLength={3} maxLength={160} placeholder="Ej.: Mejora del inventario mensual" /></label>
        <label>Tipo<select className="field-control mt-1" name="kind"><option value="experience">Logro laboral</option><option value="portfolio">Portafolio o certificación</option><option value="project">Proyecto</option><option value="repository">Repositorio</option></select></label>
        <label>Enlace (opcional)<input className="field-control mt-1" name="url" type="url" /></label>
        <label>Habilidades demostradas, separadas por comas<input className="field-control mt-1" name="skills" required placeholder="Inventarios, atención al cliente…" /></label>
        <label className="sm:col-span-2">Tu aporte, resultado y cómo comprobarlo<textarea className="field-control mt-1" name="description" required minLength={10} maxLength={2000} placeholder="Describe qué hiciste, el resultado y una referencia que pueda revisarse." /></label>
        <label className="flex items-start gap-2 text-sm sm:col-span-2"><input type="checkbox" name="add_to_profile" />Incorporar también estas habilidades declaradas a mi perfil para calcular compatibilidad.</label>
        <p className="text-xs text-[var(--muted)] sm:col-span-2">Aportar una evidencia no equivale a verificar una habilidad. Retirarla no elimina las habilidades de tu perfil; puedes editarlas en el perfil.</p>
        <button className="button-primary" disabled={busy}>Guardar evidencia</button>
      </form>
      {rows.map((row) => <article className="border-t border-[var(--line)] pt-3" key={row.id}>
        <h3 className="font-semibold">{row.title}</h3><p className="text-sm">{row.description}</p>
        <p className="mt-1 text-xs text-[var(--muted)]">{row.skills.join(", ")} · Evidencia declarada{row.add_to_profile ? " · Incorporada al perfil" : ""}</p>
        <div className="mt-2 flex gap-3">{row.url && <a className="text-sm text-[var(--accent)]" href={row.url} target="_blank" rel="noopener noreferrer">Abrir referencia</a>}
          <button className="text-sm text-[var(--muted)]" disabled={busy} onClick={async () => { if (await confirm({ title: "Retirar esta evidencia", description: "La referencia dejará de aparecer en tu perfil. Tus habilidades declaradas se conservan.", confirmLabel: "Retirar evidencia" })) act(async () => { await api.delete(`/matching/evidence/${row.id}`); setRows(rows.filter((item) => item.id !== row.id)); setMessage("Referencia retirada; tus habilidades del perfil se conservan."); }); }}>Retirar</button>
        </div>
      </article>)}
    </div>
  </details>;
}
