import { cloneElement, createContext, useContext, useId } from "react";
import { CircleAlert } from "lucide-react";

const Context = createContext({ errors: {}, clearError() {} });
export function ProfileFormFeedback({ errors, clearError, children }) {
  return <Context.Provider value={{ errors, clearError }}>{children}</Context.Provider>;
}

export function FormField({ label, path, children, className = "", help }) {
  const { errors, clearError } = useContext(Context), id = useId(), error = errors[path];
  const native = typeof children.type === "string";
  const Tag = native ? "label" : "div";
  const control = cloneElement(children, {
    id: children.props.id || id,
    "aria-invalid": error ? true : undefined,
    "aria-describedby": [children.props["aria-describedby"], error ? `${id}-error` : help ? `${id}-help` : ""].filter(Boolean).join(" ") || undefined,
    onChange: (...args) => { clearError(path); children.props.onChange?.(...args); },
  });
  return <Tag className={`form-field ${error ? "has-error" : ""} ${className}`} data-field-path={path}>{label && <span className="form-field-label">{label}</span>}{control}{error ? <span className="field-error" id={`${id}-error`} role="alert"><CircleAlert size={15} /><span>{error}</span></span> : help ? <small id={`${id}-help`} className="form-field-help">{help}</small> : null}</Tag>;
}

export function SectionFieldIssues({ prefix, exact = false }) {
  const { errors } = useContext(Context);
  const rows = Object.entries(errors).filter(([path]) => path === prefix || !exact && path.startsWith(`${prefix}.`));
  if (!rows.length) return null;
  return <div className="section-field-errors" role="alert" tabIndex={-1} data-field-path={prefix}><CircleAlert size={18} /><div><strong>Revisa este apartado</strong><ul>{[...new Set(rows.map(([, message]) => message))].map((message) => <li key={message}>{message}</li>)}</ul></div></div>;
}
