import {
  BellRing,
  BriefcaseBusiness,
  Building2,
  ExternalLink,
  MapPin,
  UsersRound,
} from "lucide-react";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { api, apiFileUrl, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";

export function CompanyProfilePage() {
  const { companyId } = useParams();
  const { user } = useAuth();
  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [follow, setFollow] = useState({ is_following: false, min_match: 60 });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setError("");
    Promise.all([api.get(`/companies/${companyId}`), api.get("/jobs")])
      .then(([companyResponse, jobsResponse]) => {
        setCompany(companyResponse.data);
        setJobs(
          jobsResponse.data.filter(
            (job) => Number(job.company_id) === Number(companyId),
          ),
        );
      })
      .catch((requestError) =>
        setError(getApiErrorMessage(requestError, "No fue posible cargar la empresa")),
      );

    if (user?.role === "candidate") {
      api
        .get(`/companies/${companyId}/follow`)
        .then(({ data }) => setFollow(data))
        .catch((requestError) =>
          setError(
            getApiErrorMessage(
              requestError,
              "No fue posible cargar tus preferencias de seguimiento",
            ),
          ),
        );
    }
  }, [companyId, user?.role]);

  async function toggleFollow() {
    setMessage("");
    setError("");
    try {
      if (follow.is_following) {
        await api.delete(`/companies/${companyId}/follow`);
        setFollow((current) => ({ ...current, is_following: false }));
        setMessage("Dejaste de seguir esta empresa.");
      } else {
        const { data } = await api.put(`/companies/${companyId}/follow`, {
          min_match: Number(follow.min_match),
        });
        setFollow(data);
        setMessage("Te avisaremos sobre nuevas vacantes que cumplan tu porcentaje.");
      }
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible actualizar el seguimiento"));
    }
  }

  async function updateMinimum(value) {
    const min_match = Number(value);
    setFollow((current) => ({ ...current, min_match }));
    if (follow.is_following) {
      try {
        const { data } = await api.put(`/companies/${companyId}/follow`, { min_match });
        setFollow(data);
        setMessage("Porcentaje mínimo actualizado.");
      } catch (requestError) {
        setError(getApiErrorMessage(requestError, "No fue posible cambiar el porcentaje"));
      }
    }
  }

  if (error && !company) return <p className="surface-card text-[var(--error)]">{error}</p>;
  if (!company) return <p className="text-[var(--muted)]">Cargando empresa…</p>;

  return (
    <div className="space-y-6">
      <section
        className="relative min-h-80 overflow-hidden rounded-[var(--radius-2xl)] border border-[var(--line)] bg-gradient-to-br from-sky-950 via-sky-800 to-cyan-600 shadow-soft"
        style={
          company.cover_url
            ? {
                backgroundImage: `linear-gradient(90deg, rgba(2, 12, 30, .9), rgba(2, 20, 40, .42)), url(${apiFileUrl(company.cover_url)})`,
                backgroundPosition: "center",
                backgroundSize: "cover",
              }
            : undefined
        }
      >
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent" />
        <div className="relative flex min-h-80 flex-col justify-end gap-6 p-6 sm:p-8 lg:flex-row lg:items-end lg:justify-between">
          <div className="flex flex-col gap-5 sm:flex-row sm:items-end">
            <span className="grid h-28 w-28 shrink-0 place-items-center overflow-hidden rounded-3xl border-4 border-white bg-white text-4xl font-black text-sky-900 shadow-2xl">
              {company.logo_url ? (
                <img src={apiFileUrl(company.logo_url)} alt={`Logo de ${company.name}`} className="h-full w-full object-contain p-2" />
              ) : (
                <Building2 size={42} />
              )}
            </span>
            <div className="pb-1 text-white">
              <p className="text-xs font-bold uppercase tracking-[0.18em] !text-sky-200">Perfil de empresa</p>
              <h1 className="mt-2 text-4xl font-bold tracking-tight !text-white">{company.name}</h1>
              <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2 text-sm text-slate-200">
                {company.sector ? <span>{company.sector}</span> : null}
                {company.size ? <span className="inline-flex items-center gap-1.5"><UsersRound size={15} />{company.size}</span> : null}
                {company.location ? <span className="inline-flex items-center gap-1.5"><MapPin size={15} />{company.location}</span> : null}
                {company.website ? <a className="inline-flex items-center gap-1.5 font-semibold text-cyan-300 hover:underline" href={company.website} target="_blank" rel="noreferrer">Visitar sitio web <ExternalLink size={14} /></a> : null}
              </div>
            </div>
          </div>
          {user?.role === "candidate" ? (
            <div className="min-w-64 rounded-2xl border border-white/20 bg-slate-950/55 p-4 text-white backdrop-blur-md">
              <label className="text-xs font-bold uppercase tracking-wide text-slate-200">
                Avísame desde
                <select className="field-control input-sm ml-2 w-24 !border-white/20 !bg-white/10 !text-white" value={follow.min_match} onChange={(event) => updateMinimum(event.target.value)}>
                  {[50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value}%</option>)}
                </select>
              </label>
              <button type="button" className={follow.is_following ? "button-secondary mt-3 w-full !border-white/30 !bg-white/10 !text-white" : "button-primary mt-3 w-full"} onClick={toggleFollow}>
                <BellRing size={16} />
                {follow.is_following ? "Dejar de seguir" : "Seguir empresa"}
              </button>
            </div>
          ) : null}
        </div>
      </section>
      {message ? <p className="rounded-xl border border-[var(--success)] bg-[var(--success)]/10 px-4 py-3 text-sm text-[var(--success)]">{message}</p> : null}
      {error ? <p className="rounded-xl border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">{error}</p> : null}
      <section className="grid gap-5 lg:grid-cols-2">
        <article className="surface-card p-6">
          <h2 className="text-xl font-bold">Quiénes somos</h2>
          <p className="mt-3 whitespace-pre-line text-sm leading-7 text-[var(--muted)]">{company.description || "La empresa aún no ha publicado una descripción."}</p>
          {company.mission ? <><h3 className="mt-6 font-bold">Nuestro propósito</h3><p className="mt-2 text-sm leading-7 text-[var(--muted)]">{company.mission}</p></> : null}
        </article>
        <article className="surface-card p-6">
          <h2 className="text-xl font-bold">Cultura y beneficios</h2>
          <TagList title="Valores" items={company.values} />
          <TagList title="Beneficios" items={company.benefits} />
        </article>
      </section>
      <section>
        <div className="flex items-center justify-between gap-4">
          <div><p className="section-kicker">Oportunidades</p><h2 className="mt-1 text-2xl font-bold">Vacantes de {company.name}</h2></div>
          <span className="text-sm text-[var(--muted)]">{jobs.length} disponibles</span>
        </div>
        <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {jobs.map((job) => (
            <Link key={job.id} to={`/vacantes/${job.id}`} className="surface-card group p-5 hover:border-[var(--accent)]">
              <BriefcaseBusiness size={20} className="text-[var(--accent)]" />
              <h3 className="mt-4 font-bold group-hover:text-[var(--accent)]">{job.title}</h3>
              <p className="mt-2 line-clamp-2 text-sm text-[var(--muted)]">{job.description}</p>
              <p className="mt-4 text-xs font-semibold text-[var(--accent)]">Ver vacante</p>
            </Link>
          ))}
          {!jobs.length ? <p className="surface-card col-span-full text-sm text-[var(--muted)]">Esta empresa no tiene vacantes activas en este momento.</p> : null}
        </div>
      </section>
    </div>
  );
}

function TagList({ title, items = [] }) {
  return (
    <div className="mt-5">
      <h3 className="text-sm font-bold">{title}</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {(items || []).map((item) => <span key={item} className="rounded-full bg-[var(--accent)]/10 px-3 py-1.5 text-sm text-[var(--accent)]">{item}</span>)}
        {!items?.length ? <span className="text-sm text-[var(--muted)]">Sin información todavía.</span> : null}
      </div>
    </div>
  );
}
