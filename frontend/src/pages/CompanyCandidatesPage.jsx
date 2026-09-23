import { useEffect, useState } from "react";
import { Check, ChevronLeft, ChevronRight, Flame, Minus, RefreshCw, Search, Send, UserRound, UsersRound } from "lucide-react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { api } from "../api/client.js";
import { languageLevelLabel } from "../constants/languages.js";

const PAGE_SIZE = 10;

export function CompanyCandidatesPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [job, setJob] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [topCandidates, setTopCandidates] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [audience, setAudience] = useState("invite");
  const [query, setQuery] = useState("");
  const [refreshKey, setRefreshKey] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [invitingId, setInvitingId] = useState(null);

  useEffect(() => {
    api.get(`/jobs/${jobId}`).then(({ data }) => setJob(data)).catch(() => setJob(null));
  }, [jobId]);

  useEffect(() => {
    const timer = window.setTimeout(async () => {
      setLoading(true);
      setError("");
      try {
        const { data } = await api.get(`/recommendations/jobs/${jobId}/candidates-page`, {
          params: { audience, query: query.trim() || undefined, minimum_match: 80, limit: PAGE_SIZE, offset: (page - 1) * PAGE_SIZE },
        });
        setCandidates(data.items || []);
        setTopCandidates(data.top_candidates || []);
        setTotal(data.total || 0);
      } catch (requestError) {
        setError(requestError?.response?.data?.detail || "No fue posible cargar los candidatos");
      } finally {
        setLoading(false);
      }
    }, 250);
    return () => window.clearTimeout(timer);
  }, [audience, jobId, page, query, refreshKey]);

  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  async function invite(candidate) {
    setError("");
    setMessage("");
    setInvitingId(candidate.user_id);
    try {
      await api.post(`/recommendations/jobs/${jobId}/candidates/${candidate.user_id}/invite`);
      setCandidates((current) => current.map((item) => item.user_id === candidate.user_id ? { ...item, has_pending_invitation: true } : item));
      setMessage(`Invitación enviada a ${candidate.name}.`);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "No fue posible enviar la invitación");
    } finally {
      setInvitingId(null);
    }
  }

  const changeAudience = (next) => {
    setAudience(next);
    setPage(1);
    setQuery("");
  };

  return (
    <div className="space-y-6">
      <section className="page-hero">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div>
            <p className="section-kicker">Talento para esta vacante</p>
            <h1 className="mt-2 font-display text-3xl font-semibold">{job?.title ?? `Vacante #${jobId}`}</h1>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[var(--muted)]">Invita perfiles con 80% o más de compatibilidad y revisa por separado a quienes ya se postularon.</p>
          </div>
          <span className="rounded-full border border-[var(--line)] px-3 py-1 text-sm text-[var(--muted)]">{total} {audience === "invite" ? "por invitar" : "postulados"}</span>
        </div>
      </section>

      {error ? <p className="rounded-[var(--radius-md)] border border-[var(--error)] bg-[var(--error)]/10 px-3 py-2 text-sm text-[var(--error)]">{error}</p> : null}
      {message ? <p className="rounded-[var(--radius-md)] border border-[var(--success)] bg-[var(--success)]/10 px-3 py-2 text-sm text-[var(--success)]">{message}</p> : null}

      <section className="surface-card p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <p className="text-sm font-bold text-[var(--ink-strong)]">¿Qué grupo quieres revisar?</p>
            <div className="mt-2 flex flex-wrap gap-2" role="tablist" aria-label="Grupos de candidatos">
              <button type="button" role="tab" aria-selected={audience === "invite"} className={audience === "invite" ? "button-primary button-sm" : "button-secondary button-sm"} onClick={() => changeAudience("invite")}>Recomendados 80%+</button>
              <button type="button" role="tab" aria-selected={audience === "applied"} className={audience === "applied" ? "button-primary button-sm" : "button-secondary button-sm"} onClick={() => changeAudience("applied")}>Ya se postularon</button>
            </div>
          </div>
          <div className="flex w-full flex-col gap-2 sm:flex-row lg:w-auto">
            <label className="relative w-full sm:w-80"><Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-[var(--muted)]" /><input className="field-control !pl-10" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Nombre, profesión o habilidad" /></label>
            <button type="button" className="button-secondary" onClick={() => setRefreshKey((current) => current + 1)}><RefreshCw size={15} />Actualizar</button>
          </div>
        </div>
      </section>

      <section className="surface-card overflow-hidden !p-0">
        <div className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-4">
          <Flame size={20} className="text-[var(--warning)]" />
          <div><h2 className="font-semibold text-[var(--ink)]">Comparación rápida de los mejores perfiles</h2><p className="text-sm text-[var(--muted)]">Solo se muestran los cinco perfiles y las cinco habilidades principales.</p></div>
        </div>
        <CandidateHeatmap candidates={topCandidates} requiredSkills={job?.skills ?? []} />
      </section>

      <section className="surface-card overflow-hidden !p-0">
        <header className="flex items-center justify-between gap-3 border-b border-[var(--line)] px-5 py-4"><div className="flex items-center gap-3"><UsersRound size={20} className="text-[var(--accent)]" /><div><h2 className="font-semibold text-[var(--ink)]">{audience === "invite" ? "Perfiles para invitar" : "Personas postuladas"}</h2><p className="text-xs text-[var(--muted)]">Mostrando {total ? (page - 1) * PAGE_SIZE + 1 : 0}–{Math.min(page * PAGE_SIZE, total)} de {total}</p></div></div></header>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] border-collapse text-sm">
            <thead><tr className="bg-[var(--surface-subtle)] text-left text-xs uppercase tracking-wide text-[var(--muted)]"><th className="px-5 py-3">Candidato</th><th className="px-4 py-3">Compatibilidad</th><th className="px-4 py-3">Experiencia</th><th className="px-4 py-3">Habilidades destacadas</th><th className="px-4 py-3">Idiomas solicitados</th><th className="px-5 py-3 text-right">Acción</th></tr></thead>
            <tbody className="divide-y divide-[var(--line)]">
              {candidates.map((candidate) => <CandidateRow key={candidate.user_id} candidate={candidate} job={job} jobId={jobId} inviting={invitingId === candidate.user_id} onInvite={() => invite(candidate)} />)}
            </tbody>
          </table>
        </div>
        {loading ? <p className="px-5 py-12 text-center text-sm text-[var(--muted)]">Cargando candidatos…</p> : null}
        {!loading && !candidates.length ? <div className="px-5 py-14 text-center"><UsersRound className="mx-auto text-[var(--muted)]" /><p className="mt-3 font-semibold text-[var(--ink-strong)]">No hay resultados en este grupo</p><p className="mt-1 text-sm text-[var(--muted)]">{audience === "invite" ? "No encontramos perfiles con 80% o más de compatibilidad." : "Todavía no hay postulaciones para esta vacante."}</p></div> : null}
        {total > PAGE_SIZE ? <nav className="flex items-center justify-between border-t border-[var(--line)] px-5 py-4" aria-label="Paginación de candidatos"><button type="button" className="button-secondary button-sm" disabled={page === 1} onClick={() => setPage((current) => current - 1)}><ChevronLeft size={15} />Anterior</button><span className="text-sm font-semibold text-[var(--muted)]">Página {page} de {pages}</span><button type="button" className="button-secondary button-sm" disabled={page >= pages} onClick={() => setPage((current) => current + 1)}>Siguiente<ChevronRight size={15} /></button></nav> : null}
      </section>

      <button type="button" className="inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover:underline" onClick={() => navigate("/empresa/vacantes")}>← Volver a mis vacantes</button>
    </div>
  );
}

function CandidateRow({ candidate, job, jobId, inviting, onInvite }) {
  const required = (job?.skills || []).map((skill) => skill.toLowerCase());
  const matching = (candidate.skills || []).filter((skill) => required.includes(skill.toLowerCase())).slice(0, 4);
  return (
    <tr className="align-top hover:bg-[var(--surface-subtle)]">
      <td className="px-5 py-4"><p className="font-bold text-[var(--ink-strong)]">{candidate.name}</p><p className="mt-1 text-xs text-[var(--muted)]">{candidate.profession || "Perfil profesional"}</p></td>
      <td className="px-4 py-4"><span className="inline-flex min-w-16 justify-center rounded-full bg-[var(--accent)]/10 px-3 py-1.5 font-bold text-[var(--accent)]">{Math.round(candidate.match_percentage)}%</span></td>
      <td className="px-4 py-4 text-[var(--muted)]">{candidate.experience_years ? `${candidate.experience_years} año${candidate.experience_years === 1 ? "" : "s"}` : candidate.experience_summary || "Sin registrar"}</td>
      <td className="px-4 py-4"><div className="flex max-w-64 flex-wrap gap-1.5">{matching.length ? matching.map((skill) => <span key={skill} className="rounded-md border border-[var(--line)] px-2 py-1 text-xs">{skill}</span>) : <span className="text-xs text-[var(--muted)]">Sin coincidencias directas</span>}</div></td>
      <td className="px-4 py-4 text-xs text-[var(--muted)]">{job?.languages?.length ? job.languages.map((item) => { const actual = candidate.languages?.find((language) => language.name === item.name); return <p key={item.name} className="mb-1"><span className="capitalize font-semibold">{item.name}</span>: {actual ? languageLevelLabel(actual.level) : "sin registrar"} <span className="text-[var(--muted)]">(mín. {languageLevelLabel(item.level)})</span></p>; }) : "No se solicitaron idiomas"}</td>
      <td className="px-5 py-4 text-right">{candidate.has_applied ? <Link className="button-secondary button-sm inline-flex" to={`/empresa/candidatos/${candidate.user_id}?job=${jobId}`}><UserRound size={14} />Ver perfil</Link> : <button type="button" className="button-primary button-sm" disabled={candidate.has_pending_invitation || inviting} onClick={onInvite}><Send size={14} />{candidate.has_pending_invitation ? "Invitación enviada" : inviting ? "Enviando…" : "Invitar"}</button>}</td>
    </tr>
  );
}

function CandidateHeatmap({ candidates, requiredSkills }) {
  const skills = requiredSkills.slice(0, 5);
  const normalized = (value) => String(value ?? "").toLowerCase().trim();
  const hasSkill = (candidate, skill) => (candidate.skills ?? []).some((item) => normalized(item) === normalized(skill));
  if (!candidates.length || !skills.length) return <p className="px-5 py-10 text-sm text-[var(--muted)]">La comparación aparecerá cuando existan perfiles y habilidades suficientes.</p>;
  return (
    <div className="overflow-x-auto"><table className="w-full min-w-[720px] border-collapse text-sm"><thead><tr className="text-left text-xs uppercase tracking-wide text-[var(--muted)]"><th className="px-5 py-3">Candidato</th>{skills.map((skill) => <th key={skill} className="px-3 py-3 text-center">{skill}</th>)}<th className="px-5 py-3 text-center">Afinidad</th></tr></thead><tbody>{candidates.map((candidate) => <tr key={candidate.user_id} className="border-t border-[var(--line)]"><td className="px-5 py-3"><p className="font-bold">{candidate.name}</p><p className="text-xs text-[var(--muted)]">{candidate.profession || "Perfil profesional"}</p></td>{skills.map((skill) => { const matched = hasSkill(candidate, skill); return <td key={skill} className="px-2 py-2 text-center"><span className={`mx-auto grid h-9 w-9 place-items-center rounded-lg ${matched ? "bg-[var(--accent)] text-white" : "bg-[var(--surface-subtle)] text-[var(--muted)]"}`}>{matched ? <Check size={16} /> : <Minus size={15} />}</span></td>; })}<td className="px-5 py-3 text-center"><strong className="text-[var(--accent)]">{Math.round(candidate.match_percentage)}%</strong></td></tr>)}</tbody></table></div>
  );
}
