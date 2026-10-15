import { loadCandidatePages } from "../utils/candidateRequests.js";
import { experienceDuration } from "../utils/experienceDates.js";
import { Pagination } from "../components/Pagination.jsx";
import { useEffect, useState } from "react";
import { ArrowRight, BriefcaseBusiness, Check, RefreshCw, Search, Send, UsersRound } from "lucide-react";
import { Link, useLocation, useSearchParams } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { matchingSkills } from "../utils/talentSearch.js";
import { languageLevelLabel } from "../constants/languages.js";
import { ApplicationAnswersModal } from "../components/ApplicationAnswersModal.jsx";

export function CompanyTalentPage() {
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const [jobs, setJobs] = useState([]);
  const [jobSearch, setJobSearch] = useState(""), [jobOffset, setJobOffset] = useState(0), [jobTotal, setJobTotal] = useState(0), [selectedSnapshot, setSelectedSnapshot] = useState(null), [pending, setPending] = useState(0);
  const [selectedJobId, setSelectedJobId] = useState(searchParams.get("job") || "");
  const [candidates, setCandidates] = useState([]);
  const [page, setPage] = useState(Math.max(1, Math.min(100000, Math.floor(Number(searchParams.get("page"))) || 1))), [total, setTotal] = useState(0);
  const pageSize = 9;
  const [query, setQuery] = useState(searchParams.get("query") || "");
  const [audience, setAudience] = useState(searchParams.get("audience") || "new");
  const [minMatch, setMinMatch] = useState(Math.max(0, Math.min(100, Number(searchParams.get("min") ?? 50) || 0)));
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [loading, setLoading] = useState(false);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [invitation, setInvitation] = useState(null);
  const [sending, setSending] = useState(false);
  const [reviewApplication, setReviewApplication] = useState(null);
  const selectedJob = jobs.find((job) => String(job.id) === selectedJobId) || (String(selectedSnapshot?.id) === selectedJobId ? selectedSnapshot : null);

  useEffect(() => {
    const next = { audience, min: String(minMatch), page: String(page) };
    if (selectedJobId) next.job = selectedJobId;
    if (query) next.query = query;
    setSearchParams(next, { replace: true });
  }, [audience, minMatch, query, selectedJobId, page, setSearchParams]);

  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      try {
        const { data } = await api.get("/jobs/mine/choices", { params: { search: jobSearch, offset: jobOffset, limit: 50 }, signal: controller.signal });
        if (controller.signal.aborted) return;
        setJobs((current) => jobOffset ? [...current, ...data.items] : data.items); setJobTotal(data.total);
        if (selectedJobId && !data.items.some((job) => String(job.id) === selectedJobId) && !selectedSnapshot) {
          const response = await api.get(`/jobs/${selectedJobId}`, { signal: controller.signal });
          if (!controller.signal.aborted && response.data.company_id === data.company_id) setSelectedSnapshot(response.data);
        }
      } catch (failure) { if (!controller.signal.aborted) setError(getApiErrorMessage(failure, "No pudimos cargar tus vacantes.")); }
      finally { if (!controller.signal.aborted) setLoadingJobs(false); }
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [jobSearch, jobOffset]);

  useEffect(() => {
    const controller = new AbortController();
    setCandidates([]); setMessage(""); setInvitation(null); setPending(0);
    if (!selectedJobId) { setLoading(false); return; }
    setError(""); setLoading(true);
    const timer = setTimeout(async () => {
      try {
        await loadCandidatePages({ signal: controller.signal, request: () => api.get(`/recommendations/jobs/${selectedJobId}/candidates-page`, { params: { audience: audience === "new" ? "invite" : "applied", query, minimum_match: minMatch, limit: pageSize, offset: (page - 1) * pageSize }, signal: controller.signal, __skipRetry: true }), onPage: (data) => { setCandidates(data.items); setTotal(data.total); setPending(data.pending || 0); setLoading(false); if (!data.pending && page > Math.max(1, Math.ceil(data.total / pageSize))) setPage(Math.max(1, Math.ceil(data.total / pageSize))); } });
      } catch (failure) { if (!controller.signal.aborted) { setPending(0); setError(getApiErrorMessage(failure, "No pudimos cargar los candidatos. Pulsa Actualizar para volver a intentar.")); } }
      finally { if (!controller.signal.aborted) setLoading(false); }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [selectedJobId, refreshVersion, query, audience, minMatch, page]);

  const results = candidates;

  async function sendInvitation() {
    if (!invitation || !selectedJob) return;
    setSending(true);
    setError("");
    try {
      await api.post(`/recommendations/jobs/${selectedJob.id}/candidates/${invitation.user_id}/invite`);
      setCandidates((current) => current.map((candidate) => candidate.user_id === invitation.user_id ? { ...candidate, has_pending_invitation: true } : candidate));
      setMessage(`Invitación enviada a ${invitation.name} para ${selectedJob.title}. Recibirá una notificación y podrá decidir si se postula.`);
      setInvitation(null);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No pudimos enviar la invitación."));
      setInvitation(null);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader kicker="Buscar talento" title="Encuentra personas para tu equipo" description="Elige una vacante, conoce personas que encajan con el cargo e invítalas a postularse." />

      {error ? <p role="alert" className="surface-card !border-[var(--error)] text-sm text-[var(--error)]">{error}</p> : null}
      {message ? <p role="status" className="surface-card flex items-start gap-3 !border-[var(--success)] text-sm text-[var(--success)]"><Check size={18} className="shrink-0" />{message}</p> : null}

      <section className="surface-card !p-6 sm:!p-7">
        <div className="flex items-start gap-3">
          <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-[var(--accent)] text-sm font-bold text-white">1</span>
          <div><h2 className="text-xl font-bold">¿Para qué cargo buscas candidatos?</h2><p className="mt-1 text-sm text-[var(--muted)]">La búsqueda se hará únicamente para la vacante que elijas.</p></div>
        </div>
        <label className="mt-4 block text-xs text-[var(--muted)]">Buscar entre mis vacantes<input className="field-control mt-2" placeholder="Nombre del cargo" value={jobSearch} onChange={(event) => { setJobSearch(event.target.value); setJobOffset(0); }} /></label>
        {loadingJobs ? <p className="mt-5 text-sm text-[var(--muted)]">Cargando tus vacantes…</p> : jobs.length ? (
          <div className="mt-5 sm:ml-12">
            <label className="block max-w-2xl text-sm font-semibold">Vacante
              <select className="field-control mt-2" value={selectedJobId} disabled={sending} onChange={(event) => { setSelectedSnapshot(jobs.find((job) => String(job.id) === event.target.value) || null); setSelectedJobId(event.target.value); setQuery(""); setPage(1); }}>
                <option value="">Selecciona una vacante…</option>
                {selectedJob && !jobs.some((job) => job.id === selectedJob.id) && <option value={selectedJob.id}>{selectedJob.title}</option>}
                {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}{job.status === "paused" ? " · Pausada" : ""}</option>)}
              </select>
            </label>
            {jobs.length < jobTotal && <button type="button" className="button-secondary button-sm mt-3" onClick={() => setJobOffset(jobs.length)}>Cargar más vacantes ({jobTotal - jobs.length})</button>}
            {selectedJob ? <p className="mt-3 flex items-start gap-2 text-xs text-[var(--muted)]"><BriefcaseBusiness size={15} className="shrink-0" />{selectedJob.skills?.length ? `Buscamos experiencia en ${selectedJob.skills.slice(0, 3).join(", ")}${selectedJob.skills.length > 3 ? " y otras habilidades" : ""}.` : "Compararemos la experiencia y la formación con los requisitos del cargo."}</p> : null}
          </div>
        ) : !error ? <div className="mt-5 sm:ml-12"><p className="text-sm text-[var(--muted)]">{jobSearch ? "No hay vacantes con ese nombre. Prueba otra búsqueda." : "Publica una vacante para empezar a buscar personas para tu equipo."}</p><Link className="button-primary mt-4" to="/empresa/vacantes">Gestionar vacantes <ArrowRight size={16} /></Link></div> : null}
      </section>

      {selectedJob ? (
        <section className="space-y-5" aria-busy={loading}>
          <div className="flex items-start gap-3 px-1">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-[var(--line)] bg-[var(--surface)] text-sm font-bold text-[var(--accent)]">2</span>
            <div className="min-w-0"><h2 className="text-xl font-bold">Conoce a los candidatos</h2><p className="mt-1 text-sm text-[var(--muted)]">Para <strong className="text-[var(--ink-strong)]">{selectedJob.title}</strong>. Ordenados de mayor a menor coincidencia con el cargo.</p></div>
          </div>
          {pending > 0 && <p role="status" className="text-sm text-[var(--muted)]">Actualizando {pending} compatibilidades pendientes. Los resultados disponibles se pueden revisar mientras termina.</p>}
          <div className="surface-card !p-4 sm:!p-5">
            <div className="flex flex-wrap gap-2 border-b border-[var(--line)] pb-4" role="group" aria-label="Tipo de candidatos">
              {[{ value: "new", label: "Personas para invitar" }, { value: "applied", label: "Ya se postularon" }].map((tab) => <button key={tab.value} type="button" aria-pressed={audience === tab.value} className={`${audience === tab.value ? "button-primary" : "button-secondary"} button-sm`} onClick={() => { setAudience(tab.value); setPage(1); }}>{tab.label}</button>)}
            </div>
            <div className="mt-4 grid items-end gap-4 sm:grid-cols-[1fr_180px_auto]">
              <label className="block text-xs font-semibold text-[var(--muted)]">Nombre, profesión o habilidad
                <span className="relative mt-2 block"><Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2" /><input className="field-control !pl-10" value={query} onChange={(event) => { setQuery(event.target.value); setPage(1); }} placeholder="Ej. servicio al cliente o administración" /></span>
              </label>
              <label className="block text-xs font-semibold text-[var(--muted)]">Porcentaje mínimo
                <select className="field-control mt-2" value={minMatch} onChange={(event) => { setMinMatch(Number(event.target.value)); setPage(1); }}>{[0, 50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value ? `${value}% o más` : "Cualquier porcentaje"}</option>)}</select>
              </label>
              <button type="button" className="button-secondary" onClick={() => setRefreshVersion((value) => value + 1)} disabled={loading || sending}><RefreshCw size={16} />Actualizar</button>
            </div>
          </div>

          {loading ? <div className="surface-card py-12 text-center text-sm text-[var(--muted)]">Buscando candidatos para {selectedJob.title}…</div> : error && !candidates.length ? null : (
            <>
              <p className="px-1 text-sm text-[var(--muted)]">{total} {total === 1 ? "persona" : "personas"} {audience === "new" ? "para invitar" : total === 1 ? "que ya se postuló" : "que ya se postularon"}</p>
              <div className="talent-results-grid">
                {results.map((candidate) => <TalentCard key={candidate.user_id} candidate={candidate} job={selectedJob} sending={sending} returnTo={`${location.pathname}${location.search}`} onInvite={() => setInvitation(candidate)} onReview={() => setReviewApplication(candidate)} />)}
              </div>
              <Pagination page={page} pages={Math.max(1, Math.ceil(total / pageSize))} total={total} pageSize={pageSize} onChange={setPage} label="Páginas de candidatos" />
              {!results.length ? <div className="surface-card !py-10 text-center"><UsersRound className="mx-auto text-[var(--accent)]" size={30} /><h3 className="mt-3 font-bold">{audience === "new" ? "No hay personas para invitar con estos filtros" : "No hay postulaciones con estos filtros"}</h3><p className="mx-auto mt-2 max-w-md text-sm text-[var(--muted)]">{audience === "new" ? "Prueba otra búsqueda o revisa a las personas que ya se postularon. Los nuevos candidatos deben tener al menos 50% de coincidencia para recibir una invitación." : "Prueba otra búsqueda o selecciona cualquier porcentaje para ver todas las postulaciones."}</p><button type="button" className="button-secondary mt-4" onClick={() => { setQuery(""); setMinMatch(audience === "new" ? 50 : 0); setPage(1); }}>Limpiar filtros</button></div> : null}
              {audience === "new" && results.length ? <p className="px-1 text-xs leading-5 text-[var(--muted)]">El perfil completo estará disponible si la persona se postula. La invitación no inicia una contratación.</p> : null}
            </>
          )}
        </section>
      ) : jobs.length ? <div className="rounded-2xl border border-dashed border-[var(--line)] px-6 py-10 text-center"><Search className="mx-auto text-[var(--accent)]" size={30} /><h2 className="mt-3 text-lg font-bold">Empieza eligiendo una vacante</h2><p className="mt-2 text-sm text-[var(--muted)]">Aquí aparecerán las personas que puedes invitar para ese cargo.</p></div> : null}

      <ConfirmModal open={Boolean(invitation)} title="¿Enviar invitación?" description={`${invitation?.name || "Esta persona"} recibirá una notificación para conocer la vacante ${selectedJob?.title || "seleccionada"} y decidir si quiere postularse.`} confirmLabel="Enviar invitación" loading={sending} onConfirm={sendInvitation} onClose={() => { if (!sending) setInvitation(null); }} />
      <ApplicationAnswersModal application={reviewApplication} candidateName={reviewApplication?.name} onClose={() => setReviewApplication(null)} onSaved={() => setRefreshVersion((value) => value + 1)} />
    </div>
  );
}

function TalentCard({ candidate, job, sending, returnTo, onInvite, onReview }) {
  const skills = matchingSkills(candidate.skills, job.skills);
  const initials = candidate.name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("");
  return (
    <article className="surface-card talent-card">
      <div className="flex items-start gap-3">
        <span aria-hidden="true" className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[var(--accent)]/10 font-bold text-[var(--accent)]">{initials}</span>
        <div className="min-w-0"><h3 className="text-lg font-bold">{candidate.name}</h3><p className="mt-1 text-sm text-[var(--muted)]">{candidate.profession || "Perfil profesional"}</p></div>
      </div>
      <div className="talent-match">
        <div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold">Coincidencia con el cargo</span><strong className="text-xl text-[var(--accent)]">{Math.round(candidate.match_percentage)}%</strong></div>
        <p className="mt-1 text-xs text-[var(--muted)]">Según sus habilidades, experiencia, formación{job.languages?.length ? " e idiomas" : ""}.</p>
        {candidate.has_applied ? <p className="mt-2 text-xs font-semibold text-[var(--muted)]">Base {Math.round(candidate.base_match_percentage ?? candidate.match_percentage)}% · valoración manual {candidate.screening_adjustment > 0 ? "+" : ""}{candidate.screening_adjustment || 0} · final {Math.round(candidate.match_percentage)}%</p> : null}
      </div>
      <div className="talent-facts">{candidate.location_fit?.message && <p className={`talent-location ${candidate.location_fit.status}`}><strong>Ubicación y movilidad</strong>{candidate.location_fit.message}{candidate.location_fit.factor < 1 && <small>Afinidad profesional: {Math.round(candidate.professional_match_percentage)}% · con disponibilidad: {Math.round(candidate.match_percentage)}%</small>}</p>}
        {candidate.identity_hidden && <p className="text-xs font-semibold text-[var(--accent)]">Identidad protegida hasta la entrevista</p>}
        <details className="talent-details"><summary>Idiomas, evidencias y habilidades por reforzar</summary><div className="mt-2 space-y-2">
        {candidate.related_skills?.map((row) => <p className="text-xs text-[var(--muted)]" key={row.skill}>Base para aprender {row.skill}: {row.foundations.join(", ")} · aún sin acreditar</p>)}
        {candidate.validated_foundations?.map((row, index) => <p className="text-xs text-[var(--success)]" key={index}>Fundamentos evaluados: {row.skill} · {row.score}%</p>)}
        {job.languages?.length ? <div><p className="text-xs font-semibold text-[var(--muted)]">Idiomas para este cargo</p>{job.languages.map((item) => { const actual = candidate.languages?.find((language) => language.name === item.name); return <p key={item.name} className="mt-1 text-xs text-[var(--muted)]"><span className="capitalize font-semibold">{item.name}</span>: solicita {languageLevelLabel(item.level)} · Candidato: {actual ? languageLevelLabel(actual.level) : "sin registrar"}</p>; })}</div> : null}
        </div></details>
        <p className="text-sm text-[var(--muted)]">{experienceDuration(candidate.experience_months)}</p>
        <div><p className="text-xs font-semibold text-[var(--muted)]">Habilidades que coinciden</p><div className="mt-2 flex flex-wrap gap-2">{skills.length ? skills.slice(0, 4).map((skill) => <span key={skill} className="inline-flex items-center gap-1 rounded-lg border border-[var(--line)] px-2 py-1 text-xs text-[var(--ink-strong)]"><Check size={12} className="text-[var(--success)]" />{skill}</span>) : <p className="text-xs text-[var(--muted)]">La coincidencia se basa en otros aspectos del perfil.</p>}{skills.length > 4 ? <span className="py-1 text-xs text-[var(--muted)]">+{skills.length - 4} más</span> : null}</div></div>
      </div>
      <div className="mt-auto border-t border-[var(--line)] pt-4">
        {candidate.has_applied ? <div className="grid gap-2">{candidate.identity_hidden ? <Link className="button-secondary w-full" state={{ returnTo }} to={`/empresa/candidatos/${candidate.user_id}?job=${job.id}`}>Ver perfil anónimo</Link> : <Link className="button-secondary w-full" state={{ returnTo }} to={`/empresa/candidatos/${candidate.user_id}?job=${job.id}`}>Ver perfil del candidato <ArrowRight size={16} /></Link>}{candidate.screening_answers?.length ? <button type="button" className="button-outline w-full" onClick={onReview}>Ver respuestas y valorar</button> : null}</div> : <button type="button" className="button-primary w-full" disabled={candidate.has_pending_invitation || sending || candidate.match_percentage < 50 || candidate.location_fit?.invitation_allowed === false} onClick={onInvite}><Send size={16} />{candidate.has_pending_invitation ? "Invitación enviada" : "Invitar a postularse"}</button>}
        <p className="mt-2 text-center text-xs text-[var(--muted)]">{candidate.identity_hidden && candidate.has_applied ? "Compara habilidades y resultados antes de avanzar a entrevista." : candidate.has_applied ? "Ya puedes consultar su perfil completo." : candidate.has_pending_invitation ? "Estamos esperando que decida si desea postularse." : "Le enviaremos la vacante. Tú decides después a quién contratar."}</p>
      </div>
    </article>
  );
}
