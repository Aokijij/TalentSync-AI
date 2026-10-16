import { QUALITY_STEPS, qualityStepProgress } from "../utils/offerQuality.js";

export function OfferQualityBreakdown({ quality, onGo }) {
  return <details className="offer-quality-breakdown"><summary>Cómo se suman los {quality.score} puntos</summary><p>Los datos básicos aportan hasta 90 puntos. Las mejoras adicionales aportan 10. Cada apartado conserva sus puntos aunque otro esté incompleto.</p>{QUALITY_STEPS.slice(0, 4).map((label, step) => {
    const progress = qualityStepProgress(quality, step);
    return <section key={label}><header><strong>{label}</strong><b>{progress.points}/{progress.total}</b></header>{quality.checks.filter((row) => row.step === step).map((row) => <button type="button" key={row.key} onClick={() => onGo?.(row.step, row.key)}><span>{row.label}<small>{row.required ? row.passed ? "Datos básicos completos" : "Obligatorio para publicar" : "Mejora opcional"}</small></span><b>{row.points ?? (row.passed ? row.weight : 0)}/{row.weight}</b></button>)}</section>;
  })}</details>;
}
