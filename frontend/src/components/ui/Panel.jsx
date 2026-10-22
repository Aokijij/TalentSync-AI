export function Panel({ title, description, actions, children, className = "", ...props }) {
  return <section className={`ui-panel ${className}`} {...props}>
    {(title || actions) && <header className="ui-panel-heading"><div>{title && <h2>{title}</h2>}{description && <p>{description}</p>}</div>{actions && <div className="ui-panel-heading-actions">{actions}</div>}</header>}
    <div className="ui-panel-content">{children}</div>
  </section>;
}

export function PanelActions({ children, className = "" }) {
  return <footer className={`ui-panel-actions ${className}`}>{children}</footer>;
}

export function WorkspaceTabs({ items, value, onChange, label, id }) {
  return <div className="ui-workspace-tabs" role="tablist" aria-label={label} onKeyDown={(event) => {
    const buttons = [...event.currentTarget.querySelectorAll('[role="tab"]')];
    const current = buttons.indexOf(document.activeElement);
    if (current < 0) return;
    const next = event.key === "ArrowRight" ? (current + 1) % buttons.length : event.key === "ArrowLeft" ? (current - 1 + buttons.length) % buttons.length : event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : null;
    if (next !== null) { event.preventDefault(); buttons[next].focus(); buttons[next].click(); }
  }}>{items.map(([key, text, Icon]) => <button key={key} id={`${id}-tab-${key}`} role="tab" type="button" aria-selected={value === key} aria-controls={`${id}-panel-${key}`} tabIndex={value === key ? 0 : -1} onClick={() => onChange(key)}>{Icon && <Icon size={17} />}{text}</button>)}</div>;
}

export function InlineNotice({ children, error = false }) {
  return <div className={`ui-inline-notice${error ? " is-error" : ""}`} role={error ? "alert" : "status"}>{children}</div>;
}
