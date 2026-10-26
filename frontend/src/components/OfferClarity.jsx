import { ListChecks, Sparkles } from "lucide-react";
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
