import { Bookmark, EyeOff, SlidersHorizontal, X } from "lucide-react";
import { useState } from "react";
import { SearchPreferences } from "./SearchPreferences.jsx";
import { InterestsSettings } from "./JobInterests.jsx";

export function RecommendationControls({ interests, jobs, onSaved, respectPreferences, onRespectChange, excludedCount }) {
  const [panel, setPanel] = useState(null);
  const saved = [...interests.byId.values()].filter((value) => value === true).length;
  const hidden = [...interests.byId.values()].filter((value) => value === false).length;
  return <section className="recommendation-controls">
    <div className="flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-bold">Tu búsqueda, a tu medida</h2><p className="text-xs text-[var(--muted)]">Ajusta condiciones y organiza las oportunidades que te interesan.</p></div><div className="flex flex-wrap gap-2"><button className={panel === "preferences" ? "button-primary" : "button-secondary"} aria-expanded={panel === "preferences"} onClick={() => setPanel(panel === "preferences" ? null : "preferences")}><SlidersHorizontal size={16} />Preferencias</button><button className={panel === "interests" ? "button-primary" : "button-secondary"} aria-expanded={panel === "interests"} onClick={() => setPanel(panel === "interests" ? null : "interests")}><Bookmark size={16} />Guardadas ({saved})<EyeOff size={16} />{hidden}</button></div></div>
    <label className="mt-4 flex items-start gap-2 text-sm"><input type="checkbox" checked={respectPreferences} onChange={(event) => onRespectChange(event.target.checked)} />Respetar mis condiciones imprescindibles{excludedCount > 0 && <span className="text-xs text-[var(--muted)]">({excludedCount} ofertas no las cumplen)</span>}</label>
    {panel && <div className="mt-4 border-t border-[var(--line)] pt-4"><div className="flex items-center justify-between"><h3 className="font-semibold">{panel === "preferences" ? "¿Qué buscas en tu próximo empleo?" : "Decisiones guardadas y vacantes ocultas"}</h3><button className="button-secondary" aria-label="Cerrar ajustes" onClick={() => setPanel(null)}><X size={17} /></button></div>{panel === "preferences" ? <SearchPreferences embedded onSaved={onSaved} /> : <InterestsSettings embedded interests={interests} jobs={jobs} />}<p className="mt-3 text-xs text-[var(--muted)]">Las condiciones no cambian tu índice de habilidades. Una oferta con datos desconocidos sigue visible para que puedas revisarla.</p></div>}
  </section>;
}
