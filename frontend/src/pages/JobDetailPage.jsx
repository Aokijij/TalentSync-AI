import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Building2,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  MapPin,
  Send,
  BriefcaseBusiness,
  ExternalLink,
  X,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { api, apiFileUrl } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { formatRelativeTime } from "../utils/dates.js";

export function JobDetailPage() {
  const { jobId } = useParams();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [match, setMatch] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [alreadyApplied, setAlreadyApplied] = useState(false);
  const [showQuestions, setShowQuestions] = useState(false);
  const [answers, setAnswers] = useState({});

  useEffect(() => {
    api.get(`/jobs/${jobId}`).then(({ data }) => setJob(data));
    if (user?.role === "candidate") {
      api
        .post(`/jobs/${jobId}/match`)
        .then(({ data }) => setMatch(data))
        .catch(() => setMatch(null));
      api
        .get("/applications/me")
        .then(({ data }) =>
          setAlreadyApplied(
            data.some(
              (application) => Number(application.job_id) === Number(jobId),
            ),
          ),
        )
        .catch(() => setAlreadyApplied(false));
    }
  }, [jobId, user?.role]);

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
        Cargando vacante...
      </div>
    );
  return (
    <div className="space-y-6">
      <Link
        to={user?.role === "company" ? "/empresa/vacantes" : "/vacantes"}
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        {user?.role === "company" ? "Volver a mis vacantes" : "Volver a vacantes"}
      </Link>
      <section className="surface-card p-6">
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
                  ? `$${job.salary.toLocaleString("es-CO")}`
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
              <CompatibilityBar value={match.match_percentage} />
              <p className="mt-2 px-1 text-xs text-[var(--muted)]">
                Compatibilidad basada en tu trayectoria, habilidades{job.languages?.length ? " e idiomas" : ""}.
              </p>
            </div>
          ) : null}
        </div>
      </section>
      <section className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
        <div className="surface-card space-y-6 p-6">
          <Info title="Descripción" text={job.description} />
          <Info title="Requisitos" text={job.requirements} />
          <div>
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
          </div>
          <div className="rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface-subtle)] p-5">
            <div className="flex items-start gap-4">
              {job.company_logo_url ? <img src={apiFileUrl(job.company_logo_url)} alt={`Logo de ${job.company_name}`} className="h-14 w-14 rounded-xl border border-[var(--line)] bg-white object-contain p-1" /> : <span className="grid h-14 w-14 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Building2 size={26} /></span>}
              <div className="min-w-0 flex-1">
                <p className="section-kicker">Conoce a la empresa</p>
                <h2 className="mt-1 text-lg font-bold">{job.company_name}</h2>
                <p className="mt-2 line-clamp-3 text-sm leading-6 text-[var(--muted)]">{job.company_description || "La empresa todavía no ha publicado una descripción completa."}</p>
                <div className="mt-3 flex flex-wrap gap-3 text-xs text-[var(--muted)]">{job.company_location ? <span>{job.company_location}</span> : null}{job.company_size ? <span>{job.company_size}</span> : null}</div>
                <div className="mt-4 flex flex-wrap gap-2"><Link className="button-outline button-sm" to={user?.role === "company" ? "/empresa/perfil" : `/empresas/${job.company_id}`}>{user?.role === "company" ? "Ir a mi perfil" : "Ver perfil completo"}</Link>{job.company_website ? <a className="button-ghost button-sm" href={job.company_website} target="_blank" rel="noreferrer">Sitio web <ExternalLink size={14} /></a> : null}</div>
              </div>
            </div>
          </div>
        </div>
        <aside className="surface-card p-5">
          <h2 className="text-lg font-semibold">Habilidades relacionadas</h2>
          <div className="mt-4 space-y-3">
            {(job.skills || []).map((skill) => (
              <p className="flex items-center gap-2 text-sm" key={skill}>
                <CheckCircle2 size={16} className="text-[var(--accent)]" />
                {skill}
              </p>
            ))}
          </div>
          <div className="mt-6 border-t border-[var(--line)] pt-5"><h2 className="mb-3 font-semibold">Idiomas y nivel mínimo</h2><LanguagesEditor value={job.languages || []} editing={false} required /></div>
          {user?.role === "candidate" ? (
            <>
              {alreadyApplied ? (
                <div className="mt-8 rounded-[var(--radius-lg)] bg-[var(--accent)]/10 px-4 py-3 text-center text-sm font-semibold text-[var(--accent)]">
                  Ya estás postulado a esta vacante
                </div>
              ) : (
                <button onClick={() => job.application_questions?.length ? setShowQuestions(true) : apply()} className="button-primary mt-8 w-full">
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
        </aside>
      </section>
      {showQuestions ? (
        <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/65 p-4 backdrop-blur-sm">
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
