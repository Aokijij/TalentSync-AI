import { useEffect, useState } from "react";
import {
  ArrowLeft,
  Award,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  Mail,
  MapPin,
  Phone,
  Sparkles,
  UserRound,
} from "lucide-react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

import { api, apiFileUrl, getApiErrorMessage } from "../api/client.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";

const availabilityLabels = {
  immediate: "Inmediata",
  Immediate: "Inmediata",
  Inmediata: "Inmediata",
  two_weeks: "En 15 días",
  one_month: "En 30 días",
  negotiable: "Fecha acordada",
};
const modalityLabels = {
  remote: "Remoto",
  hybrid: "Híbrido",
  onsite: "Presencial",
};

export function CandidateDetailPage() {
  const { userId } = useParams();
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job");
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [match, setMatch] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    const profileRequest = api.get(`/profiles/candidates/${userId}`);
    const matchRequest = jobId
      ? api
          .get(`/recommendations/jobs/${jobId}/candidates`)
          .then(({ data }) =>
            data.find((item) => String(item.user_id) === String(userId)),
          )
          .catch(() => null)
      : Promise.resolve(null);
    Promise.all([profileRequest, matchRequest])
      .then(([{ data }, candidateMatch]) => {
        setCandidate(data);
        setMatch(candidateMatch || null);
      })
      .catch((requestError) =>
        setError(
          getApiErrorMessage(requestError, "No fue posible cargar el perfil"),
        ),
      );
  }, [jobId, userId]);

  if (error)
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
        >
          <ArrowLeft size={16} />
          Volver
        </button>
        <p className="rounded-xl border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">
          {error}
        </p>
      </div>
    );
  if (!candidate)
    return <p className="text-sm text-[var(--muted)]">Cargando perfil...</p>;

  return (
    <div className="space-y-6">
      <button
        type="button"
        onClick={() => navigate(-1)}
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        Volver a candidatos recomendados
      </button>
      <section className="page-hero">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-start gap-5">
            <CandidatePhoto key={`${userId}:${candidate.photo_url}`} candidate={candidate} />
            <div>
              <p className="section-kicker">Perfil de candidato</p>
              <h1 className="mt-2 font-display text-3xl font-semibold text-[var(--ink-strong)]">
                {candidate.name}
              </h1>
              <p className="mt-2 text-[var(--muted)]">
                {candidate.profession || "Perfil profesional"}
              </p>
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-[var(--muted)]">
                <span className="inline-flex items-center gap-1.5">
                  <Mail size={15} />
                  {candidate.email}
                </span>
                {candidate.phone && (
                  <span className="inline-flex items-center gap-1.5">
                    <Phone size={15} />
                    {candidate.phone}
                  </span>
                )}
                {candidate.location && (
                  <span className="inline-flex items-center gap-1.5">
                    <MapPin size={15} />
                    {candidate.location}
                  </span>
                )}
                <span className="inline-flex items-center gap-1.5">
                  <Award size={15} />
                  {availabilityLabels[candidate.availability] ||
                    candidate.availability ||
                    "Disponibilidad por definir"}
                </span>
              </div>
            </div>
          </div>
          {match ? (
            <div className="w-full rounded-[var(--radius-xl)] border border-[var(--accent)]/30 bg-[var(--accent)]/5 p-4 lg:w-72">
              <p className="mb-3 flex items-center gap-2 text-sm font-bold text-[var(--ink-strong)]">
                <Sparkles size={16} className="text-[var(--accent)]" />
                Compatibilidad para esta vacante
              </p>
              <CompatibilityBar value={match.match_percentage} />
            </div>
          ) : null}
        </div>
      </section>
      <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="space-y-6">
          <Timeline
            title="Experiencia laboral"
            icon={BriefcaseBusiness}
            items={candidate.experiences}
            empty="No hay experiencia laboral registrada."
            render={(item) => (
              <>
                <p className="font-bold text-[var(--ink-strong)]">
                  {item.role}
                </p>
                <p className="mt-1 text-sm font-semibold text-[var(--accent)]">
                  {item.company} · {item.start_year}
                  {item.end_year ? ` - ${item.end_year}` : ""}
                </p>
                {item.description && (
                  <p className="mt-2 text-sm leading-6 text-[var(--muted)]">
                    {item.description}
                  </p>
                )}
              </>
            )}
          />
          <Timeline
            title="Formación académica"
            icon={BookOpen}
            items={candidate.educations}
            empty="No hay formación académica registrada."
            render={(item) => (
              <>
                <p className="font-bold text-[var(--ink-strong)]">
                  {item.degree}
                </p>
                <p className="mt-1 text-sm font-semibold text-[var(--accent)]">
                  {item.institution} · {item.start_year}
                  {item.end_year ? ` - ${item.end_year}` : ""}
                </p>
              </>
            )}
          />
          <Timeline
            title="Cursos y certificaciones"
            icon={CheckCircle2}
            items={candidate.certifications}
            empty="No hay cursos o certificaciones registrados."
            render={(item) => (
              <>
                <p className="font-bold text-[var(--ink-strong)]">
                  {item.name}
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {item.issuer}
                  {item.year ? ` · ${item.year}` : ""}
                </p>
              </>
            )}
          />
        </div>
        <aside className="space-y-5">
          <section className="surface-card p-5"><h2 className="mb-3 font-bold">Idiomas</h2><LanguagesEditor value={candidate.languages || []} editing={false} /></section>
          <section className="surface-card p-5">
            <h2 className="font-bold text-[var(--ink-strong)]">
              Habilidades verificadas
            </h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(candidate.skills || []).map((skill) => (
                <span
                  key={skill}
                  className="rounded-full border border-[var(--accent)]/25 bg-[var(--accent)]/10 px-3 py-1.5 text-sm font-semibold text-[var(--accent)]"
                >
                  {skill}
                </span>
              ))}
              {!candidate.skills?.length && (
                <p className="text-sm text-[var(--muted)]">
                  No hay habilidades registradas.
                </p>
              )}
            </div>
          </section>
          <section className="surface-card p-5">
            <h2 className="font-bold text-[var(--ink-strong)]">Preferencias</h2>
            <dl className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Modalidad</dt>
                <dd className="font-semibold text-[var(--ink-strong)]">
                  {modalityLabels[candidate.preferred_modality] ||
                    candidate.preferred_modality ||
                    "Sin preferencia"}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Aspiración</dt>
                <dd className="font-semibold text-[var(--ink-strong)]">
                  {candidate.desired_salary
                    ? `$${Number(candidate.desired_salary).toLocaleString("es-CO")}`
                    : "No definida"}
                </dd>
              </div>
            </dl>
          </section>
        </aside>
      </section>
    </div>
  );
}

function CandidatePhoto({ candidate }) {
  const [failed, setFailed] = useState(false);
  return <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--accent)]/10 text-[var(--accent)]">
    {candidate.photo_url && !failed ? <img src={apiFileUrl(candidate.photo_url)} alt={`Foto de ${candidate.name}`} className="h-full w-full object-cover" onError={() => setFailed(true)} /> : <UserRound size={36} />}
  </div>;
}

function Timeline({ title, icon: Icon, items = [], empty, render }) {
  return (
    <section className="surface-card p-6">
      <h2 className="flex items-center gap-2 text-xl font-bold text-[var(--ink-strong)]">
        <Icon size={19} className="text-[var(--accent)]" />
        {title}
      </h2>
      <div className="mt-5 space-y-4">
        {items.length ? (
          items.map((item, index) => (
            <article
              key={`${title}-${index}`}
              className="border-l-2 border-[var(--line)] pl-4"
            >
              {render(item)}
            </article>
          ))
        ) : (
          <p className="text-sm text-[var(--muted)]">{empty}</p>
        )}
      </div>
    </section>
  );
}
