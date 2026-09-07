import { useEffect, useState } from "react";
import {
  ArrowRight,
  BriefcaseBusiness,
  Building2,
  ChartNoAxesCombined,
  RefreshCw,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { Link } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import {
  ActivityTrendChart,
  InfrastructurePanel,
  SemanticSkillGraph,
} from "../components/AdminVisuals.jsx";
import { PageHeader } from "../components/PageHeader.jsx";

const metricConfig = [
  { key: "users", label: "Usuarios registrados", icon: UsersRound },
  { key: "companies", label: "Empresas activas", icon: Building2 },
  { key: "active_jobs", label: "Vacantes activas", icon: BriefcaseBusiness },
  {
    key: "conversion_rate",
    label: "Conversión NLP",
    icon: ChartNoAxesCombined,
    suffix: "%",
  },
];

export function AdminDashboard() {
  const [stats, setStats] = useState({});
  const [analytics, setAnalytics] = useState({
    timeline: [],
    skill_graph: { nodes: [], edges: [] },
    infrastructure: [],
  });
  const [updatedAt, setUpdatedAt] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  async function load() {
    setLoading(true);
    setError("");
    const [statsResult, analyticsResult] = await Promise.allSettled([
      api.get("/admin/stats"),
      api.get("/admin/analytics"),
    ]);
    if (statsResult.status === "fulfilled") setStats(statsResult.value.data);
    else
      setError(
        getApiErrorMessage(
          statsResult.reason,
          "No fue posible cargar las métricas generales.",
        ),
      );
    if (analyticsResult.status === "fulfilled")
      setAnalytics(analyticsResult.value.data);
    else
      setError(
        (current) =>
          current ||
          (analyticsResult.reason?.response?.status === 404
            ? "El servicio de analítica aún no está disponible. Reinicia el backend para habilitar los gráficos en vivo."
            : getApiErrorMessage(
                analyticsResult.reason,
                "No fue posible cargar la analítica en vivo.",
              )),
      );
    if (
      statsResult.status === "fulfilled" ||
      analyticsResult.status === "fulfilled"
    )
      setUpdatedAt(new Date());
    setLoading(false);
  }
  useEffect(() => {
    load();
    const timer = window.setInterval(load, 30000);
    return () => window.clearInterval(timer);
  }, []);

  const values = {
    ...stats,
    ...analytics,
    active_jobs: analytics.active_jobs ?? stats.jobs ?? 0,
  };
  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Administración"
        title="Centro de control en tiempo real"
        description="Métricas de crecimiento, desempeño del matching y salud técnica en una sola vista."
        actions={
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              className="button-secondary"
              onClick={load}
              disabled={loading}
            >
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              Actualizar
            </button>
            <Link to="/administracion" className="button-primary">
              Gestionar plataforma <ArrowRight size={16} />
            </Link>
          </div>
        }
      />
      {error ? (
        <p
          role="alert"
          className="rounded-[var(--radius-lg)] border border-[var(--warning)] bg-[var(--warning)]/10 px-4 py-3 text-sm font-medium text-[var(--ink-strong)]"
        >
          {error}
        </p>
      ) : null}
      <div className="flex items-center gap-2 text-xs font-semibold text-[var(--muted)]">
        <span className="h-2.5 w-2.5 rounded-full bg-[var(--success)]" />
        Actualización automática cada 30 segundos
        {updatedAt
          ? ` · Última lectura ${updatedAt.toLocaleTimeString("es-CO", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`
          : ""}
      </div>

      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {metricConfig.map(({ key, label, icon: Icon, suffix }) => (
          <article key={key} className="surface-card p-5">
            <div className="flex items-center justify-between">
              <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
                <Icon size={20} />
              </div>
              <span className="text-xs font-bold uppercase tracking-wide text-[var(--muted)]">
                En vivo
              </span>
            </div>
            <p className="mt-5 text-3xl font-bold tracking-tight text-[var(--ink-strong)]">
              {values[key] ?? 0}
              {suffix}
            </p>
            <p className="mt-1 text-sm text-[var(--muted)]">{label}</p>
          </article>
        ))}
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.45fr_0.75fr]">
        <div className="surface-card p-5 sm:p-6">
          <ActivityTrendChart data={analytics.timeline} />
        </div>
        <div className="surface-card p-5 sm:p-6">
          <ConversionBars
            recommendations={stats.recommendations ?? 0}
            applications={analytics.recommended_applications ?? 0}
            hires={analytics.hires ?? 0}
          />
        </div>
      </section>

      <section className="grid gap-6 xl:grid-cols-[1.25fr_0.75fr]">
        <div className="surface-card p-5 sm:p-6">
          <SemanticSkillGraph graph={analytics.skill_graph} />
        </div>
        <div className="surface-card p-5 sm:p-6">
          <InfrastructurePanel services={analytics.infrastructure} />
        </div>
      </section>
    </div>
  );
}

function ConversionBars({ recommendations, applications, hires }) {
  const max = Math.max(1, recommendations);
  const stages = [
    {
      label: "Recomendaciones NLP",
      value: recommendations,
      color: "bg-[var(--accent)]",
    },
    {
      label: "Terminaron en postulación",
      value: applications,
      color: "bg-violet-600",
    },
    { label: "Contrataciones", value: hires, color: "bg-[var(--success)]" },
  ];
  return (
    <div>
      <div className="flex items-center gap-3">
        <div className="grid h-10 w-10 place-items-center rounded-[var(--radius-md)] bg-[var(--accent)]/10 text-[var(--accent)]">
          <Sparkles size={19} />
        </div>
        <div>
          <h3 className="font-bold text-[var(--ink-strong)]">
            Embudo de éxito
          </h3>
          <p className="text-sm text-[var(--muted)]">
            Impacto de las recomendaciones
          </p>
        </div>
      </div>
      <div className="mt-7 space-y-6">
        {stages.map((stage) => (
          <div key={stage.label}>
            <div className="mb-2 flex items-center justify-between gap-3 text-sm">
              <span className="font-semibold text-[var(--muted)]">
                {stage.label}
              </span>
              <strong className="text-[var(--ink-strong)]">
                {stage.value}
              </strong>
            </div>
            <div className="h-3 rounded-full bg-[var(--line)]">
              <div
                className={`h-full rounded-full ${stage.color}`}
                style={{
                  width: `${Math.max(stage.value ? 5 : 0, (stage.value / max) * 100)}%`,
                }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
