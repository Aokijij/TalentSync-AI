import "../styles/consent-choice.css";

export function ConsentChoice({ title, description, checked, onChange, disabled = false, required = false, href, linkText }) {
  return <div className="consent-choice">
    <label className="consent-choice-control">
      <input type="checkbox" checked={checked} onChange={onChange} disabled={disabled} required={required} />
      <span className="consent-choice-copy"><strong>{title}</strong>{description && <span>{description}</span>}</span>
    </label>
    {href && <a className="consent-choice-link" href={href} target="_blank" rel="noopener noreferrer">{linkText}<span aria-hidden="true">↗</span></a>}
  </div>;
}
