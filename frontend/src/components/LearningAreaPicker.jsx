import { useRef, useState } from "react";
import { Check, ChevronDown, Compass, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import { AreaIcon } from "./LearningVisuals.jsx";

export function LearningAreaPicker({ areas = [], value, onChange }) {
  const [expanded, setExpanded] = useState(false);
  const toggle = useRef(null);
  const options = [{ id: "recommended", label: "Para mi perfil", detail: "Según tu trayectoria", Icon: Sparkles }, { id: "all", label: "Todas las áreas", detail: "Explora la biblioteca", Icon: Compass }, ...areas.filter((row) => !["recommended", "all"].includes(row.id))];
  const selected = options.find((row) => row.id === value) || options[0];
  return <section className="area-picker-visual area-picker-compact"><header><div><p className="section-kicker">Tu siguiente paso</p><h2>¿En qué quieres avanzar?</h2><p>Elige un área para explorar formación.</p></div><Link to="/perfil">Ajustar mi perfil →</Link></header><button ref={toggle} type="button" className="area-picker-toggle" aria-expanded={expanded} aria-controls="learning-area-options" onClick={() => setExpanded(!expanded)}><span><Compass size={17} aria-hidden="true" />{selected.label}</span><span>{expanded ? "Ocultar áreas" : "Cambiar área"}<ChevronDown size={16} aria-hidden="true" /></span></button><div id="learning-area-options" hidden={!expanded}><div className="area-picker-grid" role="group" aria-label="Área de aprendizaje">{options.map(({ id, label, Icon }) => <button key={id} type="button" aria-pressed={value === id} className={value === id ? "selected" : ""} onClick={() => { onChange(id); setExpanded(false); toggle.current?.focus(); }}><span className="area-picker-symbol">{Icon ? <Icon size={18} /> : <AreaIcon area={id} size={18} />}</span><strong>{label}</strong>{value === id && <Check className="area-picker-check" size={14} />}</button>)}</div></div></section>;
}
