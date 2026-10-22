import { Languages } from "lucide-react";
import { LANGUAGE_LEVELS } from "../constants/languages.js";
import "../styles/profile-languages.css";

const cefr = ["A1", "A2", "B1", "B2", "C1", "C2"];
export function LanguageSummary({ value = [], required = false }) {
  const rows = value.filter((item) => item.name?.trim());
  if (!rows.length) return <p className="language-summary-empty">{required ? "Sin requisitos de idioma registrados." : "No has registrado idiomas."}</p>;
  return <div className="language-summary"><ul aria-label={required ? "Idiomas requeridos" : "Idiomas del perfil"}>{rows.map((item, index) => {
    const rank = cefr.indexOf(item.level), native = item.level === "NATIVE";
    const description = native ? "Dominio nativo" : LANGUAGE_LEVELS[item.level]?.split(" · ").slice(1).join(" · ") || "Nivel sin especificar";
    return <li key={`${item.name}-${index}`} className={native ? "language-summary-row is-native" : "language-summary-row"}><span className="language-summary-icon"><Languages size={18} /></span><div className="language-summary-content"><div><strong>{item.name}</strong><span className="language-summary-level">{native ? "Nativo" : item.level || "Sin nivel"}</span></div><p>{description}</p>{rank >= 0 && <span className="language-summary-meter" aria-hidden="true">{cefr.map((level, step) => <i key={level} className={step <= rank ? "is-filled" : ""} />)}</span>}</div></li>;
  })}</ul><p className="language-summary-note">{required ? "Nivel mínimo solicitado para el cargo." : "Niveles declarados en el perfil."}</p></div>;
}
