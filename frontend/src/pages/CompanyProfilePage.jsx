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
import { CompanyScore } from "../components/CompanyScore.jsx";
import "../styles/company-public.css";

export function CompanyProfilePage() {
  const { companyId } = useParams();
  const { user } = useAuth();
  const [company, setCompany] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [follow, setFollow] = useState({ is_following: false, min_match: 60 });
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setError(""); setCompany(null); setJobs([]);
    Promise.all([api.get(`/companies/${companyId}`), api.get("/jobs")])
      .then(([companyResponse, jobsResponse]) => {
        if (!active) return;
        setCompany(companyResponse.data);
        setJobs(
          jobsResponse.data.filter(
            (job) => Number(job.company_id) === Number(companyId) && job.status === "active",
          ),
        );
      })
      .catch((requestError) =>
        active && setError(getApiErrorMessage(requestError, "No fue posible cargar la empresa")),
      );

    if (user?.role === "candidate") {
      api
        .get(`/companies/${companyId}/follow`)
        .then(({ data }) => { if (active) setFollow(data); })
        .catch((requestError) =>
          active && setError(
            getApiErrorMessage(
              requestError,
              "No fue posible cargar tus preferencias de seguimiento",
            ),
          ),
        );
    }
    return () => { active = false; };
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
    <div className="company-public space-y-6">
      <section className="company-public-hero">
        <div className="company-public-cover" style={company.cover_url ? { backgroundImage: `linear-gradient(90deg,#07172bd9,#07172b55), url(${apiFileUrl(company.cover_url)})` } : undefined}><p>CONOCE A TU PRÓXIMO EQUIPO</p></div>
        <div className="company-public-identity"><div className="company-public-logo">{company.logo_url ? <img src={apiFileUrl(company.logo_url)} alt={`Logo de ${company.name}`} /> : <Building2 size={40} />}</div><div><p className="section-kicker">PERFIL DE EMPRESA</p><h1>{company.name}</h1><div className="company-public-facts">{company.sector && <span><BriefcaseBusiness size={15} />{company.sector}</span>}{company.location && <span><MapPin size={15} />{company.location}</span>}{company.size && <span><UsersRound size={15} />{company.size} personas</span>}</div>{company.website && <a href={company.website} target="_blank" rel="noreferrer">Visitar sitio web<ExternalLink size={14} /></a>}</div><aside><CompanyScore value={company.platform_score} /><span className="company-public-job-count"><BriefcaseBusiness size={15} />{jobs.length} vacantes activas</span></aside></div>
        {user?.role === "candidate" && <footer className="company-public-follow"><div><BellRing size={21} /><span><strong>Recibe sus próximas oportunidades</strong><small>Elige la compatibilidad mínima para los avisos.</small></span></div><label>A partir de<select className="field-control" value={follow.min_match} onChange={(event) => updateMinimum(event.target.value)}>{[50, 60, 70, 80, 90].map((value) => <option key={value} value={value}>{value}%</option>)}</select></label><button type="button" className={follow.is_following ? "button-secondary" : "button-primary"} onClick={toggleFollow}><BellRing size={16} />{follow.is_following ? "Dejar de seguir" : "Seguir empresa"}</button></footer>}
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
