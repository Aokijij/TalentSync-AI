import { useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Award, BriefcaseBusiness, Check, ChevronDown, Code2, ExternalLink, FileBadge, FolderOpen, Info, Link2, Plus, Save, Trash2, X } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { GitHubEvidence } from "./GitHubEvidence.jsx";
import { CodewarsEvidence } from "./CodewarsEvidence.jsx";
import { programmingEvidenceRelevant } from "../utils/evidenceContext.js";
import "../styles/profile-evidence.css";

const kinds = {
  experience: { label: "Logro laboral", Icon: BriefcaseBusiness },
  portfolio: { label: "Portafolio", Icon: FolderOpen },
  certificate: { label: "Certificado externo", Icon: Award },
  project: { label: "Proyecto", Icon: FolderOpen },
  repository: { label: "Repositorio", Icon: Code2 },
};

function EvidenceCard({ row, busy, onRemove, onAddSkills }) {
  const { label, Icon } = kinds[row.kind] || kinds.experience;
  const skills = row.skills || [];
  const github = row.analysis?.origin === "github_public";
  const codewars = row.analysis?.origin === "codewars_public";
  return <article className="evidence-card">
    <div className="evidence-card-heading">
      <span className="evidence-icon"><Icon size={19} aria-hidden="true" /></span>
      <span className="evidence-kind">{label}</span>
      <span className="evidence-status">{row.kind === "certificate" ? "Aportado" : "Declarada"}</span>
    </div>
    <h4>{row.title}</h4>
    {row.kind === "certificate" && (row.issuer || row.year) && <p className="evidence-field-help">{[row.issuer, row.year].filter(Boolean).join(" · ")}{row.certificate_id && ` · Credencial ${row.certificate_id}`}</p>}
    <p className="evidence-description">{row.description}</p>
    <div className="evidence-skills" aria-label="Habilidades relacionadas">
      {skills.slice(0, 4).map((skill) => <span key={skill}>{skill}</span>)}
      {skills.length > 4 && <details className="evidence-extra-skills"><summary>+{skills.length - 4} más</summary><div>{skills.slice(4).map((skill) => <span key={skill}>{skill}</span>)}</div></details>}
    </div>
    {row.add_to_profile && <p className="evidence-profile-note"><Check size={14} aria-hidden="true" />Habilidades añadidas a tu perfil</p>}
    <details className="evidence-card-detail">
      <summary>Detalles de la evidencia<ChevronDown size={14} aria-hidden="true" /></summary>
      <div>
        <p className="whitespace-pre-wrap">{row.description}</p>
        {github && <p>GitHub · revisión {row.analysis.revision?.slice(0, 12)}. Tecnologías detectadas mediante análisis estático; autoría sin verificar.</p>}
        {codewars && <p>Codewars · {row.analysis.overall?.rank} · {row.analysis.completed_challenges?.toLocaleString("es-CO")} retos resueltos · Consulta: {new Date(row.analysis.fetched_at).toLocaleDateString("es-CO")}. Cuenta declarada; titularidad sin verificar.</p>}
        <p>Esta referencia fue aportada por ti. No equivale a una habilidad verificada.</p>
      </div>
    </details>
    {!row.add_to_profile && skills.length > 0 && <button type="button" className="evidence-skills-action" disabled={busy} onClick={() => onAddSkills(row)}><span className="evidence-skills-action-icon"><Plus size={17} aria-hidden="true" /></span><span>{row.kind === "certificate" ? "Añadir certificado al perfil" : "Añadir habilidades"}<span>Incorporar el contenido como declarado por mí</span></span></button>}
    <footer className="evidence-card-actions">
      {row.url ? <a className="button-secondary button-sm" href={row.url} target="_blank" rel="noopener noreferrer">{row.kind === "certificate" ? "Ver certificado" : "Abrir referencia"}<ExternalLink size={14} aria-hidden="true" /></a> : <span className="evidence-no-link">Sin enlace adjunto</span>}
      <button type="button" className="evidence-remove" disabled={busy} onClick={() => onRemove(row)} aria-label={`Retirar evidencia: ${row.title}`}><Trash2 size={15} aria-hidden="true" />Retirar</button>
    </footer>
  </article>;
}

export function ProfileEvidence({ profile, onChanged }) {
  const { confirm } = useFeedback();
  const location = useLocation();
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [kind, setKind] = useState("experience");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [toolsActivated, setToolsActivated] = useState(false);
  const titleInput = useRef(null);
  const addButton = useRef(null);
  const formFocusPending = useRef(false);
  const programmingRelevant = programmingEvidenceRelevant(profile, rows);

  useEffect(() => { if (location.hash === "#evidencias") document.getElementById("evidencias")?.scrollIntoView({ block: "start" }); }, [location.hash]);
  useEffect(() => {
    if (showForm) titleInput.current?.focus();
    else if (!busy && formFocusPending.current) { addButton.current?.focus(); formFocusPending.current = false; }
  }, [showForm, busy]);
  useEffect(() => {
    api.get("/matching/evidence").then(({ data }) => setRows(data))
      .catch((failure) => setError(getApiErrorMessage(failure))).finally(() => setLoading(false));
  }, []);

  function closeForm() { formFocusPending.current = true; setShowForm(false); }
  async function act(action) {
    setBusy(true); setError(""); setMessage("");
    try { await action(); } catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
  }
  async function remove(row) {
    if (await confirm({ title: "Retirar esta evidencia", description: "La referencia dejará de aparecer en tu perfil. Tus habilidades declaradas se conservan.", confirmLabel: "Retirar evidencia" })) {
      act(async () => {
        await api.delete(`/matching/evidence/${row.id}`);
        setRows((current) => current.filter((item) => item.id !== row.id));
        setMessage("Referencia retirada; tus habilidades del perfil se conservan.");
      });
    }
  }
  async function save(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const data = new FormData(form);
    await act(async () => {
      const response = await api.post("/matching/evidence", {
        issuer: data.get("issuer") || "", year: data.get("year") || "", title: data.get("title"), kind: data.get("kind"), url: data.get("url") || null,
        skills: data.get("skills").split(",").map((skill) => skill.trim()).filter(Boolean),
        description: data.get("description"), add_to_profile: data.has("add_to_profile"),
      });
      setRows(response.data); form.reset(); setKind("experience"); closeForm();
      setMessage(data.has("add_to_profile") ? "Evidencia guardada y contenido añadido a tu perfil." : "Evidencia guardada y vinculada a tus habilidades.");
      await onChanged?.();
    });
  }

  return <details className="surface-card profile-evidence" id="evidencias" open={location.hash === "#evidencias" ? true : undefined}>
    <summary className="evidence-section-heading">
      <span className="evidence-icon evidence-icon-main"><FileBadge size={22} aria-hidden="true" /></span>
      <span className="evidence-heading-copy"><strong>Evidencias de mi experiencia</strong><span>Lo que has hecho también habla de ti</span></span>
      <span className="evidence-count">{loading ? "…" : rows.length}</span>
      <ChevronDown className="evidence-section-chevron" size={18} aria-hidden="true" />
    </summary>
    <div className="evidence-section-body">
      <p className="evidence-intro">Respalda tus habilidades con logros, trabajos y certificados. Las empresas de tus procesos podrán consultarlos con tu permiso.</p>
      {error && <p role="alert" className="evidence-feedback evidence-feedback-error">{error}</p>}
      {message && <p role="status" className="evidence-feedback"><Check size={17} aria-hidden="true" /><span>{message} <Link to="/recomendaciones">Ver recomendaciones<ExternalLink size={13} aria-hidden="true" /></Link></span></p>}
      <div className="evidence-toolbar">
        <div><h3>Tus evidencias</h3><p>Una muestra concreta de tu experiencia y aprendizaje.</p></div>
        <button ref={addButton} type="button" className="button-primary button-sm" aria-expanded={showForm} aria-controls="evidence-create-form" disabled={busy || showForm} onClick={() => setShowForm(true)}><Plus size={17} aria-hidden="true" />Añadir evidencia</button>
      </div>
      <section className="evidence-form-panel" hidden={!showForm} id="evidence-create-form" aria-labelledby="evidence-create-title">
        <header><div><h4 id="evidence-create-title">Nueva evidencia</h4><p>Cuenta qué hiciste y cómo se puede comprobar.</p></div><button type="button" className="evidence-close" disabled={busy} onClick={closeForm} aria-label="Cerrar formulario de nueva evidencia"><X size={18} /></button></header>
        <form onSubmit={save}>
          <fieldset disabled={busy} className="evidence-form-fields">
            <label>Título<input ref={titleInput} className="field-control mt-2" name="title" required minLength={3} maxLength={160} placeholder="Ej.: Mejoré el control de inventarios" /></label>
            <label>Tipo de evidencia<select className="field-control mt-2" name="kind" value={kind} onChange={(event) => setKind(event.target.value)}><option value="experience">Logro laboral</option><option value="portfolio">Portafolio</option><option value="certificate">Certificado externo</option><option value="project">Proyecto</option>{(programmingRelevant || toolsActivated) && <option value="repository">Repositorio</option>}</select></label>
            {kind === "certificate" && <><label>Entidad emisora (para certificados)<input className="field-control mt-2" name="issuer" maxLength={160} placeholder="Ej.: SENA, universidad o proveedor" /></label><label>Año del certificado<input className="field-control mt-2" name="year" inputMode="numeric" pattern="[0-9]{4}" maxLength={4} placeholder="2026" /></label></>}
            <label className="evidence-field-wide">Tu aporte y resultado<textarea className="field-control mt-2" name="description" rows={3} required minLength={10} maxLength={2000} placeholder="Qué hiciste, qué cambió gracias a tu trabajo y cómo podría revisarse." /></label>
            <label>Habilidades relacionadas<input className="field-control mt-2" name="skills" required placeholder="Inventarios, organización, atención al cliente…" /><span className="evidence-field-help">Separa cada habilidad con una coma.</span></label>
            <label>Enlace de respaldo <span className="evidence-optional">Opcional</span><input className="field-control mt-2" name="url" type="url" placeholder="https://…" /><span className="evidence-field-help">El archivo permanece en su plataforma de origen.</span></label>
            <label className="evidence-add-skills evidence-field-wide"><input type="checkbox" name="add_to_profile" /><span><strong>{kind === "certificate" ? "Añadir certificado y habilidades a mi perfil" : "Añadir estas habilidades a mi perfil"}</strong><span>{kind === "certificate" ? "Aparecerá en Cursos y certificaciones con su enlace. Las habilidades se añaden como declaradas." : "Se incorporarán como habilidades declaradas para calcular tu compatibilidad."}</span></span></label>
          </fieldset>
          <footer className="evidence-form-actions"><p><Info size={15} aria-hidden="true" />Aportar una evidencia no verifica automáticamente una habilidad.</p><div><button type="button" className="button-secondary button-sm" disabled={busy} onClick={closeForm}>Cancelar</button><button className="button-primary button-sm" disabled={busy}><Save size={16} aria-hidden="true" />{busy ? "Guardando…" : "Guardar evidencia"}</button></div></footer>
        </form>
      </section>
      {loading ? <p role="status" className="evidence-empty">Cargando tus evidencias…</p> : rows.length ? <div className="evidence-grid">{rows.map((row) => <EvidenceCard key={row.id} row={row} busy={busy} onRemove={remove} onAddSkills={(row) => act(async () => { const { data } = await api.post(`/matching/evidence/${row.id}/skills`); setRows(data); await onChanged?.(); setMessage("Habilidades incorporadas como declaradas por ti."); })} />)}</div> : !error && <div className="evidence-empty"><span className="evidence-icon"><FolderOpen size={24} aria-hidden="true" /></span><h4>Tu experiencia merece verse</h4><p>Empieza con un logro laboral, una muestra de trabajo o un certificado. Puede ser de cualquier profesión.</p></div>}
      <details className="evidence-integrations" onToggle={(event) => { if (event.currentTarget.open) setToolsActivated(true); }}>
        <summary><Link2 size={18} aria-hidden="true" /><span><strong>{programmingRelevant ? "Conectar GitHub o Codewars" : "Otras fuentes de evidencia"}</strong><span>Opcional · Proyectos y práctica de programación</span></span><ChevronDown size={16} aria-hidden="true" /></summary>
        {toolsActivated && <div className="evidence-integration-content"><p>Elige qué proyectos o retos relacionar con tus habilidades.</p><GitHubEvidence onSaved={async (data) => { setRows(data); await onChanged?.(); }} /><CodewarsEvidence onSaved={async (data) => { setRows(data); await onChanged?.(); }} /></div>}
      </details>
    </div>
  </details>;
}
