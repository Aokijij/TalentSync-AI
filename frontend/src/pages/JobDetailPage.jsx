import { useEffect, useState } from "react";
import {
  ArrowLeft,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  MapPin,
  Send,
} from "lucide-react";
import { Link, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";

export function JobDetailPage() {
  const { jobId } = useParams();
  const { user } = useAuth();
  const [job, setJob] = useState(null);
  const [match, setMatch] = useState(null);
  const [successMessage, setSuccessMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [alreadyApplied, setAlreadyApplied] = useState(false);

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
    try {
      await api.post("/applications", { job_id: Number(jobId) });
      setAlreadyApplied(true);
      setSuccessMessage("Postulación enviada correctamente");
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
        to="/vacantes"
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        Volver a vacantes
      </Link>
      <section className="surface-card p-6">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <p className="text-sm font-semibold text-[var(--accent)]">
              {job.company_name}
            </p>
            <h1 className="mt-1 text-3xl font-bold">{job.title}</h1>
            <div className="mt-4 flex flex-wrap gap-4 text-sm text-[var(--muted)]">
              <span className="flex items-center gap-1">
                <MapPin size={16} />
                {[job.location, job.department].filter(Boolean).join(", ") ||
                  "Ubicación flexible"}
              </span>
              <span className="flex items-center gap-1">
                <Clock3 size={16} />
                {job.employment_type}
              </span>
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
            <div className="w-full max-w-64 rounded-[var(--radius-xl)] border border-[var(--line)] bg-[var(--surface-subtle)] p-3">
              <CompatibilityBar value={match.match_percentage} />
              <p className="mt-2 px-1 text-xs text-[var(--muted)]">
                Compatibilidad basada en contexto y habilidades.
              </p>
            </div>
          ) : null}
        </div>
      </section>
      <section className="grid gap-6 lg:grid-cols-[1fr_320px]">
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
          {user?.role === "candidate" ? (
            <>
              {alreadyApplied ? (
                <div className="mt-8 rounded-[var(--radius-lg)] bg-[var(--accent)]/10 px-4 py-3 text-center text-sm font-semibold text-[var(--accent)]">
                  Ya estás postulado a esta vacante
                </div>
              ) : (
                <button onClick={apply} className="button-primary mt-8 w-full">
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
