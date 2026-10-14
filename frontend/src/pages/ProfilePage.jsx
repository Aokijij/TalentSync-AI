import { EducationFields } from "../components/EducationFields.jsx";
import { CareerCoachWorkspace } from "../components/CareerCoachWorkspace.jsx";
import { CvContextReview } from "../components/CvContextReview.jsx";
import { isOngoing } from "../utils/profileStatus.js";
import { experiencePeriod } from "../utils/experienceDates.js";
import { ExperienceFields, MobilityFields } from "../components/ExperienceFields.jsx";
import { useLocation } from "react-router-dom";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { ProfileEvidence } from "../components/ProfileEvidence.jsx";
import { useEffect, useState } from "react";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { languageLevelLabel } from "../constants/languages.js";
import {
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  Download,
  Edit3,
  Eye,
  ImagePlus,
  Mail,
  MapPin,
  Phone,
  Plus,
  Palette,
  Save,
  Trash2,
  Upload,
  UserRound,
} from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { AuthenticatedImage } from "../components/AuthenticatedImage.jsx";
import { CurrencyInput } from "../components/CurrencyInput.jsx";
import "../styles/profile-page.css";
import { ProfileCompletionRing, getProfileCompletion } from "../components/ProfileCompletionRing.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import { getResumePalette, getResumePalettes } from "../constants/resumePalettes.js";
import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
} from "../constants/colombianCities.js";
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
  experiences: data.experiences || [],
  educations: data.educations || [],
  certifications: data.certifications || [],
  languages: data.languages || [],
  resume_style: data.resume_style || "classic",
  resume_color: getResumePalette(data.resume_style, data.resume_color).id,
});

export function ProfilePage() {
  const { refreshUser } = useAuth();
  const location = useLocation();
  const { confirm } = useFeedback();
  const [profile, setProfile] = useState(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [skill, setSkill] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [photoVersion, setPhotoVersion] = useState(0);
  const [uploadingCv, setUploadingCv] = useState(false);
  const [coachTarget, setCoachTarget] = useState("");
  const [coachLaunch] = useState(() => {
    const params = new URLSearchParams(location.search);
    return params.get("coach") === "vacancy" ? { tab: "vacancy", jobId: params.get("job") } : null;
  });
  useEffect(() => {
    if (!coachTarget || !editing && coachTarget !== "profile-evidence") return;
    const target = document.getElementById(coachTarget);
    if (target) {
      target.scrollIntoView({ block: "center", behavior: "smooth" });
      (target.matches("input,textarea") ? target : target.querySelector("input,textarea,button"))?.focus({ preventScroll: true });
    }
    setCoachTarget("");
  }, [coachTarget, editing]);
  function editFromCoach(target) {
    if (target === "profile-evidence" && editing) {
      setMessage("Guarda los cambios del perfil antes de gestionar tus evidencias.");
      return;
    }
    setPreviewMode(false);
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
  useEffect(() => { if (profile && location.hash === "#preferencias") document.getElementById("preferencias")?.scrollIntoView({ block: "start" }); }, [Boolean(profile), location.hash]);
  const update = (key, value) => setProfile((p) => ({ ...p, [key]: value }));
  const updateItem = (key, index, field, value) =>
    update(
      key,
      profile[key].map((item, current) =>
        current === index ? { ...item, [field]: value } : item,
      ),
    );
  const addSkill = () => {
    const value = skill.trim();
    if (
      value &&
      !profile.skills.some((item) => item.toLowerCase() === value.toLowerCase())
    )
      update("skills", [...profile.skills, value]);
    setSkill("");
  };
  async function save() {
    setError("");
    try {
      const { data } = await api.put("/profiles/me", { ...profile, name, mobility: { ...profile.mobility, commuting_cities: (profile.mobility?.commuting_cities || []).map((value) => value.trim()).filter(Boolean) } });
      setProfile(normalize(data));
      await refreshUser();
      setEditing(false);
      setMessage("Hoja de vida actualizada correctamente");
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible actualizar la hoja de vida"));
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
      setProfile(normalize(data));
      setPhotoVersion((current) => current + 1);
      setEditing(true);
      setMessage("Foto agregada. Guarda el perfil para conservar los demás cambios.");
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "No fue posible guardar la foto");
    }
  }
  async function exportPdf() {
    setError("");
    try {
      // Export the visible draft, including the selected style and palette.
      if (editing) {
        if (!await confirm({ title: "Guardar y exportar", description: "Se guardarán los cambios que ves, incluidos el estilo y el color, antes de generar el PDF.", confirmLabel: "Guardar y descargar" })) return;
        const { data } = await api.put("/profiles/me", { ...profile, name, mobility: { ...profile.mobility, commuting_cities: (profile.mobility?.commuting_cities || []).map((value) => value.trim()).filter(Boolean) } });
        setProfile(normalize(data)); setEditing(false); await refreshUser();
      }
      const { data } = await api.get("/profiles/me/export", { responseType: "blob" });
      const url = URL.createObjectURL(data), anchor = document.createElement("a");
      anchor.href = url; anchor.download = `${String(name || "Candidato").replace(/[\\/:*?"<>|]/g, " ")} - HV.pdf`;
      document.body.append(anchor); anchor.click(); anchor.remove();
      setTimeout(() => URL.revokeObjectURL(url), 30000);
      setMessage("PDF generado. Revisa las descargas de tu navegador.");
      window.dispatchEvent(new CustomEvent("talentsync:feedback", { detail: { message: "PDF generado. Revisa las descargas de tu navegador." } }));
    } catch (failure) { setError(getApiErrorMessage(failure, "No se pudo generar el PDF")); }
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
    <div className={`profile-page space-y-6 ${editing ? "profile-is-editing" : ""}`}>
      <header className="profile-page-heading">
        <div><p className="profile-eyebrow">TU TRAYECTORIA, TU PRÓXIMO PASO</p><h1>Mi perfil profesional</h1><p>Presenta lo que sabes y encuentra cómo seguir avanzando.</p></div>
        <span className="profile-mode"><span />{previewMode ? "Vista del documento" : editing ? "Editando tu perfil" : "Tu perfil guardado"}</span>
      </header>
      <section className="profile-toolbar print-hidden">
        <ProfileCompletionRing profile={profile} compact />
          <div className="profile-toolbar-actions">
            <label className="button-secondary cursor-pointer hover-lift pressed focus-ring">
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
              onClick={() => setPreviewMode((current) => !current)}
            >
              <Eye size={16} />
              {previewMode ? "Volver al editor" : "Vista previa"}
            </button>
            <button
              className="button-secondary"
              type="button"
              onClick={exportPdf}
            >
              <Download size={16} />
              Exportar PDF
            </button>
            <button
              className="button-primary w-auto hover-lift pressed focus-ring"
              type="button"
              disabled={uploadingCv}
              onClick={() =>
                editing ? save() : (setPreviewMode(false), setEditing(true))
              }
            >
              {editing ? <Save size={16} /> : <Edit3 size={16} />}
              {editing ? "Guardar" : "Editar"}
            </button>
          </div>
      </section>
      <p className="profile-upload-note print-hidden">Importa tu PDF para completar los campos. El original es privado; puedes revisarlo en el Coach o reemplazarlo con otra carga.</p>
      {(message || error) && (
        <p
          className={`rounded-[var(--radius-lg)] border px-4 py-3 text-sm ${error ? "border-[var(--error)] bg-[var(--error)]/10 text-[var(--error)]" : "border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"}`}
        >
          {error || message}
        </p>
      )}
      {previewMode ? (
        <section className="surface-card print-hidden p-5">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex items-center gap-4">
            {profile.photo_url ? (
              <AuthenticatedImage
                src={`${profile.photo_url}?v=${photoVersion}`}
                alt="Foto de perfil"
                className="h-20 w-20 rounded-2xl object-cover ring-2 ring-[var(--line)]"
                fallback={<span className="grid h-20 w-20 place-items-center rounded-2xl bg-[var(--surface-subtle)] text-[var(--muted)]"><ImagePlus size={28} /></span>}
              />
            ) : (
              <span className="grid h-20 w-20 place-items-center rounded-2xl bg-[var(--surface-subtle)] text-[var(--muted)]">
                <ImagePlus size={28} />
              </span>
            )}
            <div>
              <h2 className="font-bold">Presentación de la hoja de vida</h2>
              <p className="mt-1 text-sm text-[var(--muted)]">Agrega una foto y elige el diseño que mejor te represente.</p>
              <label className="button-secondary button-sm mt-3 cursor-pointer">
                <ImagePlus size={15} /> Cambiar foto
                <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={uploadPhoto} />
              </label>
            </div>
          </div>
          <div className="space-y-4 lg:w-72 lg:shrink-0">
          <label className="block text-sm font-semibold text-[var(--muted)]">
            <span className="mb-1 flex items-center gap-2"><Palette size={16} /> Estilo</span>
            <select
              className="field-control"
              value={profile.resume_style}
              onChange={(event) => {
                const nextStyle = event.target.value;
                setProfile((current) => ({ ...current, resume_style: nextStyle, resume_color: getResumePalette(nextStyle, current.resume_color).id }));
                setEditing(true);
              }}
            >
              <option value="classic">Clásico profesional</option>
              <option value="modern">Moderno</option>
              <option value="minimal">Minimalista</option>
            </select>
          </label>
          <fieldset>
            <legend className="text-sm font-semibold text-[var(--muted)]">Color del diseño</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {getResumePalettes(profile.resume_style).map((palette) => (
                <button
                  key={palette.id}
                  type="button"
                  aria-label={`Color ${palette.label}`}
                  aria-pressed={profile.resume_color === palette.id}
                  title={palette.label}
                  className={`grid h-10 w-10 place-items-center rounded-full border-2 outline-offset-4 focus-visible:outline focus-visible:outline-2 focus-visible:outline-[var(--accent)] ${profile.resume_color === palette.id ? "border-[var(--accent)]" : "border-[var(--line)]"}`}
                  onClick={() => { update("resume_color", palette.id); setEditing(true); }}
                >
                  <span className="grid h-7 w-7 place-items-center rounded-full text-white" style={{ backgroundColor: palette.swatch }}>{profile.resume_color === palette.id ? <CheckCircle2 size={17} /> : null}</span>
                </button>
              ))}
            </div>
            <p className="mt-2 text-xs text-[var(--muted)]">{getResumePalette(profile.resume_style, profile.resume_color).label} · Vista actualizada · guarda para conservar tu elección.</p>
          </fieldset>
          </div>
          </div>
        </section>
      ) : null}
      {!previewMode && <CareerCoachWorkspace profile={profile} editing={editing} launch={coachLaunch} onEdit={editFromCoach} onProfileChanged={async () => { setProfile(normalize((await api.get("/profiles/me")).data)); await refreshUser(); }} />}
      {!previewMode && <nav className="profile-section-nav print-hidden" aria-label="Secciones de mi perfil">{[["profile-experiences", "Experiencia"], ["profile-educations", "Formación"], ["profile-skills", "Habilidades"], ["profile-certifications", "Certificados"], ["profile-languages", "Idiomas"], ["preferencias", "Preferencias"]].map(([id, label]) => <a key={id} href={`#${id}`}>{label}</a>)}{!editing && <a href="#profile-evidence">Evidencias</a>}</nav>}
      {previewMode ? (
        <ResumePreview profile={profile} name={name} email={email} photoVersion={photoVersion} />
      ) : (
        <article className="profile-document">
          <header className="profile-identity">
            <div className="absolute inset-x-0 top-0 h-1.5 bg-gradient-to-r from-[var(--accent)] to-[var(--success)]" />
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0 flex-1">
                {editing ? (
                  <label className="mb-3 block max-w-xl text-sm font-semibold text-[var(--muted)]">
                    Nombre completo
                    <input className="field-control input-lg mt-1" value={name} onChange={(event) => setName(event.target.value)} placeholder="Nombres y apellidos" />
                  </label>
                ) : (
                  <><p className="profile-eyebrow">PRESENTACIÓN PROFESIONAL</p><h2 className="profile-name">{name || "Candidato"}</h2></>
                )}
                <div className={`${editing ? "" : "mt-1"} text-xl font-bold text-[var(--ink)]`}>
                  {editing ? (
                    <input
                      className="field-control input-md max-w-xl"
                      value={profile.profession || ""}
                      onChange={(e) => update("profession", e.target.value)}
                      placeholder="Profesión" aria-label="Profesión"
                      id="profile-profession"
                    />
                  ) : (
                    profile.profession || "Perfil profesional"
                  )}
                </div>
                <div id="profile-contact" className="mt-5 flex flex-wrap gap-2 text-sm text-[var(--muted)]">
                  <span className="flex items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--surface)]/80 px-3 py-2">
                    <Mail size={15} className="text-[var(--muted)]" />
                    {email || "Correo no registrado"}
                  </span>
                  <span className="flex flex-wrap items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--surface)]/80 px-3 py-2">
                    <MapPin size={15} className="text-[var(--muted)]" />
                    {editing ? (
                      <>
                        <select
                          className="field-control input-sm w-44"
                          value={profile.department || ""}
                          onChange={(event) =>
                            setProfile((current) => ({
                              ...current,
                              department: event.target.value,
                              location: "",
                            }))
                          }
                        >
                          <option value="">Departamento</option>
                          {COLOMBIAN_DEPARTMENTS.map((department) => (
                            <option key={department}>{department}</option>
                          ))}
                        </select>
                        <select
                          className="field-control input-sm w-44"
                          value={profile.location || ""}
                          disabled={!profile.department}
                          onChange={(event) =>
                            update("location", event.target.value)
                          }
                        >
                          <option value="">Ciudad</option>
                          {(COLOMBIA_LOCATIONS[profile.department] || []).map(
                            (city) => (
                              <option key={city}>{city}</option>
                            ),
                          )}
                        </select>
                      </>
                    ) : (
                      [profile.location, profile.department]
                        .filter(Boolean)
                        .join(", ") || "Ciudad no registrada"
                    )}
                  </span>
                  <span className="flex items-center gap-1.5 rounded-lg border border-[var(--line)] bg-[var(--surface)]/80 px-3 py-2">
                    <Phone size={15} className="text-[var(--muted)]" />
                    {editing ? (
                      <input
                        className="field-control profile-phone-input"
                        value={profile.phone || ""}
                        onChange={(e) => update("phone", e.target.value)}
                        placeholder="Teléfono"
                      />
                    ) : (
                      profile.phone || "Teléfono no registrado"
                    )}
                  </span>
                </div>
              </div>
              <span className={`rounded-full px-3 py-1.5 text-xs font-semibold ${getProfileCompletion(profile).percentage === 100 ? "bg-[var(--success)]/20 text-[var(--success)]" : "bg-[var(--warning)]/15 text-[var(--warning)]"}`}>
                {getProfileCompletion(profile).percentage === 100 ? "Perfil listo para comparar" : `${getProfileCompletion(profile).percentage}% completo`}
              </span>
            </div>
          </header>
          <div className="profile-content-grid">
            <div className="profile-main-sections">
            <Section icon={UserRound} title="Resumen profesional">
              <p className="text-sm leading-6 text-[var(--muted)]">
                {profile.experience || "Agrega tu profesión, experiencia, formación y habilidades. Al guardar construiremos un resumen breve de tu trayectoria."}
              </p>
              {editing ? <p className="text-xs text-[var(--muted)]">Este resumen se actualiza automáticamente al guardar, sin repetir la lista de empresas.</p> : null}
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
            </div>
            <aside className="profile-side-sections">
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
              <CvContextReview rows={profile.cv_skill_context} skills={profile.skills} />
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((item) => (
                  <span
                    key={item}
                    className="profile-skill"
                  >
                    {item}
                    {editing && (
                      <button
                        type="button"
                        className="profile-skill-remove" aria-label={`Quitar habilidad ${item}`}
                        onClick={() =>
                          update(
                            "skills",
                            profile.skills.filter(
                              (current) => current !== item,
                            ),
                          )
                        }
                      >
                        x
                      </button>
                    )}
                  </span>
                ))}
              </div>
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
      {!editing && <div id="profile-evidence"><ProfileEvidence profile={profile} onChanged={async () => setProfile(normalize((await api.get("/profiles/me")).data))} /></div>}
    </div>
  );
}
function Section({ id, icon: Icon, title, children }) {
  return (
    <section id={id} className="profile-section">
      <h2 className="profile-section-heading">
        <span className="profile-section-icon"><Icon size={18} /></span>
        {title}
      </h2>
      <div className="profile-section-body space-y-3">{children}</div>
    </section>
  );
}
function Items({ type, profile, editing, update, updateItem }) {
  if (type === "educations") return <EducationFields items={profile.educations} editing={editing} onChange={(items) => update("educations", items)} />;
  if (type === "experiences") return <ExperienceFields items={profile.experiences} editing={editing} onChange={(items) => update("experiences", items)} />;
  const fields =
    type === "experiences"
      ? ["role", "company", "start_year", "end_year", "description"]
      : type === "educations"
        ? ["degree", "institution", "start_year", "end_year"]
        : ["name", "issuer", "year"];
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
                  <label key={field} className="text-xs font-semibold text-[var(--muted)]">{labels[field]}<input className="field-control input-md mt-1" placeholder={placeholders[field]} value={item[field] || ""} onChange={(event) => updateItem(type, index, field, event.target.value)} /></label>
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

const resumeStyles = {
  classic: {
    header: "bg-slate-950 text-white",
    photo: "rounded-xl",
  },
  modern: {
    header: "bg-white text-slate-950",
    photo: "rounded-full",
  },
  minimal: {
    header: "bg-white text-slate-950",
    photo: "rounded-full",
  },
};

function ResumePreview({ profile, name, email, photoVersion }) {
  const style = resumeStyles[profile.resume_style] || resumeStyles.classic;
  const palette = getResumePalette(profile.resume_style, profile.resume_color);
  const location = [profile.location, profile.department]
    .filter(Boolean)
    .join(", ");
  const initials = String(name || "Candidato")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  return (
    <article
      className={`resume-print-area resume-${profile.resume_style} mx-auto w-full max-w-6xl overflow-hidden bg-white text-slate-900 shadow-2xl`}
      style={palette.variables}
    >
      <header className={`resume-header ${style.header}`}>
        <div className="resume-identity">
          {profile.photo_url ? (
            <AuthenticatedImage
              src={`${profile.photo_url}?v=${photoVersion}`}
              alt=""
              className={`resume-photo shrink-0 object-cover ${style.photo}`}
              fallback={<span className={`resume-photo resume-monogram ${style.photo}`}>{initials}</span>}
            />
          ) : (
            <span className={`resume-photo resume-monogram ${style.photo}`}>
              {initials}
            </span>
          )}
          <div className="min-w-0">
            <p className="resume-eyebrow">Hoja de vida</p>
            <p className="resume-name">{name}</p>
            <p className="resume-profession">
              {profile.profession || "Perfil profesional"}
            </p>
          </div>
        </div>
        <div className="resume-contact-list">
          {email ? <span><Mail size={14} />{email}</span> : null}
          {profile.phone ? <span><Phone size={14} />{profile.phone}</span> : null}
          {location ? <span><MapPin size={14} />{location}</span> : null}
        </div>
      </header>
      <div className="resume-body">
        <aside className="resume-sidebar">
          {profile.languages?.length ? <ResumeSection title="Idiomas" compact>{profile.languages.map((item, index) => <p className="resume-compact-item capitalize" key={index}><b>{item.name}</b><br />{languageLevelLabel(item.level)}</p>)}</ResumeSection> : null}
          <ResumeSection title="Habilidades" compact>
            <div className="resume-skills">
              {profile.skills.map((item) => (
                <span key={item} className="resume-skill">
                  {item}
                </span>
              ))}
              {!profile.skills.length ? <span className="text-sm opacity-70">Sin habilidades registradas</span> : null}
            </div>
          </ResumeSection>
          {profile.certifications?.length ? (
            <ResumeSection title="Certificaciones" compact>
              {profile.certifications.map((item, index) => (
                <div key={`${item.name}-${index}`} className="resume-compact-item">
                  <p className="font-bold">{item.name}</p>
                  <p className="opacity-70">
                    {item.issuer}
                    {item.year ? ` · ${item.year}` : ""}
                  </p>
                </div>
              ))}
            </ResumeSection>
          ) : null}
          {(profile.preferred_sector || profile.preferred_modality || profile.availability) ? (
            <ResumeSection title="Preferencias" compact>
              <div className="space-y-3 text-sm">
                {profile.preferred_sector ? <p><b>Sector</b><span>{profile.preferred_sector}</span></p> : null}
                {profile.preferred_modality ? <p><b>Modalidad</b><span>{modalityLabels[profile.preferred_modality] || profile.preferred_modality}</span></p> : null}
                {profile.availability ? <p><b>Disponibilidad</b><span>{availabilityLabels[profile.availability] || profile.availability}</span></p> : null}
              </div>
            </ResumeSection>
          ) : null}
        </aside>
        <main className="resume-main">
          {profile.experience ? (
            <ResumeSection title="Perfil profesional">
              <p className="resume-summary">{profile.experience}</p>
            </ResumeSection>
          ) : null}
          {profile.experiences?.length ? (
            <ResumeSection title="Experiencia">
              {profile.experiences.map((item, index) => (
                <div
                  key={`${item.company}-${index}`}
                  className="resume-timeline-item break-inside-avoid"
                >
                  <div className="resume-item-heading">
                    <div>
                      <p className="resume-item-title">{item.role || "Cargo"}</p>
                      <p className="resume-item-company">{item.company}</p>
                    </div>
                    <p className="resume-item-date">
                      {experiencePeriod(item)}
                    </p>
                  </div>
                  {item.description ? (
                    <p className="resume-item-description">
                      {item.description}
                    </p>
                  ) : null}
                </div>
              ))}
            </ResumeSection>
          ) : null}
          {profile.educations?.length ? (
            <ResumeSection title="Formación">
              {profile.educations.map((item, index) => (
                <div
                  key={`${item.degree}-${index}`}
                  className="resume-education-item break-inside-avoid"
                >
                  <div>
                    <p className="resume-item-title">{item.degree}</p>
                    <p className="resume-item-company">{item.institution}</p>
                  </div>
                  <p className="resume-item-date">{item.start_year}{isOngoing(item) ? " – En curso" : item.end_year ? ` - ${item.end_year}` : ""}</p>
                </div>
              ))}
            </ResumeSection>
          ) : profile.education ? (
            <ResumeSection title="Formación">
              <p className="resume-summary">{profile.education}</p>
            </ResumeSection>
          ) : null}
        </main>
      </div>
    </article>
  );
}

function ResumeSection({ title, children, compact = false }) {
  return (
    <section className={compact ? "resume-section resume-section-compact" : "resume-section"}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
