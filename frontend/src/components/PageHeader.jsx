export function PageHeader({ kicker, title, description, actions }) {
  return (
    <header className="page-heading">
        <div className="page-heading-copy">
          {kicker ? <p className="section-kicker">{kicker}</p> : null}
          <h1>
            {title}
          </h1>
          {description ? (
            <p className="page-heading-description">
              {description}
            </p>
          ) : null}
        </div>
        {actions ? <div className="page-heading-actions">{actions}</div> : null}
    </header>
  );
}
