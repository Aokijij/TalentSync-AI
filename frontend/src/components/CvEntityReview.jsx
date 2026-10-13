import { useState } from "react";
import { Check, Plus, ScanText } from "lucide-react";

const labels = { role: "Cargo", company: "Empresa", degree: "Título o carrera", institution: "Institución", skill: "Habilidad mencionada", date: "Fecha" };
const contexts = { negated: "El CV indica falta de experiencia", learning: "En aprendizaje", project: "Uso en proyecto", applied: "Uso mencionado", declared: "Mencionada en el CV" };
const keyOf = (value) => value.trim().toLocaleLowerCase();

export function CvEntityReview({ review, profile, editing, update }) {
  const [selection, setSelection] = useState({ role: "", company: "", degree: "", institution: "" });
  const [notice, setNotice] = useState("");
  if (!review || review.status === "disabled" || !review.status) return null;
  const entities = review.entities || [];
  const unique = entities.filter((row, index) => entities.findIndex((other) => other.kind === row.kind && keyOf(other.text) === keyOf(row.text)) === index);
  function addRecord(type, fields) {
    const row = Object.fromEntries(fields.map((field) => [field, selection[field]]));
    if (profile[type].some((item) => fields.every((field) => keyOf(item[field] || "") === keyOf(row[field])))) {
      setNotice("Ese registro ya está en tu perfil. Revisa sus fechas y descripción.");
      return;
    }
    update(type, [...profile[type], { ...row, start_year: "", end_year: "", ...(type === "experiences" ? { description: "", is_current: false } : {}) }]);
    setSelection((value) => ({ ...value, ...Object.fromEntries(fields.map((field) => [field, ""])) }));
    setNotice("Añadido al borrador. Completa las fechas y los detalles antes de guardar tu perfil.");
  }
  function choose(field) {
    return <label>{labels[field]}<select value={selection[field]} onChange={(event) => setSelection((value) => ({ ...value, [field]: event.target.value }))}><option value="">Selecciona una detección</option>{unique.filter((row) => row.kind === field).map((row) => <option key={row.text} value={row.text}>{row.text}</option>)}</select></label>;
  }
  return <details className="cv-entity-review">
    <summary><ScanText size={18} /> Detecciones con IA para revisar <span>{entities.length}</span></summary>
    {review.status !== "ready" ? <p>La extracción adicional no estuvo disponible en esta carga. Se conservó el análisis habitual del PDF. Puedes volver a cargarlo para intentarlo de nuevo.</p> : <>
      <p>Estas menciones se detectaron en tu CV. Revisa el contexto: una mención no demuestra dominio ni vincula automáticamente un cargo con una empresa. {editing ? "Los cambios se añadirán al borrador y se guardarán con tu perfil." : "Pulsa Editar para usar las sugerencias."}</p>
      {review.truncated && <p>Se revisaron los primeros 30.000 caracteres. Comprueba también el resto de tu documento.</p>}
      {!entities.length && <p>No se encontraron detecciones adicionales con suficiente puntuación. Puedes completar los campos manualmente.</p>}
      <div className="cv-entity-list">{entities.map((row, index) => {
        const added = row.kind === "skill" && profile.skills.some((skill) => keyOf(skill) === keyOf(row.text));
        return <div className="cv-entity" key={`${row.start}-${row.kind}-${index}`}><div><small>{labels[row.kind]}</small><strong>{row.text}</strong></div>{row.kind === "skill" && <small>{contexts[row.context] || "Mencionada en el CV"}</small>}<blockquote>{row.excerpt}</blockquote>
          {editing && row.kind === "skill" && <button type="button" className="button-secondary" disabled={added} onClick={() => update("skills", [...profile.skills, row.text])}>{added ? <Check size={14} /> : <Plus size={14} />}{added ? "Ya está en tu perfil" : "Confirmar como habilidad declarada"}</button>}
          {editing && row.kind === "role" && <button type="button" className="button-secondary" onClick={() => update("profession", row.text)}>Usar como profesión</button>}
        </div>;
      })}</div>
      {editing && !!entities.length && <div className="cv-entity-records"><fieldset><legend>Preparar una experiencia</legend><p>Elige el cargo y su empresa. No se asignan fechas automáticamente.</p>{choose("role")}{choose("company")}<button type="button" className="button-secondary" disabled={!selection.role || !selection.company} onClick={() => addRecord("experiences", ["role", "company"])}><Plus size={14} /> Añadir al borrador</button></fieldset><fieldset><legend>Preparar un estudio</legend><p>Elige el título y la institución que correspondan.</p>{choose("degree")}{choose("institution")}<button type="button" className="button-secondary" disabled={!selection.degree || !selection.institution} onClick={() => addRecord("educations", ["degree", "institution"])}><Plus size={14} /> Añadir al borrador</button></fieldset></div>}
      {notice && <p role="status">{notice}</p>}
    </>}
  </details>;
}
