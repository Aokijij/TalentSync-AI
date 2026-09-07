export function PageHeader({ kicker, title, description, actions }) {
  return (
    <section className="page-hero">
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div className="max-w-2xl">
          {kicker ? <p className="section-kicker">{kicker}</p> : null}
          <h1 className="mt-3 text-balance text-3xl font-bold sm:text-4xl">
            {title}
          </h1>
          {description ? (
            <p className="mt-4 max-w-xl text-sm leading-6 text-[var(--muted)] sm:text-base">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? <div className="flex flex-wrap gap-3">{actions}</div> : null}
      </div>
    </section>
  );
}
