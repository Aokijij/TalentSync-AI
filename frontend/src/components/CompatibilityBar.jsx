export function CompatibilityBar({ value }) {
  const percentage = Number(value ?? 0);
  const safe = Number.isFinite(percentage)
    ? Math.max(0, Math.min(100, percentage))
    : 0;
  const label =
    safe >= 80
      ? "Excelente"
      : safe >= 60
        ? "Prometedor"
        : safe >= 40
          ? "Parcial"
          : "Inicial";
  const color =
    safe >= 80
      ? "var(--success)"
      : safe >= 60
        ? "var(--accent)"
        : safe >= 40
          ? "var(--warning)"
          : "var(--error)";

  return (
    <section
      className="surface-card p-4"
      aria-label={`Compatibilidad ${safe.toFixed(0)} por ciento, nivel ${label}`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-semibold text-[var(--muted)]">
          Compatibilidad
        </span>
        <strong className="text-lg font-bold tabular-nums text-[var(--ink-strong)]">
          {safe.toFixed(0)}%
        </strong>
      </div>
      <div
        className="mt-4 h-2 overflow-hidden rounded-full bg-[var(--surface-hover)]"
        role="progressbar"
        aria-valuenow={safe}
        aria-valuemin="0"
        aria-valuemax="100"
      >
        <div
          className="h-full rounded-full transition-[width] duration-300"
          style={{ width: `${safe}%`, backgroundColor: color }}
        />
      </div>
      <div className="mt-3 flex items-center justify-between text-xs text-[var(--muted)]">
        <span>0%</span>
        <span>{label}</span>
        <span>100%</span>
      </div>
    </section>
  );
}
