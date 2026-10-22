import { CandidateHero } from "../components/CandidateHero.jsx";
import { TRAINING_TYPES } from "../constants/trainingTypes.js";
import { ProfileCredentials } from "../components/ProfileCredentials.jsx";
import { CandidateMatchExplanation } from "../components/CandidateMatchExplanation.jsx";
import { ProfileLinks } from "../components/ProfileLinks.jsx";
import { StructuredJobText } from "../components/StructuredJobText.jsx";
import { skillLevels, skillLevelFor } from "../utils/skillLevels.js";
import { isOngoing } from "../utils/profileStatus.js";
import { experiencePeriod, recentExperiences } from "../utils/experienceDates.js";
import { useEffect, useState } from "react";
import {
  ArrowLeft,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  Sparkles,
  ShieldCheck,
} from "lucide-react";
import { Link, useLocation, useNavigate, useParams, useSearchParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { LanguagesEditor } from "../components/LanguagesEditor.jsx";
import { ApplicationAnswersModal } from "../components/ApplicationAnswersModal.jsx";

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
    const profileRequest = api.get(`/profiles/candidates/${userId}`, { signal: controller.signal, params: jobId ? { job_id: jobId } : {} }).then((response) => { if (!cancelled) setCandidate(response.data); return response; });
    const matchRequest = jobId ? api.get(`/recommendations/jobs/${jobId}/candidates/${userId}/explanation`, { signal: controller.signal }).then(({ data }) => { if (!cancelled) setMatch(data); return data; }).catch((failure) => { if (!cancelled) setMatchError(getApiErrorMessage(failure, "No pudimos cargar la explicación de compatibilidad.")); return null; }) : Promise.resolve(null);
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
          onClick={() => navigate(location.state?.returnTo || (jobId ? `/empresa/talento?job=${jobId}&audience=applied&min=40` : "/empresa/talento"))}
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
    <div className="company-candidate-profile space-y-6">
      {candidate.submitted_version && <p className="surface-card p-4 text-sm text-[var(--muted)]">Estás viendo la versión del perfil enviada para esta vacante. Los cambios posteriores del perfil principal se mantienen separados. La compatibilidad base se calcula con el perfil actual registrado.</p>}
      <button
        type="button"
        onClick={() => navigate(location.state?.returnTo || (jobId ? `/empresa/talento?job=${jobId}&audience=applied&min=40` : "/empresa/talento"))}
        className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline"
      >
        <ArrowLeft size={16} />
        Volver a candidatos recomendados
      </button>
      {candidate.identity_hidden && <aside className="identity-note"><ShieldCheck size={22} /><div><h2 className="font-bold">Perfil profesional en selección ciega</h2><p>La vacante oculta nombre, contacto y organizaciones de origen. La identidad se comparte cuando la persona se postula a esta vacante.</p><Link to={`/procesos/${application?.id || ""}`} className="text-[var(--accent)]">Consultar el proceso →</Link></div></aside>}
      <CandidateHero candidate={candidate}>
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
      </CandidateHero>
      {candidate.experience && <section className="profile-section candidate-profile-summary"><h2>Resumen profesional</h2><p>{candidate.experience}</p></section>}
      {jobId && !match && !matchError && <section className="surface-card p-4 text-sm text-[var(--muted)]" role="status">Preparando la explicación de compatibilidad… Puedes revisar el perfil mientras termina.</section>}
      {match?.match_details && <CandidateMatchExplanation match={match} />}
      {matchError && <section className="surface-card p-4" role="alert"><p className="text-sm text-[var(--error)]">{matchError}</p><button type="button" className="button-secondary mt-3" onClick={() => setRetry((value) => value + 1)}>Reintentar explicación</button></section>}
      <ApplicationAnswersModal application={showAnswers ? application : null} candidateName={candidate.name} onClose={() => setShowAnswers(false)} onSaved={(updated) => { setApplication(updated); setMatch((current) => current ? { ...current, screening_adjustment: updated.screening_adjustment, match_percentage: Math.max(0, Math.min(100, current.base_match_percentage + updated.screening_adjustment)) } : current); }} />
      <section className="grid gap-6 xl:grid-cols-[1fr_360px]">
        <div className="company-candidate-profile space-y-6">
          <Timeline
            title="Experiencia laboral"
            icon={BriefcaseBusiness}
            items={recentExperiences(candidate.experiences)}
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
                  <div className="mt-3"><StructuredJobText text={item.description} /></div>
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
          {!candidate.identity_hidden && [["drivingLicenses", "Licencias de conducción", candidate.driving_licenses], ["professionalCards", "Tarjetas profesionales", candidate.professional_cards]].filter(([, , rows]) => rows?.length).map(([kind, title]) => <section key={kind} className="surface-card p-5"><h2 className="font-bold mb-3">{title}</h2><ProfileCredentials kind={kind} drivingLicenses={candidate.driving_licenses || []} professionalCards={candidate.professional_cards || []} /></section>)}
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
                </p><div className="candidate-certificate-details">{TRAINING_TYPES[item.kind] && <span>{TRAINING_TYPES[item.kind]}</span>}{item.url?.startsWith("https://") && <a className="button-secondary button-sm" href={item.url} target="_blank" rel="noopener noreferrer">Ver documento ↗</a>}</div>
              </>
            )}
          />}
        </div>
        <aside className="space-y-5">
          {!candidate.identity_hidden && candidate.links?.length > 0 && <section className="surface-card p-5"><h2 className="mb-3 font-bold text-[var(--ink-strong)]">Enlaces profesionales</h2><ProfileLinks value={candidate.links} /></section>}
          {candidate.languages?.length > 0 && <section className="surface-card p-5"><h2 className="mb-3 font-bold">Idiomas</h2><LanguagesEditor value={candidate.languages} editing={false} /></section>}
          {candidate.skills?.length > 0 && <section className="surface-card p-5">
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
          </section>}
          {(candidate.preferred_modality || candidate.desired_salary) && <section className="surface-card p-5">
            <h2 className="font-bold text-[var(--ink-strong)]">Preferencias</h2>
            <dl className="mt-4 space-y-3 text-sm">
              {candidate.preferred_modality && <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Modalidad</dt>
                <dd className="font-semibold text-[var(--ink-strong)]">
                  {modalityLabels[candidate.preferred_modality] ||
                    candidate.preferred_modality ||
                    "Sin preferencia"}
                </dd>
              </div>}
              {candidate.desired_salary > 0 && <div className="flex justify-between gap-4">
                <dt className="text-[var(--muted)]">Aspiración</dt>
                <dd className="font-semibold text-[var(--ink-strong)]">
                  {candidate.desired_salary
                    ? `$${Number(candidate.desired_salary).toLocaleString("es-CO")}`
                    : "No definida"}
                </dd>
              </div>}
            </dl>
          </section>}
        </aside>
      </section>
    </div>
  );
}

function Timeline({ title, icon: Icon, items = [], render }) {
  if (!items?.length) return null;
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
          <p className="text-sm text-[var(--muted)]">Sin información</p>
        )}
      </div>
    </section>
  );
}
