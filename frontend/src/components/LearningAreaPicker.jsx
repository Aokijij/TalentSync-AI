import { Check, Compass, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { AreaIcon } from "./LearningVisuals.jsx";

export function LearningAreaPicker({ areas = [], value, onChange }) {
  const options = [{ id: "recommended", label: "Para mi perfil", detail: "Según tu trayectoria", Icon: Sparkles }, { id: "all", label: "Todas las áreas", detail: "Explora la biblioteca", Icon: Compass }, ...areas.filter((row) => !["recommended", "all"].includes(row.id))];
  return <section className="area-picker-visual"><header><div><p className="section-kicker">Tu siguiente paso</p><h2>¿En qué quieres avanzar?</h2><p>Elige un área y descubre retos, cursos y prácticas para reforzar tu perfil.</p></div><Link to="/perfil">Ajustar mi perfil →</Link></header><div className="area-picker-grid" role="group" aria-label="Área de aprendizaje">{options.map(({ id, label, detail, Icon }) => <button key={id} type="button" aria-pressed={value === id} className={value === id ? "selected" : ""} onClick={() => onChange(id)}><span className="area-picker-symbol">{Icon ? <Icon size={22} /> : <AreaIcon area={id} />}</span><span><strong>{label}</strong>{detail && <small>{detail}</small>}</span>{value === id && <Check className="area-picker-check" size={15} />}</button>)}</div></section>;
}
