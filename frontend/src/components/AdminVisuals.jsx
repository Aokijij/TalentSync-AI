import {
  AlertTriangle,
  CheckCircle2,
  CircleDot,
  Database,
  HardDrive,
  Sparkles,
} from "lucide-react";

export function ActivityTrendChart({ data = [] }) {
  const width = 720;
  const height = 250;
  const left = 46;
  const right = 18;
  const top = 20;
  const bottom = 42;
  const max = Math.max(
    1,
    ...data.flatMap((item) => [item.users, item.applications]),
  );
  const x = (index) =>
    left + (index / Math.max(data.length - 1, 1)) * (width - left - right);
  const y = (value) => top + (1 - value / max) * (height - top - bottom);
  const line = (key) =>
    data
      .map((item, index) => `${index ? "L" : "M"}${x(index)},${y(item[key])}`)
      .join(" ");
  return (
    <figure aria-label="Usuarios y postulaciones registradas durante los últimos 14 días">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="font-bold text-[var(--ink-strong)]">
            Actividad de los últimos 14 días
          </h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Altas de usuarios y nuevas postulaciones
          </p>
        </div>
        <div className="flex gap-4 text-xs font-semibold text-[var(--muted)]">
          <span className="flex items-center gap-2">
            <i className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
            Usuarios
          </span>
          <span className="flex items-center gap-2">
            <i className="h-2.5 w-2.5 rounded-full bg-[var(--success)]" />
            Postulaciones
          </span>
        </div>
      </div>
      <svg
        className="mt-4 h-auto w-full"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
      >
        <title>Actividad diaria</title>
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const value = Math.round(max * step);
          const cy = y(value);
          return (
            <g key={step}>
              <line
                x1={left}
                y1={cy}
                x2={width - right}
                y2={cy}
                stroke="var(--line)"
              />
              <text
                x={left - 10}
                y={cy + 4}
                textAnchor="end"
                fill="var(--muted)"
                fontSize="11"
              >
                {value}
              </text>
            </g>
          );
        })}
        {data.map((item, index) =>
          index % 3 === 0 || index === data.length - 1 ? (
            <text
              key={item.date}
              x={x(index)}
              y={height - 12}
              textAnchor="middle"
              fill="var(--muted)"
              fontSize="10"
            >
              {new Date(`${item.date}T12:00:00`).toLocaleDateString("es-CO", {
                day: "2-digit",
                month: "short",
              })}
            </text>
          ) : null,
        )}
        <path
          d={line("users")}
          fill="none"
          stroke="var(--accent)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d={line("applications")}
          fill="none"
          stroke="var(--success)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        {data.map((item, index) => (
          <g key={item.date}>
            <circle
              cx={x(index)}
              cy={y(item.users)}
              r="3"
              fill="var(--accent)"
            />
            <circle
              cx={x(index)}
              cy={y(item.applications)}
              r="3"
              fill="var(--success)"
            />
          </g>
        ))}
      </svg>
    </figure>
  );
}

export function SemanticSkillGraph({ graph = { nodes: [], edges: [] } }) {
  const nodes = graph.nodes ?? [];
  const edges = graph.edges ?? [];
  const width = 620;
  const height = 360;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) * 0.35;
  const positions = Object.fromEntries(
    nodes.map((node, index) => [
      node.id,
      {
        x:
          centerX +
          Math.cos(
            (Math.PI * 2 * index) / Math.max(nodes.length, 1) - Math.PI / 2,
          ) *
            radius,
        y:
          centerY +
          Math.sin(
            (Math.PI * 2 * index) / Math.max(nodes.length, 1) - Math.PI / 2,
          ) *
            radius,
      },
    ]),
  );
  if (!nodes.length)
    return (
      <p className="py-12 text-center text-sm text-[var(--muted)]">
        Publica vacantes con habilidades para construir el grafo semántico.
      </p>
    );
  return (
    <figure aria-label="Relaciones entre habilidades presentes en las vacantes activas">
      <div>
        <h3 className="font-bold text-[var(--ink-strong)]">
          Grafo semántico del mercado
        </h3>
        <p className="mt-1 text-sm text-[var(--muted)]">
          La cercanía se basa en habilidades que aparecen juntas en ofertas
          activas.
        </p>
      </div>
      <svg
        className="mt-2 h-auto w-full"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
      >
        <title>Red de habilidades laborales</title>
        {edges.map((edge) => {
          const source = positions[edge.source];
          const target = positions[edge.target];
          return source && target ? (
            <line
              key={`${edge.source}-${edge.target}`}
              x1={source.x}
              y1={source.y}
              x2={target.x}
              y2={target.y}
              stroke="var(--line)"
              strokeWidth={Math.min(5, 1 + edge.weight)}
            />
          ) : null;
        })}
        {nodes.map((node) => {
          const p = positions[node.id];
          const nodeRadius = 14 + Math.min(16, node.count * 3);
          return (
            <g key={node.id}>
              <circle
                cx={p.x}
                cy={p.y}
                r={nodeRadius}
                fill="var(--surface)"
                stroke="var(--accent)"
                strokeWidth="2.5"
              />
              <text
                x={p.x}
                y={p.y - 2}
                textAnchor="middle"
                fill="var(--ink-strong)"
                fontSize="11"
                fontWeight="700"
              >
                {node.id.length > 14 ? `${node.id.slice(0, 13)}…` : node.id}
              </text>
              <text
                x={p.x}
                y={p.y + 12}
                textAnchor="middle"
                fill="var(--muted)"
                fontSize="9"
              >
                {node.count} ofertas
              </text>
            </g>
          );
        })}
      </svg>
    </figure>
  );
}

const serviceIcons = {
  "Base de datos": Database,
  Almacenamiento: HardDrive,
  "Motor NLP": Sparkles,
};
export function InfrastructurePanel({ services = [] }) {
  return (
    <div>
      <div className="flex items-center justify-between gap-3">
        <div>
          <h3 className="font-bold text-[var(--ink-strong)]">
            Salud de infraestructura
          </h3>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Comprobaciones operativas en tiempo real
          </p>
        </div>
        <span className="flex items-center gap-2 text-xs font-bold text-[var(--success)]">
          <CircleDot size={15} />
          En línea
        </span>
      </div>
      <div className="mt-5 space-y-3">
        {services.map((service) => {
          const Icon = serviceIcons[service.service] ?? Database;
          const healthy = service.status === "healthy";
          return (
            <article
              key={service.service}
              className="flex items-center gap-3 rounded-[var(--radius-lg)] bg-[var(--surface-subtle)] p-4"
            >
              <div
                className={`grid h-10 w-10 place-items-center rounded-[var(--radius-md)] ${healthy ? "bg-[var(--success)]/10 text-[var(--success)]" : "bg-[var(--warning)]/10 text-[var(--warning)]"}`}
              >
                <Icon size={19} />
              </div>
              <div className="min-w-0 flex-1">
                <p className="font-bold text-[var(--ink-strong)]">
                  {service.service}
                </p>
                <p className="truncate text-xs text-[var(--muted)]">
                  {service.detail}
                </p>
              </div>
              <div className="text-right">
                {healthy ? (
                  <CheckCircle2
                    className="ml-auto text-[var(--success)]"
                    size={20}
                  />
                ) : (
                  <AlertTriangle
                    className="ml-auto text-[var(--warning)]"
                    size={20}
                  />
                )}
                <p className="mt-1 text-[10px] font-semibold uppercase text-[var(--muted)]">
                  {service.latency_ms != null
                    ? `${service.latency_ms} ms`
                    : healthy
                      ? "Operativo"
                      : "Revisar"}
                </p>
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
}
