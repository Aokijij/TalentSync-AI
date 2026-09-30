import { CheckCircle2, CircleDashed, Info } from "lucide-react";
import { useMemo } from "react";

function normalize(value) {
  return String(value ?? "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9áéíóúüñ+#.]/g, "");
}

function candidateScore(skill, candidateSkills) {
  const target = normalize(skill);
  if (candidateSkills.some((item) => normalize(item) === target)) return 100;
  if (
    candidateSkills.some(
      (item) =>
        normalize(item).includes(target) || target.includes(normalize(item)),
    )
  )
    return 72;
  return 18;
}

function labelLines(value) {
  const words = String(value).split(/\s+/);
  const lines = [];
  for (const word of words) {
    const last = lines.at(-1);
    if (last && `${last} ${word}`.length <= 17) lines[lines.length - 1] = `${last} ${word}`;
    else lines.push(word);
  }
  return lines.slice(0, 3);
}

export function SkillRadarChart({
  candidateSkills = [],
  requiredSkills = [],
  matchPercentage,
  title = "Mapa de compatibilidad",
}) {
  const axes = useMemo(() => {
    const unique = [...new Set(requiredSkills.filter(Boolean))].slice(0, 6);
    return unique.map((skill) => ({
      label: skill,
      candidate: candidateScore(skill, candidateSkills),
      required: 100,
    }));
  }, [candidateSkills, requiredSkills]);

  if (axes.length < 3) {
    const matched = axes.filter((item) => item.candidate >= 72);
    const missing = axes.filter((item) => item.candidate < 72);
    return (
      <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-5">
        <div className="flex items-start gap-3">
          <span className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]">
            <Info size={19} />
          </span>
          <div>
            <h3 className="font-bold text-[var(--ink-strong)]">
              Comparación simplificada
            </h3>
            <p className="mt-1 text-sm leading-6 text-[var(--muted)]">
              Esta vacante solo especifica {axes.length === 1 ? "una habilidad" : `${axes.length} habilidades`}.
              No hay suficientes datos para dibujar un radar confiable, así que te
              mostramos directamente qué cumples y qué puedes fortalecer.
            </p>
          </div>
        </div>

        {axes.length ? (
          <div className="mt-4 grid gap-2 sm:grid-cols-2">
            {matched.map((item) => (
              <p key={item.label} className="flex items-center gap-2 rounded-xl border border-[var(--success)]/30 bg-[var(--success)]/10 px-3 py-2 text-sm font-semibold text-[var(--ink-strong)]">
                <CheckCircle2 size={16} className="text-[var(--success)]" />
                {item.label}: ya aparece en tu perfil
              </p>
            ))}
            {missing.map((item) => (
              <p key={item.label} className="flex items-center gap-2 rounded-xl border border-[var(--warning)]/30 bg-[var(--warning)]/10 px-3 py-2 text-sm font-semibold text-[var(--ink-strong)]">
                <CircleDashed size={16} className="text-[var(--warning)]" />
                {item.label}: habilidad por fortalecer
              </p>
            ))}
          </div>
        ) : (
          <p className="mt-4 rounded-xl border border-[var(--line)] bg-[var(--surface)] px-4 py-3 text-sm leading-6 text-[var(--muted)]">
            La fuente no publicó habilidades concretas. Usa el porcentaje como una
            orientación inicial y revisa las funciones completas antes de decidir.
          </p>
        )}
      </section>
    );
  }

  const center = 170;
  const radius = 88;
  const angle = (index) => (Math.PI * 2 * index) / axes.length - Math.PI / 2;
  const point = (index, value, extra = 0) => {
    const distance = radius * (value / 100) + extra;
    return [
      center + Math.cos(angle(index)) * distance,
      center + Math.sin(angle(index)) * distance,
    ];
  };
  const polygon = (key) =>
    axes.map((item, index) => point(index, item[key]).join(",")).join(" ");

  return (
    <figure
      className="min-w-0"
      aria-label={`${title}. Compatibilidad global ${Math.round(matchPercentage ?? 0)} por ciento.`}
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="font-bold text-[var(--ink-strong)]">{title}</h3>
          <p className="mt-1 text-xs text-[var(--muted)]">
            Tu dominio frente al nivel solicitado
          </p>
        </div>
        {matchPercentage != null ? (
          <span className="rounded-full bg-[var(--accent)]/10 px-3 py-1 text-sm font-bold text-[var(--accent)]">
            {Math.round(matchPercentage)}% de compatibilidad
          </span>
        ) : null}
      </div>
      <svg
        className="mx-auto mt-2 block h-auto w-full max-w-[360px]"
        viewBox="0 0 340 320"
        role="img"
      >
        <title>{title}</title>
        {[25, 50, 75, 100].map((level) => (
          <polygon
            key={level}
            points={axes
              .map((_, index) => point(index, level).join(","))
              .join(" ")}
            fill={level === 100 ? "var(--surface-subtle)" : "none"}
            stroke="var(--line)"
            strokeWidth="1"
          />
        ))}
        {axes.map((item, index) => {
          const [x, y] = point(index, 100);
          const [labelX, labelY] = point(index, 100, 32);
          const lines = labelLines(item.label);
          return (
            <g key={item.label}>
              <line
                x1={center}
                y1={center}
                x2={x}
                y2={y}
                stroke="var(--line)"
              />
              <text
                x={labelX}
                y={labelY}
                textAnchor={
                  labelX < center - 8
                    ? "end"
                    : labelX > center + 8
                      ? "start"
                      : "middle"
                }
                dominantBaseline="middle"
                fill="var(--muted)"
                fontSize="9"
                fontWeight="600"
              >
                <title>{item.label}</title>
                {lines.map((line, lineIndex) => (
                  <tspan key={line} x={labelX} dy={lineIndex ? 11 : -(lines.length - 1) * 5.5}>
                    {line}
                  </tspan>
                ))}
              </text>
            </g>
          );
        })}
        <polygon
          points={polygon("required")}
          fill="rgba(180,83,9,0.08)"
          stroke="var(--warning)"
          strokeWidth="2"
          strokeDasharray="5 4"
        />
        <polygon
          points={polygon("candidate")}
          fill="rgba(3,105,161,0.18)"
          stroke="var(--accent)"
          strokeWidth="2.5"
        />
        {axes.map((item, index) => {
          const [x, y] = point(index, item.candidate);
          return (
            <circle
              key={item.label}
              cx={x}
              cy={y}
              r="4"
              fill="var(--surface)"
              stroke="var(--accent)"
              strokeWidth="2"
            />
          );
        })}
      </svg>
      <figcaption className="flex flex-wrap justify-center gap-4 text-xs font-semibold text-[var(--muted)]">
        <span className="flex items-center gap-2">
          <i className="h-2.5 w-2.5 rounded-full bg-[var(--accent)]" />
          Tu perfil
        </span>
        <span className="flex items-center gap-2">
          <i className="h-2.5 w-2.5 rounded-full bg-[var(--warning)]" />
          Vacante
        </span>
      </figcaption>
    </figure>
  );
}
