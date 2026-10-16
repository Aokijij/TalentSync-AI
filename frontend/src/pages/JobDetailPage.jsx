import { EDUCATION_LEVELS } from "../constants/educationLevels.js";
import { skillLevels, skillKey } from "../utils/skillLevels.js";
import { AdminVacancyActions } from "../components/AdminVacancyActions.jsx";
import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  PencilLine,
  BookOpen,
  Globe2,
  Building2,
  CalendarDays,
  CircleDollarSign,
  Clock3,
  MapPin,
  Send,
  BriefcaseBusiness,
  ExternalLink,
  X,
} from "lucide-react";
import { Link, useLocation, useParams } from "react-router-dom";

import { OfferConditions } from "../components/OfferConditions.jsx";
import { VacancyCvAdvice } from "../components/VacancyCvAdvice.jsx";
import { OfferFeedback } from "../components/OfferFeedback.jsx";
import { salaryLabel } from "../utils/offerQuality.js";
import { loadVacancyData } from "../utils/vacancyRequests.js";

import { api, apiFileUrl, getApiErrorMessage } from "../api/client.js";
import { CompanyScore } from "../components/CompanyScore.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { languageLevelLabel } from "../constants/languages.js";
import "../styles/job-detail.css";
import { ExternalApplicationDialog } from "../components/ExternalApplicationDialog.jsx";
import { StructuredJobText } from "../components/StructuredJobText.jsx";
import { formatRelativeTime } from "../utils/dates.js";
import { cleanExternalLocation, externalPortal } from "../utils/externalPortal.js";

export function JobDetailPage() {
  const { jobId } = useParams();
  return <JobDetailContent key={jobId} jobId={jobId} />;
}

function JobDetailContent({ jobId }) {
  const routeLocation = useLocation();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [match, setMatch] = useState(null);
  const [matchError, setMatchError] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [alreadyApplied, setAlreadyApplied] = useState(false);
  const [showQuestions, setShowQuestions] = useState(false);
  const [showExternalWarning, setShowExternalWarning] = useState(false);
  const [answers, setAnswers] = useState({});
  const [availableJobs, setAvailableJobs] = useState([]);
  const [companyId, setCompanyId] = useState(null);
  const [companyRole, setCompanyRole] = useState(null);
  useEffect(() => { if (routeLocation.hash === "#postularme" && job?.application_questions?.length) setShowQuestions(!alreadyApplied); }, [job, routeLocation.hash, alreadyApplied]);
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "auto" });
    return loadVacancyData(api, { jobId, role: user?.role }, {
      job: (data) => setJob({ ...data, location: data.source_kind === "external" ? cleanExternalLocation(data.location) : data.location }),
      catalog: (data) => setAvailableJobs(data.map((item) => ({ ...item, location: item.source_kind === "external" ? cleanExternalLocation(item.location) : item.location }))),
      match: setMatch,
      matchError: (failure) => setMatchError(getApiErrorMessage(failure, "No pudimos calcular la compatibilidad de esta oferta.")),
      applications: (data) => setAlreadyApplied(data.some((item) => Number(item.job_id) === Number(jobId))),
      company: (data) => { setCompanyId(data?.id ?? null); setCompanyRole(data?.active === false ? null : data?.role); },
      error: () => setErrorMessage("No pudimos cargar esta vacante. Vuelve a intentarlo."),
    });
  }, [jobId, user?.role]);

  const isOwnCompanyJob = user?.role === "company" && Number(companyId) === Number(job?.company_id);

  const similarJobs = useMemo(() => {
    if (!job) return [];
    const skills = new Set((job.skills || []).map((item) => item.toLowerCase()));
    return availableJobs
      .filter((item) => item.id !== job.id && item.status === "active")
      .map((item) => ({
        ...item,
        similarity:
          (item.sector === job.sector ? 3 : 0) +
          (item.modality === job.modality ? 1 : 0) +
          (item.skills || []).filter((skill) => skills.has(skill.toLowerCase())).length * 2,
      }))
      .filter((item) => item.similarity > 0)
      .sort((first, second) => second.similarity - first.similarity || new Date(second.created_at) - new Date(first.created_at))
      .slice(0, 3);
  }, [availableJobs, job]);

  async function apply() {
    const missing = (job.application_questions || []).find(
      (question) => question.required && !String(answers[question.id] || "").trim(),
    );
    if (missing) {
      setErrorMessage(`Responde la pregunta: ${missing.prompt}`);
      return;
    }
    try {
      await api.post("/applications", {
        job_id: Number(jobId),
        screening_answers: Object.entries(answers)
          .filter(([, answer]) => String(answer).trim())
          .map(([question_id, answer]) => ({ question_id, answer: String(answer).trim() })),
      });
      setAlreadyApplied(true);
      setSuccessMessage("Postulación enviada correctamente");
      setShowQuestions(false);
    } catch (error) {
      setErrorMessage(
        error.response?.data?.detail || "No fue posible enviar la postulación",
      );
    }
  }

  if (!job)
    return (
      <div className="surface-card p-8 text-[var(--muted)]">
        {errorMessage || "Cargando vacante…"}
      </div>
    );
  const displayedSkills = [...new Map([...(job.skill_requirements || []).map((row) => row.skill), ...(job.skills || [])].map((skill) => [skillKey(skill), skill])).values()];
  const minimumLevels = Object.fromEntries((job.skill_requirements || []).map((row) => [skillKey(row.skill), row.level]));
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3"><Link
        to={user?.role === "company" ? "/empresa/vacantes" : (routeLocation.state?.returnTo || "/vacantes")}
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        {user?.role === "company" ? "Volver a mis vacantes" : "Volver a vacantes"}
      </Link>
      {isOwnCompanyJob && ["owner", "recruiter"].includes(companyRole) && <Link className="button-secondary" to={`/empresa/calidad?vacante=${job.id}`}><PencilLine size={16} />Editar vacante</Link>}</div>
      {user?.role === "admin" && <AdminVacancyActions job={job} onChanged={setJob} />}
      <section className="surface-card p-6">
        {matchError && <div className="vacancy-match-notice" role="status"><p>{matchError}</p><button type="button" onClick={async () => { setMatchError(""); try { setMatch((await api.post(`/jobs/${jobId}/match`, {}, { __quiet: true })).data); } catch (failure) { setMatchError(getApiErrorMessage(failure, "La compatibilidad aún no está disponible.")); } }}>Volver a calcular</button></div>}
        <div className={match ? "grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_280px]" : "block"}>
          <div>
            {user?.role === "candidate" || user?.role === "admin" ? (
              <Link className="text-sm font-semibold text-[var(--accent)] hover:underline" to={`/empresas/${job.company_id}`}>
                {job.company_name} · Ver empresa
              </Link>
            ) : (
              <p className="text-sm font-semibold text-[var(--accent)]">{job.company_name}</p>
            )}
            <h1 className="mt-1 text-3xl font-bold">{job.title}</h1>
            {job.source_kind === "external" ? (
              <p className="mt-2 inline-flex items-center gap-1.5 rounded-full bg-[var(--accent)]/10 px-3 py-1 text-xs font-semibold text-[var(--accent)]">
                <ExternalLink size={13} />
                Oferta disponible en {externalPortal(job)}
              </p>
            ) : null}
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-[var(--muted)]">
              <span className="flex items-center gap-1">
                <MapPin size={16} />
                {[job.location, job.department].filter(Boolean).join(", ") ||
                  "Ubicación flexible"}
              </span>
              <span className="flex items-center gap-1">
                <Clock3 size={16} />
                {{ full_time: "Tiempo completo", part_time: "Medio tiempo", contract: "Contrato", internship: "Prácticas", temporary: "Temporal" }[job.employment_type] || "Tipo de contrato no especificado"}
              </span>
              <span className="flex items-center gap-1"><BriefcaseBusiness size={16} />{{ remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" }[job.modality] || "Modalidad no especificada"}</span>
              <span className="flex items-center gap-1"><CalendarDays size={16} />Publicada {formatRelativeTime(job.created_at).toLowerCase()}</span>
              <span className="flex items-center gap-1">
                <CircleDollarSign size={16} />
                {job.salary
                  ? salaryLabel(job)
                  : job.source_kind === "external"
                    ? "Salario no informado"
                    : "A convenir"}
              </span>
              {job.sector ? (
                <span className="rounded-full border border-[var(--line)] bg-[var(--surface-subtle)] px-2.5 py-1 text-xs font-semibold text-[var(--ink-strong)]">
                  {job.sector}
                </span>
              ) : null}
            </div>
          </div>
          {match ? (
            <div className="w-full rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
              <CompatibilityBar
                value={match.match_percentage}
                estimated={job.source_kind === "external"}
                confidence={match.data_confidence_percentage}
              />
              <p className="mt-2 px-1 text-xs text-[var(--muted)]">
                {job.source_kind === "external"
                  ? `Estimación basada en el resumen y las habilidades identificadas${job.languages?.length ? ", además de los idiomas" : ""}. Confirma los requisitos en la oferta original.`
                  : `Compatibilidad basada en tu trayectoria, habilidades${job.languages?.length ? " e idiomas" : ""}.`}
              </p>
            </div>
          ) : null}
        </div>
      </section>
      <section className="job-detail-grid grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
        <div className="surface-card space-y-6 p-6">
          <OfferConditions job={job} />
          {job.source_kind === "external" ? (
            <div>
              <h2 className="font-semibold">Resumen de la oferta</h2>
              <div className="mt-3"><StructuredJobText text={job.description} /></div>
            </div>
          ) : <Info title="Descripción" text={job.description} />}
          {job.source_kind === "external" ? (
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="rounded-[var(--radius-lg)] border border-[var(--accent)]/30 bg-[var(--accent)]/10 p-4">
                <h2 className="font-semibold">Qué puede analizar TalentSync</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  El cargo, la ubicación, la empresa, el salario cuando está disponible
                  y la información pública de {externalPortal(job)}. De esas
                  señales se extraen las habilidades visibles en esta página.
                </p>
              </div>
              <div className="rounded-[var(--radius-lg)] border border-[var(--warning)]/30 bg-[var(--warning)]/10 p-4">
                <h2 className="font-semibold">Qué debes confirmar</h2>
                <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                  Funciones completas, experiencia mínima, beneficios, vigencia y
                  condiciones contractuales. Esa información solo está en el anuncio
                  original.
                </p>
              </div>
            </div>
          ) : (
            <Info title="Requisitos" text={job.requirements} />
          )}
          {job.source_kind !== "external" ? <div>
            <h2 className="font-semibold">Beneficios</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {(job.benefits || []).map((benefit) => (
                <span
                  key={benefit}
                  className="rounded-md border border-[var(--line)] bg-[var(--surface-subtle)] px-3 py-2 text-sm text-[var(--ink-strong)]"
                >
                  {benefit}
                </span>
              ))}
              {!job.benefits?.length ? (
                <p className="text-sm text-[var(--muted)]">
                  La empresa no ha registrado beneficios adicionales.
                </p>
              ) : null}
            </div>
          </div> : null}
          <div className="rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface-subtle)] p-5">
            <div className="flex items-start gap-4">
              {job.company_logo_url ? <img src={apiFileUrl(job.company_logo_url)} alt={`Logo de ${job.company_name}`} className="h-14 w-14 rounded-xl border border-[var(--line)] bg-white object-contain p-1" /> : <span className="grid h-14 w-14 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Building2 size={26} /></span>}
              <div className="min-w-0 flex-1">
                <p className="section-kicker">Conoce a la empresa</p>
                <h2 className="mt-1 text-lg font-bold">{job.company_name}</h2>
                {job.source_kind !== "external" && <CompanyScore value={job.employer_trust?.score} />}
                <p className="mt-2 line-clamp-3 text-sm leading-6 text-[var(--muted)]">
                  {job.source_kind === "external"
                    ? `Empresa con una oportunidad publicada en ${externalPortal(job)}.`
                    : job.company_description || "La empresa todavía no ha publicado una descripción completa."}
                </p>
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-[var(--muted)]">{job.company_location ? <span>{job.company_location}</span> : null}{job.company_size ? <span>{job.company_size}</span> : null}</div>
                <div className="mt-4 flex flex-wrap gap-2"><Link className="button-outline button-sm" to={user?.role === "company" ? "/empresa/perfil" : `/empresas/${job.company_id}`}>{user?.role === "company" ? "Ir a mi perfil" : "Ver perfil completo"}</Link>{job.company_website ? <a className="button-ghost button-sm" href={job.company_website} target="_blank" rel="noreferrer">Sitio web <ExternalLink size={14} /></a> : null}</div>
              </div>
            </div>
          </div>
        </div>
        <aside className="job-detail-sidebar">
          <section className="job-requirements-card"><header><span><BriefcaseBusiness size={19} /></span><div><small>ANTES DE POSTULARTE</small><h2>Lo que busca esta oferta</h2></div></header>
            <div className="job-requirement-group"><h3>{job.source_kind === "external" ? "Habilidades identificadas" : "Habilidades relacionadas"}</h3><div className="job-skill-chips">{displayedSkills.map((skill) => <span key={skillKey(skill)}>{skill}{minimumLevels[skillKey(skill)] && minimumLevels[skillKey(skill)] !== "unspecified" ? ` · ${skillLevels[minimumLevels[skillKey(skill)]]}` : ""}</span>)}</div>{!displayedSkills.length && <p>Consulta los requisitos en la descripción de la oferta.</p>}</div>
            {(job.required_education_level || job.required_study_fields?.length) ? <div className="job-requirement-group"><h3><BookOpen size={16} />Formación requerida</h3><p className="job-requirement-value">{EDUCATION_LEVELS[job.required_education_level] || "Nivel no especificado"}</p>{!!job.required_study_fields?.length && <div className="job-skill-chips">{job.required_study_fields.map((field) => <span key={field}>{field}</span>)}</div>}<small>{job.quality_details?.education_accepts_in_progress ? "Se aceptan estudios en curso del nivel y área solicitados." : "Se solicitan estudios terminados; se reconocen títulos equivalentes del mismo campo."}</small></div> : null}
            <div className="job-requirement-group"><h3><Globe2 size={16} />Idiomas</h3>{job.languages?.length ? <div className="job-language-list">{job.languages.map((language) => <p key={language.name}><strong>{language.name}</strong><span>{languageLevelLabel(language.level)}</span></p>)}</div> : <p>No se especifica un requisito de idioma.</p>}</div>
          </section>
          {user?.role === "candidate" && <VacancyCvAdvice key={jobId} jobId={jobId} />}
          {user?.role === "candidate" && <section className="job-apply-card"><h2>{alreadyApplied ? "Tu postulación" : "¿Te interesa esta oportunidad?"}</h2><p>{alreadyApplied ? "Puedes consultar su avance desde Postulaciones." : "Revisa los requisitos y envía tu perfil cuando estés listo."}</p>
          {user?.role === "candidate" ? (
            <>
              {job.source_kind === "external" && job.external_url ? (
                <div className="mt-8 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
                  <p className="text-sm leading-5 text-[var(--muted)]">
                    Esta vacante fue publicada fuera de TalentSync. Revisa sus condiciones y
                    continúa el proceso en el sitio de origen.
                  </p>
                  <button
                    type="button"
                    className="button-primary mt-4 w-full"
                    onClick={() => setShowExternalWarning(true)}
                  >
                    <ExternalLink size={16} />
                    Postularme en el sitio original
                  </button>
                </div>
              ) : alreadyApplied ? (
                <div className="mt-8 rounded-[var(--radius-lg)] bg-[var(--accent)]/10 px-4 py-3 text-center text-sm font-semibold text-[var(--accent)]">
                  Ya estás postulado a esta vacante
                </div>
              ) : (
                <button id="job-apply-action" onClick={() => job.application_questions?.length ? setShowQuestions(true) : apply()} className="button-primary mt-8 w-full">
                  <Send size={16} />
                  Postularme
                </button>
              )}
              {successMessage ? (
                <p className="mt-3 text-sm text-[var(--success)]">
                  {successMessage}
                </p>
              ) : null}
              {errorMessage ? (
                <p className="mt-3 text-sm text-[var(--error)]">
                  {errorMessage}
                </p>
              ) : null}
            </>
          ) : null}
          </section>}
        </aside>
      </section>
      {!isOwnCompanyJob && similarJobs.length ? (
        <section className="surface-card p-6">
          <div>
            <p className="section-kicker">También puede interesarte</p>
            <h2 className="mt-1 text-xl font-bold">Vacantes similares</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">Relacionadas por sector, modalidad y habilidades solicitadas.</p>
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {similarJobs.map((item) => (
              <Link key={item.id} to={`/vacantes/${item.id}`} state={{ returnTo: routeLocation.state?.returnTo || "/vacantes" }} className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4 transition hover:border-[var(--accent)]">
                <p className="text-xs font-bold uppercase tracking-wide text-[var(--accent)]">{item.company_name}</p>
                <h3 className="mt-2 font-bold text-[var(--ink-strong)]">{item.title}</h3>
                <p className="mt-3 text-xs text-[var(--muted)]">{item.location || "Ubicación flexible"} · {formatRelativeTime(item.created_at)}</p>
                <div className="mt-3 flex flex-wrap gap-1.5">{(item.skills || []).slice(0, 3).map((skill) => <span key={skill} className="rounded-md border border-[var(--line)] px-2 py-1 text-[11px]">{skill}</span>)}</div>
              </Link>
            ))}
          </div>
        </section>
      ) : null}
      {user?.role === "candidate" && !alreadyApplied && job.status === "active" && job.source_kind !== "external" && <OfferFeedback key={job.id} jobId={job.id} />}
      {showQuestions ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/65 p-4 backdrop-blur-xs">
          <section role="dialog" aria-modal="true" aria-labelledby="questions-title" className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl">
            <header className="flex items-start justify-between gap-4 border-b border-[var(--line)] pb-4"><div><p className="section-kicker">Último paso</p><h2 id="questions-title" className="mt-1 text-2xl font-bold">Responde antes de postularte</h2><p className="mt-2 text-sm text-[var(--muted)]">Tus respuestas serán revisadas por {job.company_name}. Los campos con * son obligatorios.</p></div><button type="button" className="button-secondary !h-10 !w-10 !p-0" onClick={() => setShowQuestions(false)} aria-label="Cerrar"><X size={18} /></button></header>
            <div className="mt-5 space-y-5">
              {job.application_questions.map((question, index) => (
                <label key={question.id} className="block text-sm font-semibold text-[var(--ink-strong)]"><span>{index + 1}. {question.prompt}{question.required ? " *" : ""}</span>{question.type === "choice" ? <select className="field-control mt-2" value={answers[question.id] || ""} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}><option value="">Selecciona una respuesta</option>{question.options.map((option) => <option key={option}>{option}</option>)}</select> : <textarea className="field-control mt-2 min-h-28" maxLength={2000} value={answers[question.id] || ""} onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))} placeholder="Escribe una respuesta clara y concreta" />}</label>
              ))}
            </div>
            {errorMessage ? <p className="mt-4 rounded-xl bg-[var(--error)]/10 p-3 text-sm text-[var(--error)]">{errorMessage}</p> : null}
            <footer className="mt-6 flex justify-end gap-2 border-t border-[var(--line)] pt-5"><button type="button" className="button-secondary" onClick={() => setShowQuestions(false)}>Cancelar</button><button type="button" className="button-primary" onClick={apply}><Send size={16} />Enviar postulación</button></footer>
          </section>
        </div>
      ) : null}
      {showExternalWarning ? (
        <ExternalApplicationDialog
          job={job}
          onClose={() => setShowExternalWarning(false)}
        />
      ) : null}
    </div>
  );
}

function Info({ title, text }) {
  return (
    <div>
      <h2 className="font-semibold">{title}</h2>
      <p className="mt-3 whitespace-pre-line text-sm leading-6 text-[var(--muted)]">
        {text}
      </p>
    </div>
  );
}
