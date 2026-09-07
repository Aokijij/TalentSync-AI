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
  UserRound,
} from "lucide-react";
import { useNavigate, useParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";

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
  const navigate = useNavigate();
  const [candidate, setCandidate] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get(`/profiles/candidates/${userId}`)
      .then(({ data }) => setCandidate(data))
      .catch((requestError) =>
        setError(
          getApiErrorMessage(requestError, "No fue posible cargar el perfil"),
        ),
      );
  }, [userId]);

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
        Volver al ranking
      </button>
      <section className="page-hero">
        <div className="flex flex-wrap items-start gap-5">
          <div className="grid h-16 w-16 place-items-center rounded-2xl bg-[var(--accent)]/10 text-[var(--accent)]">
            <UserRound size={30} />
          </div>
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
