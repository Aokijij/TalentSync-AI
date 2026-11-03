import "../styles/resume-preferences-summary.css";
import { Link } from "react-router-dom";
import { exportSections } from "../utils/resumeExport.js";

export function ResumePreferencesSummary({ options, compact = false }) {
  const included = options?.sections ?? exportSections.map(([key]) => key);
  return <div className={`resume-preferences-summary${compact ? " is-compact" : ""}`}><strong>Contenido guardado en tu perfil</strong><p>{included.length} {included.length === 1 ? "apartado" : "apartados"} · {options?.include_photo === false ? "Sin foto" : "Foto si está disponible"}</p><details><summary>Ver qué se incluye</summary><ul>{exportSections.filter(([key]) => included.includes(key)).map(([key, label]) => <li key={key}>{label}</li>)}</ul></details><Link to="/perfil">Cambiar preferencias en mi perfil<small>Guarda allí los cambios antes de crear o enviar tu CV.</small></Link></div>;
}
