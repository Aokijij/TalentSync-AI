export function MetricCard({ label, value, detail }) {
  return (
    <article className="elevated-card hover-lift">
      <p className="section-kicker">{label}</p>
      <p className="mt-4 text-3xl font-bold tabular-nums text-[var(--ink-strong)]">
        {value}
      </p>
      {detail ? (
        <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
      ) : null}
    </article>
  );
}
