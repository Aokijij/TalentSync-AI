import { CandidateMatchExplanation } from "../components/CandidateMatchExplanation.jsx";
import { skillLevels, skillLevelFor } from "../utils/skillLevels.js";
import { isOngoing } from "../utils/profileStatus.js";
import { experiencePeriod } from "../utils/experienceDates.js";
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
  ShieldCheck,
  UserRound,
} from "lucide-react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { AuthenticatedImage } from "../components/AuthenticatedImage.jsx";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { ApplicationAnswersModal } from "../components/ApplicationAnswersModal.jsx";

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
  const location = useLocation();
  const [candidate, setCandidate] = useState(null);
  const [match, setMatch] = useState(null);
  const [application, setApplication] = useState(null);
  const [showAnswers, setShowAnswers] = useState(false);
  const [error, setError] = useState("");
  const [matchError, setMatchError] = useState("");
  const [retry, setRetry] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;
    setError(""); setMatchError(""); setCandidate(null); setMatch(null); setApplication(null);
    const profileRequest = api.get(`/profiles/candidates/${userId}`, { signal: controller.signal, params: jobId ? { job_id: jobId } : {} });
    const matchRequest = jobId ? api.get(`/recommendations/jobs/${jobId}/candidates/${userId}/explanation`, { signal: controller.signal }).then(({ data }) => data).catch((failure) => { if (!cancelled) setMatchError(getApiErrorMessage(failure, "No pudimos cargar la explicación de compatibilidad.")); return null; }) : Promise.resolve(null);
    const applicationRequest = jobId
      ? api.get(`/applications/jobs/${jobId}`, { signal: controller.signal }).then(({ data }) => data.find((item) => String(item.user_id) === String(userId))).catch(() => null)
      : Promise.resolve(null);
    Promise.all([profileRequest, matchRequest, applicationRequest])
      .then(([{ data }, candidateMatch, application]) => {
        if (cancelled) return;
        setCandidate(data);
        const base = Number(candidateMatch?.base_match_percentage ?? candidateMatch?.match_percentage ?? application?.base_match_percentage ?? 0);
        const adjustment = Number(application?.screening_adjustment ?? candidateMatch?.screening_adjustment ?? 0);
        setApplication(application ? { ...application, base_match_percentage: base } : null);
        setMatch(candidateMatch ? { ...candidateMatch, base_match_percentage: base, screening_adjustment: adjustment, match_percentage: Math.max(0, Math.min(100, base + adjustment)) } : null);
      })
      .catch((requestError) => {
        if (!cancelled) setError(
          getApiErrorMessage(requestError, "No fue posible cargar el perfil"),
        );
      });
    return () => { cancelled = true; controller.abort(); };
  }, [jobId, userId, retry]);

  if (error)
    return (
      <div className="space-y-4">
        <button
          type="button"
          onClick={() => navigate(location.state?.returnTo || (jobId ? `/empresa/talento?job=${jobId}&audience=applied&min=0` : "/empresa/talento"))}
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
      {candidate.submitted_version && <p className="surface-card p-4 text-sm text-[var(--muted)]">Estás viendo la versión del perfil enviada para esta vacante. Los cambios posteriores del perfil principal se mantienen separados. La compatibilidad base se calcula con el perfil actual registrado.</p>}
      <button
        type="button"
        onClick={() => navigate(location.state?.returnTo || (jobId ? `/empresa/talento?job=${jobId}&audience=applied&min=0` : "/empresa/talento"))}
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        Volver a candidatos recomendados
      </button>
      {candidate.identity_hidden && <aside className="identity-note"><ShieldCheck size={22} /><div><h2 className="font-bold">Perfil profesional en selección ciega</h2><p>La vacante oculta nombre, contacto y organizaciones de origen. La identidad se revela al avanzar a entrevista; puedes revisar habilidades, formación y trayectoria desde ahora.</p><Link to={`/procesos/${application?.id || ""}`} className="text-[var(--accent)]">Consultar el proceso →</Link></div></aside>}
      <section className="surface-card overflow-hidden !p-0">
        <div className="h-1.5 bg-gradient-to-r from-[var(--accent)] via-cyan-300 to-[var(--success)]" />
        <div className="p-6 sm:p-8">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-wrap items-start gap-5">
            <CandidatePhoto key={`${userId}:${candidate.photo_url}`} candidate={candidate} />
            <div className="min-w-0">
              <p className="section-kicker">Perfil de candidato</p>
              <h1 className="mt-2 font-display text-3xl font-semibold text-[var(--ink-strong)]">
                {candidate.name}
              </h1>
              <p className="mt-2 text-[var(--muted)]">
                {candidate.profession || "Perfil profesional"}
              </p>
              {candidate.experience ? <p className="mt-3 max-w-3xl text-sm leading-6 text-[var(--muted)]">{candidate.experience}</p> : null}
              <div className="mt-4 flex flex-wrap gap-3 text-sm text-[var(--muted)]">
                {candidate.email && <span className="inline-flex items-center gap-1.5"><Mail size={15} />{candidate.email}</span>}
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
              {match.screening_adjustment ? <p className="mt-2 text-xs text-[var(--muted)]">Base {Math.round(match.base_match_percentage)}% · respuestas {match.screening_adjustment > 0 ? "+" : ""}{match.screening_adjustment} puntos. Este ajuste es privado para la empresa.</p> : null}
              {application?.screening_answers?.length ? <button type="button" className="button-outline mt-3 w-full" onClick={() => setShowAnswers(true)}>Ver respuestas y valorar</button> : null}
            </div>
          ) : null}
        </div></div>
      </section>
      {match?.match_details && <CandidateMatchExplanation match={match} />}
      {matchError && <section className="surface-card p-4" role="alert"><p className="text-sm text-[var(--error)]">{matchError}</p><button type="button" className="button-secondary mt-3" onClick={() => setRetry((value) => value + 1)}>Reintentar explicación</button></section>}
      <ApplicationAnswersModal application={showAnswers ? application : null} candidateName={candidate.name} onClose={() => setShowAnswers(false)} onSaved={(updated) => { setApplication(updated); setMatch((current) => current ? { ...current, screening_adjustment: updated.screening_adjustment, match_percentage: updated.adjusted_match_percentage } : current); }} />
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
                  {item.company ? `${item.company} · ` : ""}{experiencePeriod(item)}
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
                  {item.institution ? `${item.institution} · ` : ""}{item.start_year}
                  {isOngoing(item) ? " – En curso" : item.end_year ? ` - ${item.end_year}` : ""}
                </p>
              </>
            )}
          />
          {!candidate.identity_hidden && <Timeline
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
                </p><div className="candidate-certificate-details"><span>Certificado aportado por el candidato</span>{item.url?.startsWith("https://") && <a className="button-secondary button-sm" href={item.url} target="_blank" rel="noopener noreferrer">Ver documento aportado ↗</a>}</div>
              </>
            )}
          />}
        </div>
        <aside className="space-y-5">
          <section className="surface-card p-5"><h2 className="mb-3 font-bold">Idiomas</h2><LanguagesEditor value={candidate.languages || []} editing={false} /></section>
          <section className="surface-card p-5">
            <h2 className="font-bold text-[var(--ink-strong)]">
              Habilidades declaradas
            </h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {(candidate.skills || []).map((skill) => (
                <span
                  key={skill}
                  className="rounded-full border border-[var(--accent)]/25 bg-[var(--accent)]/10 px-3 py-1.5 text-sm font-semibold text-[var(--accent)]"
                >
                  {skill}{skillLevelFor(candidate.skill_levels, skill) !== "unspecified" ? ` · ${skillLevels[skillLevelFor(candidate.skill_levels, skill)]}` : ""}
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
  return <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-2xl border border-[var(--line)] bg-[var(--accent)]/10 text-[var(--accent)]">
    <AuthenticatedImage src={candidate.photo_url} alt={`Foto de ${candidate.name}`} className="h-full w-full object-cover" fallback={<UserRound size={36} />} />
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
