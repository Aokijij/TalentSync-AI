import { useState } from "react";
import { Check, PencilLine } from "lucide-react";

export function ResumeVersionHeading({ version, selected, busy, onRename }) {
  const [editing, setEditing] = useState(false), [label, setLabel] = useState("");
  const title = version.label || "CV guardado";
  return <header className="preparation-version-heading">{editing ? <form className="preparation-rename" onSubmit={async (event) => { event.preventDefault(); if (label.trim() && await onRename(version, label.trim())) setEditing(false); }}>
    <label>Nombre del CV<input autoFocus required maxLength={80} className="field-control" value={label} disabled={busy} onChange={(event) => setLabel(event.target.value)} /></label>
    <div><button className="button-primary button-sm" type="submit" disabled={busy || !label.trim()}>Guardar nombre</button><button className="button-secondary button-sm" type="button" disabled={busy} onClick={() => setEditing(false)}>Cancelar</button></div>
  </form> : <><div><strong>{title}</strong><time dateTime={version.created_at}>{new Date(version.created_at.endsWith("Z") ? version.created_at : `${version.created_at}Z`).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" })}</time></div><div className="preparation-version-label-actions">{selected && <span><Check size={14} />Seleccionada</span>}{onRename && <button type="button" className="preparation-rename-button" disabled={busy} onClick={() => { setLabel(title); setEditing(true); }}><PencilLine size={14} />Renombrar<span className="sr-only"> {title}</span></button>}</div></>}</header>;
}
