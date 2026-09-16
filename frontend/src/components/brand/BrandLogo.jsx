const sizes = {
  sm: {
    mark: "h-9 w-9 rounded-lg",
    title: "text-base",
    subtitle: "text-[10px]",
  },
  md: {
    mark: "h-10 w-10 rounded-xl",
    title: "text-lg",
    subtitle: "text-[11px]",
  },
  lg: {
    mark: "h-12 w-12 rounded-xl",
    title: "text-xl",
    subtitle: "text-xs",
  },
};

export function BrandLogo({
  className = "",
  size = "md",
  subtitle = "IA para talento",
  tone = "default",
}) {
  const scale = sizes[size] ?? sizes.md;
  const inverse = tone === "inverse";

  return (
    <div className={`inline-flex min-w-0 items-center gap-3 ${className}`}>
      <span
        className={`brand-mark-shell grid shrink-0 place-items-center overflow-hidden border ${scale.mark} ${
          inverse
            ? "border-white/20 bg-white/10 shadow-sm"
            : "border-sky-200 bg-sky-50"
        }`}
      >
        <img
          src="/brand/talentsync-mark.png"
          alt=""
          aria-hidden="true"
          className="brand-mark-image h-full w-full scale-[1.18] object-contain"
        />
      </span>
      <span className="min-w-0">
        <span
          className={`block truncate font-bold tracking-tight ${scale.title} ${
            inverse ? "text-white" : "text-[var(--ink-strong)]"
          }`}
        >
          TalentSync
        </span>
        {subtitle ? (
          <span
            className={`block truncate font-bold uppercase tracking-[0.14em] ${scale.subtitle} ${
              inverse ? "text-[var(--sidebar-muted)]" : "text-[var(--accent)]"
            }`}
          >
            {subtitle}
          </span>
        ) : null}
      </span>
    </div>
  );
}
