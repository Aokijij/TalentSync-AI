import { ArrowRight } from "lucide-react";
import { Link } from "react-router-dom";

export function MetricCard({ label, value, detail, to }) {
  const content = (
    <>
      <p className="section-kicker">{label}</p>
      <p className="mt-4 text-3xl font-bold tabular-nums text-[var(--ink-strong)]">
        {value}
      </p>
      {detail ? (
        <p className="mt-1 text-sm text-[var(--muted)]">{detail}</p>
      ) : null}
      {to ? <ArrowRight className="absolute right-5 top-5 text-[var(--accent)]" size={17} /> : null}
    </>
  );
  return to ? (
    <Link to={to} className="elevated-card hover-lift relative block focus-ring">
      {content}
    </Link>
  ) : (
    <article className="elevated-card hover-lift relative">{content}</article>
  );
}
