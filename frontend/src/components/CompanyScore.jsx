import { ShieldCheck } from "lucide-react";
import "../styles/company-score.css";
export function CompanyScore({ value }) {
  const score = value == null ? null : Number(value);
  return <div className="company-score" aria-label={score == null ? "Empresa sin puntuación todavía" : `Puntuación en TalentSync: ${score} de 100`}><ShieldCheck size={21} /><div><span>Puntuación en TalentSync</span><strong>{score == null ? "Sin puntuación todavía" : <>{score.toLocaleString("es-CO", { maximumFractionDigits: 1 })}<small>/100</small></>}</strong></div></div>;
}
