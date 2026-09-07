import { useEffect, useState } from "react";
import { ArrowRight, SearchCheck, Sparkles, UsersRound } from "lucide-react";
import { Link } from "react-router-dom";

import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function CompanyTalentPage() {
  const [jobs, setJobs] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    api
      .get("/companies/me")
      .then(async ({ data: company }) => {
        const { data } = await api.get("/jobs", { params: { status: "" } });
        setJobs(data.filter((job) => job.company_id === company.id));
      })
      .catch(() => setError("No fue posible cargar tus vacantes"));
  }, []);
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Talento"
        title="Candidatos compatibles"
        description="Selecciona una vacante para obtener un ranking por similitud semántica y habilidades. El perfil completo solo se muestra si el candidato se postuló."
      />
      {error && (
        <p className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-[var(--error)]">
          {error}
        </p>
      )}
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {jobs.map((job) => (
          <article key={job.id} className="surface-card p-5 hover-lift">
            <div className="flex items-start justify-between gap-3">
              <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-lg)] bg-[var(--accent)]/10 text-[var(--accent)]">
                <UsersRound size={20} />
              </div>
              <span className="rounded-full bg-[var(--success)]/10 px-2.5 py-1 text-xs font-bold text-[var(--success)]">
                {job.status === "active" ? "Activa" : "Pausada"}
              </span>
            </div>
            <h2 className="mt-5 text-lg font-bold text-[var(--ink)]">
              {job.title}
            </h2>
            <p className="mt-2 line-clamp-2 text-sm leading-6 text-[var(--muted)]">
              {job.requirements}
            </p>
            <div className="mt-5 flex flex-wrap gap-2">
              {(job.skills ?? []).slice(0, 4).map((skill) => (
                <span
                  key={skill}
                  className="rounded-md border border-[var(--line)] bg-[var(--surface)]/10 px-2 py-1 text-xs text-[var(--muted)]"
                >
                  {skill}
                </span>
              ))}
            </div>
            <Link
              className="mt-6 inline-flex items-center gap-2 text-sm font-semibold text-[var(--accent)] hover-lift"
              to={`/empresa/vacantes/${job.id}/candidatos`}
            >
              <Sparkles size={16} className="text-[var(--accent)]" />
              Ver ranking NLP
              <ArrowRight size={15} />
            </Link>
          </article>
        ))}
        {jobs.length === 0 && (
          <div className="surface-card col-span-full py-14 text-center text-[var(--muted)]">
            <SearchCheck className="mx-auto mb-3 text-[var(--muted)]" />
            Publica una vacante para comenzar a buscar talento compatible.
          </div>
        )}
      </section>
    </div>
  );
}
