import { useEffect, useState } from "react";
import {
  Award,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  Download,
  Edit3,
  Eye,
  Mail,
  MapPin,
  Phone,
  Plus,
  Save,
  Trash2,
  Upload,
} from "lucide-react";
import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { ProfileCompletionRing } from "../components/ProfileCompletionRing.jsx";
import { JOB_SECTORS } from "../constants/jobSectors.js";
import {
  COLOMBIA_LOCATIONS,
  COLOMBIAN_DEPARTMENTS,
} from "../constants/colombianCities.js";

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
});

export function ProfilePage() {
  const [profile, setProfile] = useState(null);
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [editing, setEditing] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);
  const [skill, setSkill] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  useEffect(() => {
    Promise.all([api.get("/profiles/me"), api.get("/auth/me")])
      .then(([profileResponse, accountResponse]) => {
        setProfile(normalize(profileResponse.data));
        setEmail(accountResponse.data.email || "");
        setName(accountResponse.data.name || "Candidato");
      })
      .catch(() => setError("No fue posible cargar el perfil"));
  }, []);
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
    try {
      const { data } = await api.put("/profiles/me", profile);
      setProfile(normalize(data));
      setEditing(false);
      setMessage("Hoja de vida actualizada correctamente");
    } catch {
      setError("No fue posible actualizar la hoja de vida");
    }
  }
  async function upload(event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setMessage("Analizando PDF...");
    try {
      const { data } = await api.post("/profiles/me/cv", form);
      setProfile(normalize(data));
      setEditing(true);
      setMessage(
        `CV analizado: ${data.experiences?.length ?? 0} experiencias, ${data.educations?.length ?? 0} estudios y ${data.skills?.length ?? 0} habilidades. Revisa la información antes de guardar.`,
      );
    } catch (e) {
      setError(e.response?.data?.detail || "No fue posible procesar el PDF");
    }
  }
  function exportPdf() {
    setPreviewMode(true);
    setEditing(false);
    window.setTimeout(() => window.print(), 120);
  }
  if (!profile)
    return (
      <p className="text-sm text-[var(--muted)]">Cargando hoja de vida...</p>
    );
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Perfil profesional"
        title="Mi hoja de vida"
        description="Tu hoja de vida mejora el matching y las recomendaciones."
        actions={
          <div className="flex gap-2">
            <label className="button-secondary cursor-pointer hover-lift pressed focus-ring">
              <Upload size={16} />
              Subir CV
              <input
                className="hidden"
                type="file"
                accept="application/pdf"
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
              onClick={() =>
                editing ? save() : (setPreviewMode(false), setEditing(true))
              }
            >
              {editing ? <Save size={16} /> : <Edit3 size={16} />}
              {editing ? "Guardar" : "Editar"}
            </button>
          </div>
        }
      />
      {(message || error) && (
        <p
          className={`rounded-[var(--radius-lg)] border px-4 py-3 text-sm ${error ? "border-[var(--error)] bg-[var(--error)]/10 text-[var(--error)]" : "border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"}`}
        >
          {error || message}
        </p>
      )}
      <section className="surface-card print-hidden p-5">
        <ProfileCompletionRing profile={profile} compact />
      </section>
      {previewMode ? (
        <ResumePreview profile={profile} name={name} email={email} />
      ) : (
        <article className="mx-auto max-w-5xl overflow-hidden rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] shadow-soft">
          <header className="bg-[var(--success)]/10 p-6 sm:p-8">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h1 className="text-3xl font-bold text-[var(--ink)]">
                  {editing ? (
                    <input
                      className="field-control input-lg"
                      value={profile.profession || ""}
                      onChange={(e) => update("profession", e.target.value)}
                      placeholder="Profesion"
                    />
                  ) : (
                    profile.profession || "Perfil profesional"
                  )}
                </h1>
                <div className="mt-3 flex flex-wrap gap-4 text-sm text-[var(--muted)]">
                  <span className="flex items-center gap-1">
                    <Mail size={15} className="text-[var(--muted)]" />
                    {email || "Correo no registrado"}
                  </span>
                  <span className="flex flex-wrap items-center gap-1">
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
                  <span className="flex items-center gap-1">
                    <Phone size={15} className="text-[var(--muted)]" />
                    {editing ? (
                      <input
                        className="border-b bg-transparent"
                        value={profile.phone || ""}
                        onChange={(e) => update("phone", e.target.value)}
                        placeholder="Telefono"
                      />
                    ) : (
                      profile.phone || "Telefono no registrado"
                    )}
                  </span>
                </div>
              </div>
              <span className="rounded-full bg-[var(--success)]/20 px-3 py-1.5 text-xs font-semibold text-[var(--success)]">
                Perfil NLP activo
              </span>
            </div>
          </header>
          <div className="space-y-8 p-6 sm:p-8">
            <Section icon={Award} title="Experiencia laboral">
              <Items
                type="experiences"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            <Section icon={BookOpen} title="Formacion academica">
              <Items
                type="educations"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            <Section icon={CheckCircle2} title="Certificaciones">
              <Items
                type="certifications"
                profile={profile}
                editing={editing}
                update={update}
                updateItem={updateItem}
              />
            </Section>
            <Section icon={BriefcaseBusiness} title="Habilidades">
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((item) => (
                  <span
                    key={item}
                    className="rounded-full border border-[var(--line)] bg-[var(--surface)]/10 px-3 py-1.5 text-sm font-semibold text-[var(--muted)]"
                  >
                    {item}
                    {editing && (
                      <button
                        type="button"
                        className="ml-2 text-[var(--error)]"
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
                    placeholder="Ej. Python"
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
            <Section icon={BriefcaseBusiness} title="Preferencias laborales">
              {editing ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
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
                    <input
                      className="field-control mt-1"
                      type="number"
                      value={profile.desired_salary || ""}
                      onChange={(event) =>
                        update(
                          "desired_salary",
                          event.target.value
                            ? Number(event.target.value)
                            : null,
                        )
                      }
                      placeholder="COP"
                    />
                  </label>
                </div>
              ) : (
                <div className="grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
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
                    {profile.preferred_modality || "Sin definir"}
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
            </Section>
          </div>
        </article>
      )}
    </div>
  );
}
function Section({ icon: Icon, title, children }) {
  return (
    <section>
      <h2 className="flex items-center gap-2 border-b border-[var(--line)] pb-3 font-bold text-[var(--ink)]">
        <Icon size={19} className="text-[var(--success)]" />
        {title}
      </h2>
      <div className="mt-4 space-y-3">{children}</div>
    </section>
  );
}
function Items({ type, profile, editing, update, updateItem }) {
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
          className="rounded-[var(--radius-lg)] border border-[var(--line)] p-4"
        >
          {editing ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {fields.map((field) =>
                field === "description" ? (
                  <textarea
                    key={field}
                    className="field-control input-md sm:col-span-2"
                    placeholder={placeholders[field]}
                    value={item[field] || ""}
                    onChange={(event) =>
                      updateItem(type, index, field, event.target.value)
                    }
                  />
                ) : (
                  <input
                    key={field}
                    className="field-control input-md"
                    placeholder={placeholders[field]}
                    value={item[field] || ""}
                    onChange={(event) =>
                      updateItem(type, index, field, event.target.value)
                    }
                  />
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

function ResumePreview({ profile, name, email }) {
  return (
    <article className="resume-print-area mx-auto max-w-4xl overflow-hidden bg-white text-slate-900 shadow-xl">
      <header className="bg-sky-950 px-8 py-9 text-white sm:px-12">
        <p className="text-4xl font-bold tracking-tight text-white">{name}</p>
        <p className="mt-2 text-lg font-semibold text-sky-200">
          {profile.profession || "Perfil profesional"}
        </p>
        <div className="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-sm text-sky-100">
          <span>{email}</span>
          {profile.phone ? <span>{profile.phone}</span> : null}
          {profile.location ? <span>{profile.location}</span> : null}
        </div>
      </header>
      <div className="grid gap-9 px-8 py-9 sm:grid-cols-[1fr_2fr] sm:px-12">
        <aside className="space-y-8">
          <ResumeSection title="Habilidades">
            <div className="flex flex-wrap gap-2">
              {profile.skills.map((item) => (
                <span
                  key={item}
                  className="rounded-md bg-sky-50 px-2.5 py-1 text-xs font-semibold text-sky-900"
                >
                  {item}
                </span>
              ))}
            </div>
          </ResumeSection>
          {profile.certifications?.length ? (
            <ResumeSection title="Certificaciones">
              {profile.certifications.map((item, index) => (
                <div key={`${item.name}-${index}`} className="mb-3">
                  <p className="text-sm font-bold">{item.name}</p>
                  <p className="text-xs text-slate-600">
                    {item.issuer}
                    {item.year ? ` · ${item.year}` : ""}
                  </p>
                </div>
              ))}
            </ResumeSection>
          ) : null}
        </aside>
        <main className="space-y-8">
          {profile.experiences?.length ? (
            <ResumeSection title="Experiencia">
              {profile.experiences.map((item, index) => (
                <div
                  key={`${item.company}-${index}`}
                  className="mb-5 break-inside-avoid"
                >
                  <div className="flex flex-wrap justify-between gap-2">
                    <p className="font-bold">{item.role}</p>
                    <p className="text-xs font-semibold text-slate-500">
                      {item.start_year}
                      {item.end_year ? ` - ${item.end_year}` : ""}
                    </p>
                  </div>
                  <p className="text-sm font-semibold text-sky-800">
                    {item.company}
                  </p>
                  {item.description ? (
                    <p className="mt-2 text-sm leading-6 text-slate-600">
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
                  className="mb-4 break-inside-avoid"
                >
                  <p className="font-bold">{item.degree}</p>
                  <p className="text-sm text-slate-600">
                    {item.institution} · {item.start_year}
                    {item.end_year ? ` - ${item.end_year}` : ""}
                  </p>
                </div>
              ))}
            </ResumeSection>
          ) : null}
        </main>
      </div>
    </article>
  );
}

function ResumeSection({ title, children }) {
  return (
    <section>
      <h2 className="mb-4 border-b-2 border-sky-900 pb-2 text-sm font-bold uppercase tracking-[0.14em] text-sky-950">
        {title}
      </h2>
      {children}
    </section>
  );
}
