import { useEffect, useMemo, useState } from "react";
import {
  Check,
  Flame,
  Minus,
  Search,
  UsersRound,
  RefreshCw,
  Send,
  UserRound,
} from "lucide-react";

import { api } from "../api/client.js";
import { CompatibilityBar } from "../components/CompatibilityBar.jsx";
import { languageLevelLabel } from "../constants/languages.js";
import { Link, useNavigate, useParams } from "react-router-dom";

export function CompanyCandidatesPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();

  const [candidates, setCandidates] = useState([]);
  const [job, setJob] = useState(null);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [invitingId, setInvitingId] = useState(null);

  const [query, setQuery] = useState("");

  async function load() {
    setError("");
    try {
      const [jobsResp, candidatesResp] = await Promise.all([
        api.get("/jobs").catch(() => ({ data: [] })),
        api
          .get(`/recommendations/jobs/${jobId}/candidates`)
          .catch(() => ({ data: [] })),
      ]);

      const foundJob =
        (jobsResp.data ?? []).find((j) => String(j.id) === String(jobId)) ??
        null;
      setJob(foundJob);
      setCandidates(candidatesResp.data ?? []);
    } catch (e) {
      setError(e?.response?.data?.detail || "No fue posible cargar candidatos");
    }
  }

  useEffect(() => {
    load();
  }, [jobId]);

  async function invite(candidate) {
    setError("");
    setMessage("");
    setInvitingId(candidate.user_id);
    try {
      await api.post(
        `/recommendations/jobs/${jobId}/candidates/${candidate.user_id}/invite`,
      );
      setCandidates((current) =>
        current.map((item) =>
          item.user_id === candidate.user_id
            ? { ...item, has_pending_invitation: true }
            : item,
        ),
      );
      setMessage(`Invitación enviada a ${candidate.name}.`);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "No fue posible enviar la invitación",
      );
    } finally {
      setInvitingId(null);
    }
  }

  const filtered = useMemo(() => {
    const term = query.toLowerCase().trim();
    if (!term) return candidates;
    return candidates.filter((c) =>
      `${c.name} ${c.email ?? ""} ${c.profession ?? ""} ${(c.skills ?? []).join(" ")}`
        .toLowerCase()
        .includes(term),
    );
  }, [candidates, query]);

  return (
    <div className="space-y-6">
      <section className="page-hero">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="section-kicker">Candidatos</p>
            <h1 className="mt-2 font-display text-3xl font-semibold">
              Aspirantes para {job?.title ?? `vacante #${jobId}`}
            </h1>
            <p className="mt-2 text-sm text-[var(--muted)]">
              Consulta quienes se postularon e invita a perfiles con al menos
              50% de compatibilidad.
            </p>
          </div>
          <span className="rounded-full border border-[var(--line)] px-3 py-1 text-[var(--muted)]">
            {candidates.length} recomendado{candidates.length === 1 ? "" : "s"}
          </span>
        </div>
      </section>

      {error && (
        <p className="rounded-[var(--radius-md)] border border-[var(--error)] bg-[var(--error)]/10 px-3 py-2 text-sm text-[var(--error)]">
          {error}
        </p>
      )}
      {message ? <p className="rounded-[var(--radius-md)] border border-[var(--success)] bg-[var(--success)]/10 px-3 py-2 text-sm text-[var(--success)]">{message}</p> : null}

      <section className="surface-card p-5">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-center gap-3">
            <Search size={18} className="text-[var(--muted)]" />
            <div>
              <h2 className="font-semibold text-[var(--ink)]">
                Filtrar por nombre o habilidad
              </h2>
              <p className="text-sm text-[var(--muted)]">
                Busca dentro de los candidatos recomendados para esta vacante.
              </p>
            </div>
          </div>

          <div className="flex w-full flex-col gap-3 sm:w-auto sm:flex-row sm:items-center">
            <label className="relative w-full sm:w-80">
              <input
                className="field-control input-md"
                placeholder="Buscar candidato..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </label>

            <button
              type="button"
              className="button-secondary w-auto hover-lift pressed focus-ring"
              onClick={load}
            >
              <RefreshCw size={15} />
              Actualizar
            </button>
          </div>
        </div>
      </section>

      <section className="surface-card overflow-hidden">
        <div className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-4">
          <Flame size={20} className="text-[var(--warning)]" />
          <div>
            <h2 className="font-semibold text-[var(--ink)]">
              Comparación de habilidades principales
            </h2>
            <p className="text-sm text-[var(--muted)]">
              Cada marca muestra si el perfil incluye una habilidad solicitada.
            </p>
          </div>
        </div>
        <CandidateHeatmap
          candidates={filtered}
          requiredSkills={job?.skills ?? []}
        />
      </section>

      <section className="surface-card">
        <div className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-4">
          <UsersRound size={20} className="text-[var(--accent)]" />
          <h2 className="font-semibold text-[var(--ink)]">
            Candidatos recomendados
          </h2>
        </div>

        <div className="divide-y divide-[var(--line)]">
          {filtered.map((candidate) => (
            <article
              key={candidate.user_id ?? candidate.name}
              className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_240px] md:items-center"
            >
              <div>
                <p className="font-semibold text-[var(--ink)]">
                  {candidate.name}
                </p>
                <p className="text-sm text-[var(--muted)]">
                  {candidate.email ?? "—"}
                </p>
                <p className="mt-1 text-sm text-[var(--muted)]">
                  {candidate.profession ?? "Perfil profesional"}
                </p>
                <p className="mt-2 text-xs text-[var(--muted)]">
                  Habilidades:{" "}
                  {(candidate.skills ?? []).join(", ") || "Sin habilidades"}
                </p>
                <p className="mt-2 text-xs text-[var(--muted)]">
                  Experiencia:{" "}
                  {candidate.experience_years
                    ? `${candidate.experience_years} año${candidate.experience_years === 1 ? "" : "s"}`
                    : candidate.experience_summary ||
                      "Sin experiencia registrada"}
                </p>
                {candidate.has_applied ? (
                  <Link
                    className="mt-3 inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline hover-lift"
                    to={`/empresa/candidatos/${candidate.user_id}?job=${jobId}`}
                  >
                    <UserRound size={15} />
                    Ver perfil completo
                  </Link>
                ) : (
                  <button
                    type="button"
                    className="button-primary button-sm mt-3"
                    disabled={candidate.has_pending_invitation || invitingId === candidate.user_id}
                    onClick={() => invite(candidate)}
                  >
                    <Send size={14} />
                    {candidate.has_pending_invitation
                      ? "Invitación enviada"
                      : invitingId === candidate.user_id
                        ? "Enviando…"
                        : "Invitar a postularse"}
                  </button>
                )}
              </div>
              <div className="space-y-3"><CompatibilityBar value={candidate.match_percentage} />{job?.languages?.length ? <div className="text-xs text-[var(--muted)]"><p className="mb-1 font-semibold">Idiomas solicitados</p>{job.languages.map((item) => { const actual = candidate.languages?.find((language) => language.name === item.name); return <p className="mt-1" key={item.name}><span className="capitalize">{item.name}</span>: mínimo {item.level} · Su nivel: {actual ? languageLevelLabel(actual.level) : "sin registrar"}</p>; })}</div> : null}</div>
            </article>
          ))}

          {filtered.length === 0 ? (
            <div className="px-5 py-12 text-center">
              <UsersRound className="mx-auto text-[var(--muted)]" />
              <p className="mt-3 font-semibold text-[var(--ink-strong)]">
                No hay aspirantes para esta vacante
              </p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Todavía no hay postulaciones ni perfiles externos con más del
                50% de compatibilidad{query ? " para esta búsqueda" : ""}.
              </p>
            </div>
          ) : null}
        </div>
      </section>

      <div>
        <button
          type="button"
          className="inline-flex items-center gap-2 text-sm font-semibold text-indigo-800 hover:underline"
          onClick={() => navigate("/empresa")}
        >
          ← Volver al inicio
        </button>
      </div>
    </div>
  );
}

function CandidateHeatmap({ candidates, requiredSkills }) {
  const skills = requiredSkills.slice(0, 6);
  const visible = candidates.slice(0, 12);
  const normalized = (value) =>
    String(value ?? "")
      .toLowerCase()
      .trim();
  const hasSkill = (candidate, skill) =>
    (candidate.skills ?? []).some(
      (item) => normalized(item) === normalized(skill),
    );
  if (!candidates.length)
    return (
      <p className="px-5 py-10 text-sm text-[var(--muted)]">
        El mapa aparecerá cuando exista al menos un aspirante recomendado para
        esta vacante.
      </p>
    );
  if (!skills.length)
    return (
      <p className="px-5 py-10 text-sm text-[var(--muted)]">
        La vacante todavía no tiene habilidades críticas detectadas.
      </p>
    );
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[760px] border-collapse text-sm">
        <thead>
          <tr className="text-left text-xs uppercase tracking-wide text-[var(--muted)]">
            <th className="px-5 py-3">Candidato</th>
            {skills.map((skill) => (
              <th key={skill} className="px-3 py-3 text-center">
                {skill}
              </th>
            ))}
            <th className="px-5 py-3 text-center">Compatibilidad</th>
          </tr>
        </thead>
        <tbody>
          {visible.map((candidate) => (
            <tr
              key={candidate.user_id}
              className="border-t border-[var(--line)]"
            >
              <td className="px-5 py-3">
                <p className="font-bold text-[var(--ink-strong)]">
                  {candidate.name}
                </p>
                <p className="text-xs text-[var(--muted)]">
                  {candidate.profession || "Perfil profesional"}
                </p>
              </td>
              {skills.map((skill) => {
                const matched = hasSkill(candidate, skill);
                return (
                  <td key={skill} className="px-2 py-2 text-center">
                    <span
                      className={`mx-auto grid h-10 w-10 place-items-center rounded-[var(--radius-md)] ${matched ? "bg-[var(--accent)] text-white" : "bg-[var(--surface-subtle)] text-[var(--muted)]"}`}
                      aria-label={`${skill}: ${matched ? "coincide" : "brecha"}`}
                    >
                      {matched ? <Check size={17} /> : <Minus size={16} />}
                    </span>
                  </td>
                );
              })}
              <td className="px-5 py-3">
                <div
                  className="mx-auto grid h-12 w-16 place-items-center rounded-[var(--radius-md)] font-bold text-white"
                  style={{
                    backgroundColor: `rgba(3, 105, 161, ${Math.max(0.3, candidate.match_percentage / 100)})`,
                  }}
                >
                  {Math.round(candidate.match_percentage)}%
                </div>
              </td>
            </tr>
          ))}
          {!visible.length ? (
            <tr>
              <td
                colSpan={skills.length + 2}
                className="px-5 py-10 text-center text-[var(--muted)]"
              >
                No hay candidatos para comparar.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
