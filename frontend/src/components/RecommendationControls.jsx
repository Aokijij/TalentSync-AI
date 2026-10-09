import { SlidersHorizontal } from "lucide-react";
import { Link } from "react-router-dom";

export function RecommendationControls({ respectPreferences, onRespectChange, excludedCount }) {
  return <section className="recommendation-preferences"><label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={respectPreferences} onChange={(event) => onRespectChange(event.target.checked)} />Aplicar mis condiciones imprescindibles{excludedCount > 0 && <span className="text-xs text-[var(--muted)]">· {excludedCount} fuera de condiciones</span>}</label><Link className="inline-flex items-center gap-2 text-sm text-[var(--accent)]" to="/perfil#preferencias"><SlidersHorizontal size={15} />Ajustar en mi perfil</Link></section>;
}
