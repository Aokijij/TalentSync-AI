import { ProfileFormFeedback, SectionFieldIssues } from "../components/ProfileFormFeedback.jsx";
import { PrivateProfileDetails } from "../components/PrivateProfileDetails.jsx";
import { profileValidation, profileServerErrors, focusProfileError } from "../utils/profileValidation.js";
import { ProfileIdentity } from "../components/ProfileIdentity.jsx";
import { CertificationFields } from "../components/CertificationFields.jsx";
import { ProfileCredentials } from "../components/ProfileCredentials.jsx";
import { addProfileSkill } from "../utils/skillLevels.js";
import { ProfessionalSummary } from "../components/ProfessionalSummary.jsx";
import { withCustomSummary } from "../utils/professionalSummary.js";
import { SkillLevelsEditor } from "../components/SkillLevelsEditor.jsx";
import { EducationFields } from "../components/EducationFields.jsx";
import { CareerCoachWorkspace } from "../components/CareerCoachWorkspace.jsx";
import { CoachDialog } from "../components/CoachDialog.jsx";
import { ResumeExportDialog } from "../components/ResumeExportDialog.jsx";
import { CvContextReview } from "../components/CvContextReview.jsx";
import { ExperienceFields, MobilityFields } from "../components/ExperienceFields.jsx";
import { Link, useLocation } from "react-router-dom";
import { ProfileEvidence } from "../components/ProfileEvidence.jsx";
import { ProfileLinks } from "../components/ProfileLinks.jsx";
import { profileLinksPayload } from "../utils/profileLinks.js";
import { useEffect, useState } from "react";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import {
  BookOpen,
  CarFront,
  LockKeyhole,
  IdCard,
  BriefcaseBusiness,
  CheckCircle2,
  Download,
  Edit3,
  Link2,
  Plus,
  Save,
  Sparkles,
  Trash2,
  Upload,
  UserRound,
} from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CurrencyInput } from "../components/CurrencyInput.jsx";
import "../styles/profile-page.css";
import { ProfileCompletionRing, getProfileCompletion } from "../components/ProfileCompletionRing.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { getResumePalette } from "../constants/resumePalettes.js";
import { useAuth } from "../hooks/useAuth.js";

const blanks = {
  experiences: {
    role: "",
    company: "",
    start_year: "",
    end_year: "",
    description: "",
  },
  educations: { degree: "", institution: "", start_year: "", end_year: "" },
  certifications: { name: "", issuer: "", year: "" },
};
const availabilityLabels = {
  immediate: "Inmediata",
  two_weeks: "En 15 días",
  one_month: "En 30 días",
  negotiable: "Fecha acordada",
};
const modalityLabels = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
};
const normalize = (data) => ({
  ...data,
  availability: ["Immediate", "Inmediate", "Inmediata"].includes(
    data.availability,
  )
    ? "immediate"
    : data.availability,
  skills: data.skills || [],
  skill_levels: data.skill_levels || {},
  experiences: data.experiences || [],
  educations: data.educations || [],
  certifications: data.certifications || [],
  birth_date: data.birth_date || null,
  driving_licenses: data.driving_licenses || [],
  professional_cards: data.professional_cards || [],
  languages: data.languages || [],
  links: data.links || [],
  resume_export_options: data.resume_export_options || {},
  resume_style: data.resume_style || "classic",
  resume_color: getResumePalette(data.resume_style, data.resume_color).id,
});

export function ProfilePage() {
  const { refreshUser } = useAuth();
  const location = useLocation();
  const [coachOpen, setCoachOpen] = useState(false);

  const [profile, setProfile] = useState(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);
  const [completionOpen, setCompletionOpen] = useState(false);
  const [skill, setSkill] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState({});
  const clearFieldError = (path) => setFieldErrors((current) => Object.fromEntries(Object.entries(current).filter(([key]) => key !== path && !path.startsWith(`${key}.`) && !key.startsWith(`${path}.`))));
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploadingCv, setUploadingCv] = useState(false);
  const [coachTarget, setCoachTarget] = useState("");
  useEffect(() => {
    if (!coachTarget || !editing && !["profile-evidence", "preferencias"].includes(coachTarget)) return;
    const target = document.getElementById(coachTarget);
    const frame = window.requestAnimationFrame(() => {
      if (target) {
        target.scrollIntoView({ block: "center", behavior: "smooth" });
        (target.matches("input,textarea") ? target : target.querySelector(coachTarget === "profile-summary" ? "textarea" : "input,textarea,button"))?.focus({ preventScroll: true });
      }
      setCoachTarget("");
    });
    return () => window.cancelAnimationFrame(frame);
  }, [coachTarget, editing]);
  function editFromCoach(target) {
    setCoachOpen(false);
    if (target === "profile-evidence" && editing) {
      setMessage("Guarda los cambios del perfil antes de gestionar tus evidencias.");
      return;
    }
    setEditing(target !== "profile-evidence");
    setCoachTarget(target);
  }
  useEffect(() => {
    Promise.all([api.get("/profiles/me"), api.get("/auth/me")])
      .then(([profileResponse, accountResponse]) => {
        setProfile(normalize(profileResponse.data));
        setEmail(accountResponse.data.email || "");
        setName(accountResponse.data.name || "Candidato");
      })
      .catch(() => setError("No fue posible cargar el perfil"));
  }, []);
  useEffect(() => {
    if (!profile || !location.hash) return;
    const target = location.hash.slice(1);
    if (["profile-profession", "profile-contact", "profile-summary", "profile-skills", "profile-languages", "profile-certifications", "profile-experiences", "profile-educations", "profile-links", "profile-credentials", "profile-driving-licenses", "profile-professional-cards", "profile-private"].includes(target)) { setEditing(true); setCoachTarget(target); }
    else if (target === "preferencias") { setCoachTarget(target); }
    else if (["evidencias", "profile-evidence"].includes(target)) { setCoachTarget("profile-evidence"); }
  }, [Boolean(profile), location.hash]);
  const update = (key, value) => { clearFieldError(key); setProfile((p) => ({ ...p, [key]: value })); };
  const updateItem = (key, index, field, value) =>
    update(
      key,
      profile[key].map((item, current) =>
        current === index ? { ...item, [field]: value } : item,
      ),
    );
  const addSkill = () => {
    setProfile((current) => addProfileSkill(current, skill));
    setSkill("");
  };
  async function save() {
    setError("");
    const issues = profileValidation(profile, name);
    setFieldErrors(issues);
    if (Object.keys(issues).length) { requestAnimationFrame(() => focusProfileError(issues)); return null; }
    try {
      const { data } = await api.put("/profiles/me", { ...profile, name, links: profileLinksPayload(profile.links), mobility: { ...profile.mobility, commuting_cities: (profile.mobility?.commuting_cities || []).map((value) => value.trim()).filter(Boolean) } }, { __quiet: true });
      setProfile(normalize(data));
      await refreshUser();
      setEditing(false);
      setMessage("Hoja de vida actualizada correctamente");
      return data;
    } catch (requestError) {
      const issues = profileServerErrors(requestError);
      if (Object.keys(issues).length) { setFieldErrors(issues); requestAnimationFrame(() => focusProfileError(issues)); return null; }
      setError(requestError instanceof Error && !requestError.isAxiosError ? requestError.message : getApiErrorMessage(requestError, "No fue posible actualizar la hoja de vida"));
      return null;
    }
  }
  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file || uploadingCv) return;
    const form = new FormData();
    form.append("file", file);
    setUploadingCv(true);
    setError("");
    setMessage("Analizando PDF y preparando recomendaciones para tu hoja de vida...");
    try {
      const { data } = await api.post("/profiles/me/cv", form, { timeout: 190000 });
      setProfile(normalize(data));
      setEditing(true);
      setMessage(
        `CV analizado: ${data.experiences?.length ?? 0} experiencias, ${data.educations?.length ?? 0} estudios y ${data.skills?.length ?? 0} habilidades. La extracción se ha guardado. Revisa y corrige los campos detectados.`,
      );
    } catch (e) {
      setError(e.response?.data?.detail || "No fue posible procesar el PDF");
    } finally {
      setUploadingCv(false);
      event.target.value = "";
    }
  }
  async function uploadPhoto(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setError("");
    try {
      const { data } = await api.post("/profiles/me/photo", form);
      setProfile((current) => ({ ...current, photo_url: data.photo_url }));
      setPhotoVersion((current) => current + 1);
      setEditing(true);
      setMessage("Foto agregada. Guarda el perfil para conservar los demás cambios.");
      return true;
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "No fue posible guardar la foto");
      return false;
    }
  }
  if (!profile)
    return (
      <section className="surface-card p-6" aria-live="polite">
        <h1 className="font-bold text-[var(--ink-strong)]">Mi perfil profesional</h1>
        <p className="mt-3 text-sm text-[var(--muted)]" role={error ? "alert" : "status"}>{error || "Cargando tu hoja de vida…"}</p>
        {error && <button type="button" className="button-secondary mt-4" onClick={() => window.location.reload()}>Volver a cargar</button>}
      </section>
    );
  return (
    <ProfileFormFeedback errors={fieldErrors} clearError={clearFieldError}><div className={`profile-page space-y-6 ${editing ? "profile-is-editing" : ""}`}>
      <header className="profile-page-heading">
        <div><h1>Mi perfil</h1></div>
        <div className="profile-heading-actions"><button type="button" className="profile-coach-launch" aria-haspopup="dialog" onClick={() => setCoachOpen(true)}><span><Sparkles size={22} /></span><span><strong>Ideas para mejorar tu hoja de vida</strong><small>Tu ayuda de redacción, a un clic</small></span></button><span className="profile-mode"><span />{editing ? "Editando tu perfil" : "Tu perfil guardado"}</span></div>
      </header>
      <section className="profile-toolbar print-hidden">
        <ProfileCompletionRing profile={profile} variant="summary" onReview={() => setCompletionOpen(true)} />
          <div className="profile-toolbar-actions">
            <label className="button-secondary cursor-pointer hover-lift pressed focus-ring" role="button" tabIndex={uploadingCv ? -1 : 0} aria-disabled={uploadingCv} onKeyDown={(event) => { if (!uploadingCv && ["Enter", " "].includes(event.key)) { event.preventDefault(); event.currentTarget.querySelector("input").click(); } }}>
              <Upload size={16} />
              {uploadingCv ? "Analizando CV…" : "Subir CV"}
              <input
                className="hidden"
                type="file"
                accept="application/pdf"
                disabled={uploadingCv}
                onChange={upload}
              />
            </label>
            <button
              className="button-secondary"
              type="button"
              onClick={() => setExportOpen(true)}
            >
              <Download size={16} />
              Diseñar y exportar
            </button>
            <button
              className="profile-edit-action focus-ring"
              type="button"
              disabled={uploadingCv}
              onClick={() =>
                editing ? save() : setEditing(true)
              }
            >
              {editing ? <Save size={16} /> : <Edit3 size={16} />}
              {editing ? "Guardar cambios" : "Editar perfil"}
            </button>
          </div>
      </section>
      {(message || error) && (
        <p
          className={`rounded-[var(--radius-lg)] border px-4 py-3 text-sm ${error ? "border-[var(--error)] bg-[var(--error)]/10 text-[var(--error)]" : "border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"}`}
        >
          {error || message}
        </p>
      )}
      <ProfileIdentity profile={profile} name={name} email={email} editing={editing} onNameChange={setName} onChange={(patch) => setProfile((current) => ({ ...current, ...patch }))} />
      <Section id="profile-private" icon={LockKeyhole} title="Datos personales privados"><PrivateProfileDetails birthDate={profile.birth_date} editing={editing} onChange={(birth_date) => update("birth_date", birth_date)} /></Section>
      <ResumeExportDialog open={exportOpen} onClose={() => setExportOpen(false)} profile={profile} name={name} photoVersion={photoVersion} onPhoto={uploadPhoto} onDesignSaved={(design) => setProfile((current) => ({ ...current, ...design }))} onEdit={() => editFromCoach("profile-experiences")} />
      <CoachDialog open={completionOpen} onClose={() => setCompletionOpen(false)} title="Qué puedes completar en tu perfil" className="profile-completion-dialog"><div className="profile-completion-body"><p>Este indicador revisa información incluida; no mide tu compatibilidad. Completa solo lo que corresponda a tu trayectoria.</p>{getProfileCompletion(profile).missing.length ? <ul>{getProfileCompletion(profile).missing.map((label) => <li key={label}><span><Plus size={16} />{label}</span><button type="button" onClick={() => { setCompletionOpen(false); const target = { "Título profesional": "profile-profession", "Teléfono, ciudad y departamento": "profile-contact", "6 habilidades específicas": "profile-skills", "Resumen profesional de 120 caracteres": "profile-summary", "2 experiencias completas": "profile-experiences", "Formación académica completa": "profile-educations", "Curso o certificación": "profile-certifications", "Idioma con nivel": "profile-languages", "Preferencias laborales completas": "preferencias" }[label]; if (target) editFromCoach(target); else document.querySelector('.profile-toolbar input[type="file"]')?.click(); }}>Completar <span aria-hidden="true">→</span></button></li>)}</ul> : <div className="profile-completion-success"><CheckCircle2 size={28} /><strong>Tienes información en los diez apartados</strong><p>Mantenla actualizada y revisa que refleje tu experiencia real.</p></div>}</div></CoachDialog>
      <CoachDialog open={coachOpen} onClose={() => setCoachOpen(false)}>
        <Link className="profile-radar-link" to="/aprendizaje#radar-laboral">Explorar mi radar laboral →</Link>
        <CareerCoachWorkspace active={coachOpen} profile={profile} editing={editing} onEdit={editFromCoach} onSave={save} onProfileChanged={async () => { setProfile(normalize((await api.get("/profiles/me")).data)); await refreshUser(); }} />
      </CoachDialog>
      {(
        <article className="profile-document">
          <div className="profile-content-grid">
            <div className="profile-main-sections">
            <Section id="profile-summary" icon={UserRound} title="Resumen profesional">
              <ProfessionalSummary profile={profile} editing={editing} onChange={(text) => setProfile((current) => withCustomSummary(current, text))} onEdit={() => { setProfile((current) => withCustomSummary(current, current.experience || "")); editFromCoach("profile-summary"); }} />
            </Section>
            <Section id="profile-experiences" icon={BriefcaseBusiness} title="Experiencia laboral">
              <Items
                type="experiences"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            <Section id="profile-educations" icon={BookOpen} title="Formación académica">
              <Items
                type="educations"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            {[["drivingLicenses", "profile-driving-licenses", "Licencias de conducción", CarFront], ["professionalCards", "profile-professional-cards", "Tarjetas profesionales", IdCard]].map(([kind, id, title, Icon]) => <Section key={kind} id={id} icon={Icon} title={title}><ProfileCredentials kind={kind} drivingLicenses={profile.driving_licenses} professionalCards={profile.professional_cards} editing={editing} onChange={({ drivingLicenses, professionalCards }) => { clearFieldError(kind === "drivingLicenses" ? "driving_licenses" : "professional_cards"); setProfile((current) => ({ ...current, driving_licenses: drivingLicenses, professional_cards: professionalCards })); }} /></Section>)}
            </div>
            <aside className="profile-side-sections">
            <Section id="profile-links" icon={Link2} title="Enlaces profesionales"><ProfileLinks value={profile.links} editing={editing} onChange={(value) => update("links", value)} onEdit={() => editFromCoach("profile-links")} /></Section>
            <Section id="profile-certifications" icon={CheckCircle2} title="Cursos y certificaciones">
              <Items
                type="certifications"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            <Section id="profile-languages" icon={BookOpen} title="Idiomas"><LanguagesEditor value={profile.languages} editing={editing} onChange={(value) => update("languages", value)} /></Section>
            <Section id="profile-skills" icon={BriefcaseBusiness} title="Habilidades">
              <p className="mb-3 text-xs text-[var(--muted)]">Indica tu dominio actual de cada habilidad. Es una declaración de tu perfil; no una acreditación. Los niveles no se deducen de los años de experiencia.</p>
              <CvContextReview rows={profile.cv_skill_context} skills={profile.skills} decisions={profile.cv_mention_decisions} disabled={editing} onDecision={async (skill, action) => { const { data } = await api.patch("/profiles/me/cv-mentions", { skill, action }); setProfile(normalize(data)); await refreshUser(); }} />
              <SkillLevelsEditor skills={profile.skills} levels={profile.skill_levels} sources={profile.skill_level_sources} editing={editing} onChange={(levels) => update("skill_levels", levels)} onRemove={(item) => update("skills", profile.skills.filter((value) => value !== item))} />
              {editing && (
                <div className="mt-4 flex gap-2">
                  <input
                    className="field-control input-md"
                    value={skill}
                    onChange={(e) => setSkill(e.target.value)}
                    onKeyDown={(e) =>
                      e.key === "Enter" && (e.preventDefault(), addSkill())
                    }
                    placeholder="Ej. comunicación"
                  />
                  <button
                    className="button-secondary w-auto hover-lift pressed focus-ring"
                    type="button"
                    onClick={addSkill}
                  >
                    <Plus size={16} />
                    Agregar
                  </button>
                </div>
              )}
            </Section>
            <div id="preferencias" className="scroll-mt-44"><Section icon={BriefcaseBusiness} title="Preferencias laborales">
              {editing ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  <label className="text-sm font-semibold text-[var(--muted)]">
                    Sector profesional
                    <select
                      className="field-control mt-1"
                      value={profile.preferred_sector || ""}
                      onChange={(event) =>
                        update("preferred_sector", event.target.value)
                      }
                    >
                      <option value="">Seleccionar</option>
                      {JOB_SECTORS.map((sector) => (
                        <option key={sector} value={sector}>
                          {sector}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-sm font-semibold text-[var(--muted)]">
                    Disponibilidad
                    <select
                      className="field-control mt-1"
                      value={profile.availability || ""}
                      onChange={(event) =>
                        update("availability", event.target.value)
                      }
                    >
                      <option value="">Seleccionar</option>
                      {Object.entries(availabilityLabels).map(
                        ([value, label]) => (
                          <option key={value} value={value}>
                            {label}
                          </option>
                        ),
                      )}
                    </select>
                  </label>
                  <label className="text-sm font-semibold text-[var(--muted)]">
                    Modalidad
                    <select
                      className="field-control mt-1"
                      value={profile.preferred_modality || ""}
                      onChange={(event) =>
                        update("preferred_modality", event.target.value)
                      }
                    >
                      <option value="">Seleccionar</option>
                      <option value="remote">Remoto</option>
                      <option value="hybrid">Híbrido</option>
                      <option value="onsite">Presencial</option>
                    </select>
                  </label>
                  <label className="text-sm font-semibold text-[var(--muted)]">
                    Aspiración salarial
                    <CurrencyInput
                      className="field-control mt-1"
                      value={profile.desired_salary || ""}
                      onChange={(value) => update("desired_salary", value)}
                      placeholder="4.500.000"
                    />
                  </label>
                </div>
              ) : (
                <div className="grid gap-3 text-sm sm:grid-cols-2">
                  <p>
                    <span className="block text-xs font-bold uppercase text-[var(--muted)]">
                      Sector profesional
                    </span>
                    {profile.preferred_sector || "Sin definir"}
                  </p>
                  <p>
                    <span className="block text-xs font-bold uppercase text-[var(--muted)]">
                      Disponibilidad
                    </span>
                    {availabilityLabels[profile.availability] ||
                      profile.availability ||
                      "Sin definir"}
                  </p>
                  <p>
                    <span className="block text-xs font-bold uppercase text-[var(--muted)]">
                      Modalidad
                    </span>
                    {modalityLabels[profile.preferred_modality] || "Sin definir"}
                  </p>
                  <p>
                    <span className="block text-xs font-bold uppercase text-[var(--muted)]">
                      Aspiración
                    </span>
                    {profile.desired_salary
                      ? `$${Number(profile.desired_salary).toLocaleString("es-CO")} COP`
                      : "Sin definir"}
                  </p>
                </div>
              )}
            <MobilityFields value={profile.mobility || {}} editing={editing} onChange={(value) => update("mobility", value)} /></Section></div>
            </aside>
      </div>
        </article>
      )}
      {editing && <p className="surface-card p-5 text-sm text-[var(--muted)]">Guarda tus cambios para gestionar las evidencias de tu perfil.</p>}
      {!editing && <div id="profile-evidence"><ProfileEvidence profile={profile} onChanged={async () => setProfile(normalize((await api.get("/profiles/me")).data))} /></div>}
    </div></ProfileFormFeedback>
  );
}
function Section({ id, icon: Icon, title, children }) {
  return (
    <section id={id} className="profile-section">
      <h2 className="profile-section-heading">
        <span className="profile-section-icon"><Icon size={18} /></span>
        {title}
      </h2>
      <div className="profile-section-body space-y-3">{children}{({ "profile-experiences": "experiences", "profile-educations": "educations", "profile-languages": "languages", "profile-skills": "skill_levels", preferencias: "mobility" })[id] && <SectionFieldIssues prefix={({ "profile-experiences": "experiences", "profile-educations": "educations", "profile-languages": "languages", "profile-skills": "skill_levels", preferencias: "mobility" })[id]} />}</div>
    </section>
  );
}
function Items({ type, profile, editing, update, updateItem }) {
  if (type === "certifications") return <CertificationFields items={profile.certifications} editing={editing} onChange={(items) => update("certifications", items)} />;
  if (type === "educations") return <EducationFields items={profile.educations} editing={editing} onChange={(items) => update("educations", items)} />;
  if (type === "experiences") return <ExperienceFields items={profile.experiences} editing={editing} onChange={(items) => update("experiences", items)} />;
  const fields =
    type === "experiences"
      ? ["role", "company", "start_year", "end_year", "description"]
      : type === "educations"
        ? ["degree", "institution", "start_year", "end_year"]
        : ["name", "issuer", "year", "url"];
  const placeholders = {
    role: "Cargo desempeñado",
    company: "Empresa",
    start_year: "Año de inicio",
    end_year: "Año de finalización",
    description: "Descripción de responsabilidades",
    degree: "Título o carrera",
    institution: "Institución educativa",
    name: "Nombre de certificación",
    issuer: "Entidad emisora",
    year: "Año de obtención",
    url: "Enlace del certificado (https://…)",
  };
  const labels = {
    role: "Cargo",
    company: "Empresa",
    start_year: "Inicio",
    end_year: "Finalización",
    description: "Responsabilidades",
    degree: "Título o carrera",
    institution: "Institución",
    name: "Certificación",
    issuer: "Entidad emisora",
    year: "Año de obtención",
    url: "Enlace del certificado (https://…)",
  };
  const text =
    type === "experiences"
      ? "experiencia"
      : type === "educations"
        ? "estudio"
        : "certificación";

  return (
    <>
      {profile[type].map((item, index) => (
        <div
          key={index}
          className="profile-certification-entry"
        >
          {editing ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {fields.map((field) =>
                field === "description" ? (
                  <label key={field} className="text-xs font-semibold text-[var(--muted)] sm:col-span-2">{labels[field]}<textarea className="field-control input-md mt-1 min-h-24" placeholder={placeholders[field]} value={item[field] || ""} onChange={(event) => updateItem(type, index, field, event.target.value)} /></label>
                ) : (
                  <label key={field} className="text-xs font-semibold text-[var(--muted)]">{labels[field]}<input type={field === "url" ? "url" : "text"} maxLength={field === "url" ? 2000 : 255} className="field-control input-md mt-1" placeholder={placeholders[field]} value={item[field] || ""} onChange={(event) => updateItem(type, index, field, event.target.value)} /></label>
                ),
              )}
            </div>
          ) : (
            <>
              <div className="space-y-2">
                <p className="font-bold text-[var(--ink)]">
                  {item.role || item.degree || item.name}
                </p>
                <p className="text-sm font-semibold text-[var(--success)]">
                  {item.company || item.institution || item.issuer} ·{" "}
                  {item.start_year || item.year || ""}
                  {item.end_year && ` - ${item.end_year}`}
                </p>
                {type === "certifications" && item.url?.startsWith("https://") && <a className="inline-flex text-xs font-semibold text-[var(--accent)]" href={item.url} target="_blank" rel="noopener noreferrer">Ver certificado del proveedor ↗</a>}
                {type === "certifications" && item.source === "external_certificate" && <p className="text-xs text-[var(--muted)]">Certificado aportado por el candidato</p>}
                {item.description && (
                  <p className="text-sm text-[var(--muted)]">
                    {item.description}
                  </p>
                )}
              </div>
            </>
          )}
          {editing && (
            <button
              className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[var(--error)]"
              type="button"
              onClick={() =>
                update(
                  type,
                  profile[type].filter((_, current) => current !== index),
                )
              }
            >
              <Trash2 size={14} />
              Eliminar
            </button>
          )}
        </div>
      ))}
      {editing && (
        <button
          className="button-secondary w-auto hover-lift pressed focus-ring"
          type="button"
          onClick={() => update(type, [...profile[type], blanks[type]])}
        >
          <Plus size={16} />
          Agregar {text}
        </button>
      )}
      {!profile[type].length && (
        <p className="text-sm text-[var(--muted)]">
          Sin registros todavía.
          {type === "experiences" && (
            <span> Subir un CV para extraer experiencia laboral.</span>
          )}
          {type === "educations" && (
            <span> Subir un CV para extraer formación académica.</span>
          )}
          {type === "certifications" && (
            <span> Subir un CV para extraer certificaciones.</span>
          )}
        </p>
      )}
    </>
  );
}
