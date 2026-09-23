import { useEffect, useMemo, useState } from "react";
import { ArrowRight, BriefcaseBusiness, Check, RefreshCw, Search, Send, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { matchingSkills, searchTalent } from "../utils/talentSearch.js";
import { languageLevelLabel } from "../constants/languages.js";

export function CompanyTalentPage() {
  const [jobs, setJobs] = useState([]);
  const [selectedJobId, setSelectedJobId] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [query, setQuery] = useState("");
  const [audience, setAudience] = useState("new");
  const [minMatch, setMinMatch] = useState(50);
  const [loadingJobs, setLoadingJobs] = useState(true);
  const [loading, setLoading] = useState(false);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [invitation, setInvitation] = useState(null);
  const [sending, setSending] = useState(false);
  const selectedJob = jobs.find((job) => String(job.id) === selectedJobId);

  useEffect(() => {
    let cancelled = false;
    async function loadJobs() {
      try {
        const [{ data: company }, { data: allJobs }] = await Promise.all([
          api.get("/companies/me"),
          api.get("/jobs", { params: { status: "" } }),
        ]);
        if (!cancelled) setJobs(allJobs.filter((job) => job.company_id === company.id && job.status !== "filled"));
      } catch (requestError) {
        if (!cancelled) setError(getApiErrorMessage(requestError, "No pudimos cargar tus vacantes. Intenta recargar la página."));
      } finally {
        if (!cancelled) setLoadingJobs(false);
      }
    }
    loadJobs();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setCandidates([]);
    setMessage("");
    setInvitation(null);
    if (!selectedJobId) { setLoading(false); return; }
    setError("");
    setLoading(true);
    api.get(`/recommendations/jobs/${selectedJobId}/candidates`)
      .then(({ data }) => { if (!cancelled) setCandidates(data); })
      .catch((requestError) => {
        if (!cancelled) setError(getApiErrorMessage(requestError, "No pudimos cargar los candidatos. Pulsa Actualizar para volver a intentar."));
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [selectedJobId, refreshVersion]);

  const results = useMemo(() => searchTalent(candidates, { query, audience, minMatch }), [candidates, query, audience, minMatch]);

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
        {loadingJobs ? <p className="mt-5 text-sm text-[var(--muted)]">Cargando tus vacantes…</p> : jobs.length ? (
          <div className="mt-5 sm:ml-12">
            <label className="block max-w-2xl text-sm font-semibold">Vacante
              <select className="field-control mt-2" value={selectedJobId} disabled={sending} onChange={(event) => { setSelectedJobId(event.target.value); setQuery(""); }}>
                <option value="">Selecciona una vacante…</option>
                {jobs.map((job) => <option key={job.id} value={job.id}>{job.title}{job.status === "paused" ? " · Pausada" : ""}</option>)}
              </select>
            </label>
            {selectedJob ? <p className="mt-3 flex items-start gap-2 text-xs text-[var(--muted)]"><BriefcaseBusiness size={15} className="shrink-0" />{selectedJob.skills?.length ? `Buscamos experiencia en ${selectedJob.skills.slice(0, 3).join(", ")}${selectedJob.skills.length > 3 ? " y otras habilidades" : ""}.` : "Compararemos la experiencia y la formación con los requisitos del cargo."}</p> : null}
          </div>
        ) : !error ? <div className="mt-5 sm:ml-12"><p className="text-sm text-[var(--muted)]">Publica una vacante para empezar a buscar personas para tu equipo.</p><Link className="button-primary mt-4" to="/empresa/vacantes">Gestionar vacantes <ArrowRight size={16} /></Link></div> : null}
      </section>

      {selectedJob ? (
        <section className="space-y-5" aria-busy={loading}>
          <div className="flex items-start gap-3 px-1">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full border border-[var(--line)] bg-[var(--surface)] text-sm font-bold text-[var(--accent)]">2</span>
            <div className="min-w-0"><h2 className="text-xl font-bold">Conoce a los candidatos</h2><p className="mt-1 text-sm text-[var(--muted)]">Para <strong className="text-[var(--ink-strong)]">{selectedJob.title}</strong>. Ordenados de mayor a menor coincidencia con el cargo.</p></div>
          </div>
          <div className="surface-card !p-4 sm:!p-5">
            <div className="flex flex-wrap gap-2 border-b border-[var(--line)] pb-4" role="group" aria-label="Tipo de candidatos">
              {[{ value: "new", label: "Personas para invitar" }, { value: "applied", label: "Ya se postularon" }].map((tab) => <button key={tab.value} type="button" aria-pressed={audience === tab.value} className={`${audience === tab.value ? "button-primary" : "button-secondary"} button-sm`} onClick={() => setAudience(tab.value)}>{tab.label}</button>)}
            </div>
            <div className="mt-4 grid items-end gap-4 sm:grid-cols-[1fr_180px_auto]">
              <label className="block text-xs font-semibold text-[var(--muted)]">Nombre, profesión o habilidad
                <span className="relative mt-2 block"><Search size={17} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2" /><input className="field-control !pl-10" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Ej. servicio al cliente o administración" /></span>
              </label>
              <label className="block text-xs font-semibold text-[var(--muted)]">Porcentaje mínimo
                <select className="field-control mt-2" value={minMatch} onChange={(event) => setMinMatch(Number(event.target.value))}>{[0, 50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value ? `${value}% o más` : "Cualquier porcentaje"}</option>)}</select>
              </label>
              <button type="button" className="button-secondary" onClick={() => setRefreshVersion((value) => value + 1)} disabled={loading || sending}><RefreshCw size={16} />Actualizar</button>
            </div>
          </div>

          {loading ? <div className="surface-card py-12 text-center text-sm text-[var(--muted)]">Buscando candidatos para {selectedJob.title}…</div> : error && !candidates.length ? null : (
            <>
              <p className="px-1 text-sm text-[var(--muted)]">{results.length} {results.length === 1 ? "persona" : "personas"} {audience === "new" ? "para invitar" : results.length === 1 ? "que ya se postuló" : "que ya se postularon"}</p>
              <div className="grid gap-4 lg:grid-cols-2">
                {results.map((candidate) => <TalentCard key={candidate.user_id} candidate={candidate} job={selectedJob} sending={sending} onInvite={() => setInvitation(candidate)} />)}
              </div>
              {!results.length ? <div className="surface-card !py-10 text-center"><UsersRound className="mx-auto text-[var(--accent)]" size={30} /><h3 className="mt-3 font-bold">{audience === "new" ? "No hay personas para invitar con estos filtros" : "No hay postulaciones con estos filtros"}</h3><p className="mx-auto mt-2 max-w-md text-sm text-[var(--muted)]">{audience === "new" ? "Prueba otra búsqueda o revisa a las personas que ya se postularon. Los nuevos candidatos deben tener al menos 50% de coincidencia para recibir una invitación." : "Prueba otra búsqueda o selecciona cualquier porcentaje para ver todas las postulaciones."}</p><button type="button" className="button-secondary mt-4" onClick={() => { setQuery(""); setMinMatch(audience === "new" ? 50 : 0); }}>Limpiar filtros</button></div> : null}
              {audience === "new" && results.length ? <p className="px-1 text-xs leading-5 text-[var(--muted)]">El perfil completo estará disponible si la persona se postula. La invitación no inicia una contratación.</p> : null}
            </>
          )}
        </section>
      ) : jobs.length ? <div className="rounded-2xl border border-dashed border-[var(--line)] px-6 py-10 text-center"><Search className="mx-auto text-[var(--accent)]" size={30} /><h2 className="mt-3 text-lg font-bold">Empieza eligiendo una vacante</h2><p className="mt-2 text-sm text-[var(--muted)]">Aquí aparecerán las personas que puedes invitar para ese cargo.</p></div> : null}

      <ConfirmModal open={Boolean(invitation)} title="¿Enviar invitación?" description={`${invitation?.name || "Esta persona"} recibirá una notificación para conocer la vacante ${selectedJob?.title || "seleccionada"} y decidir si quiere postularse.`} confirmLabel="Enviar invitación" loading={sending} onConfirm={sendInvitation} onClose={() => { if (!sending) setInvitation(null); }} />
    </div>
  );
}

function TalentCard({ candidate, job, sending, onInvite }) {
  const skills = matchingSkills(candidate.skills, job.skills);
  const initials = candidate.name.split(" ").filter(Boolean).slice(0, 2).map((part) => part[0]).join("");
  return (
    <article className="surface-card flex flex-col !p-5 sm:!p-6">
      <div className="flex items-start gap-3">
        <span aria-hidden="true" className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-[var(--accent)]/10 font-bold text-[var(--accent)]">{initials}</span>
        <div className="min-w-0"><h3 className="text-lg font-bold">{candidate.name}</h3><p className="mt-1 text-sm text-[var(--muted)]">{candidate.profession || "Perfil profesional"}</p></div>
      </div>
      <div className="mt-5 rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
        <div className="flex items-center justify-between gap-3"><span className="text-sm font-semibold">Coincidencia con el cargo</span><strong className="text-xl text-[var(--accent)]">{Math.round(candidate.match_percentage)}%</strong></div>
        <p className="mt-1 text-xs text-[var(--muted)]">Según sus habilidades, experiencia, formación{job.languages?.length ? " e idiomas" : ""}.</p>
      </div>
      <div className="mb-5 mt-4 space-y-3">
        {job.languages?.length ? <div><p className="text-xs font-semibold text-[var(--muted)]">Idiomas para este cargo</p>{job.languages.map((item) => { const actual = candidate.languages?.find((language) => language.name === item.name); return <p key={item.name} className="mt-1 text-xs text-[var(--muted)]"><span className="capitalize font-semibold">{item.name}</span>: solicita {languageLevelLabel(item.level)} · Candidato: {actual ? languageLevelLabel(actual.level) : "sin registrar"}</p>; })}</div> : null}
        <p className="text-sm text-[var(--muted)]">{candidate.experience_years ? `${candidate.experience_years} ${candidate.experience_years === 1 ? "año" : "años"} de experiencia registrada` : candidate.experience_summary || "Experiencia no especificada"}</p>
        <div><p className="text-xs font-semibold text-[var(--muted)]">Habilidades que coinciden</p><div className="mt-2 flex flex-wrap gap-2">{skills.length ? skills.slice(0, 4).map((skill) => <span key={skill} className="inline-flex items-center gap-1 rounded-lg border border-[var(--line)] px-2 py-1 text-xs text-[var(--ink-strong)]"><Check size={12} className="text-[var(--success)]" />{skill}</span>) : <p className="text-xs text-[var(--muted)]">La coincidencia se basa en otros aspectos del perfil.</p>}{skills.length > 4 ? <span className="py-1 text-xs text-[var(--muted)]">+{skills.length - 4} más</span> : null}</div></div>
      </div>
      <div className="mt-auto border-t border-[var(--line)] pt-4">
        {candidate.has_applied ? <Link className="button-secondary w-full" to={`/empresa/candidatos/${candidate.user_id}?job=${job.id}`}>Ver perfil del candidato <ArrowRight size={16} /></Link> : <button type="button" className="button-primary w-full" disabled={candidate.has_pending_invitation || sending || candidate.match_percentage < 50} onClick={onInvite}><Send size={16} />{candidate.has_pending_invitation ? "Invitación enviada" : "Invitar a postularse"}</button>}
        <p className="mt-2 text-center text-xs text-[var(--muted)]">{candidate.has_applied ? "Ya puedes consultar su perfil completo." : candidate.has_pending_invitation ? "Estamos esperando que decida si desea postularse." : "Le enviaremos la vacante. Tú decides después a quién contratar."}</p>
      </div>
    </article>
  );
}
