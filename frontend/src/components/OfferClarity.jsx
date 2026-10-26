import { ChevronDown, Info, ListChecks, Sparkles, TrendingUp } from "lucide-react";
import "../styles/offer-clarity.css";

export function OfferClarityBadge({ job, quality }) {
  const value = quality || job?.quality_summary;
  if (job?.source_kind === "external" || !value?.rating) return null;
  const { code, label, description } = value.rating;
  return <span className="offer-clarity-badge" data-level={code} aria-label={`Nivel ${code} de claridad: ${label}`} title={`${description} Mide la información de la oferta; no certifica a la empresa ni cambia tu compatibilidad.`}>{code === "A" ? <Sparkles size={16} aria-hidden="true" /> : <ListChecks size={16} aria-hidden="true" />}<strong>Nivel {code}</strong><span>{label}</span></span>;
}

const levelMeaning = {
  A: "Funciones, requisitos y condiciones muy completos y claros.",
  B: "Información clara del cargo, con algunos detalles por completar.",
  C: "Faltan detalles relevantes sobre los requisitos o las condiciones.",
  D: "La oferta necesita más información para valorar la postulación.",
};

export function OfferClaritySummary({ job }) {
  const rating = job?.quality_summary?.rating;
  if (job?.source_kind === "external" || !rating) return null;
  return <section className="offer-clarity-current" data-level={rating.code} aria-label={`Nivel ${rating.code} de claridad: ${rating.label}`}>
    <span className="offer-clarity-letter" aria-hidden="true">{rating.code}</span>
    <div><p className="offer-clarity-caption">CLARIDAD DE ESTA OFERTA</p><h2>Nivel {rating.code}<span aria-hidden="true"> · </span>{rating.label}</h2><p>{levelMeaning[rating.code] || rating.description}</p></div>
  </section>;
}

export function OfferClarityGuide({ quality }) {
  return <details className="offer-clarity-guide"><summary><Info size={17} /><span>¿Qué significan los niveles de las ofertas?</span><ChevronDown className="offer-guide-chevron" size={17} /></summary><div><p>Los niveles de A a D describen cuánto detalle aporta la oferta sobre funciones, requisitos, condiciones y proceso de selección. Se calculan con las reglas de claridad de TalentSync.</p>{quality?.rating_scale?.length > 0 && <ol>{quality.rating_scale.map((level) => <li key={level.code} data-level={level.code}><strong>{level.code}</strong><div><b>{level.label}</b><small>{level.minimum}–{level.maximum} puntos</small><p>{level.description}</p></div></li>)}</ol>}<p className="offer-clarity-visibility"><TrendingUp size={18} /><span>Una oferta más clara puede ganar visibilidad en Recomendadas frente a otras con compatibilidad cercana. La confianza de la empresa conserva prioridad; el nivel no garantiza aparecer primero.</span></p><small>El nivel mide información de la publicación. No es el nivel profesional del cargo, una validación de la empresa ni una probabilidad de contratación. Las ofertas externas mantienen una señal neutral.</small></div></details>;
}
