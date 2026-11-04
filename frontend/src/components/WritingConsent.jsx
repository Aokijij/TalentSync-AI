import { FileText, LockKeyhole, Sparkles, ArrowUpRight } from "lucide-react";
import { ConsentChoice } from "./ConsentChoice.jsx";
import "../styles/writing-consent.css";

export function WritingConsent({ service, checked, onChange, disabled = false, summary = false }) {
  if (!service?.external) return null;
  return <div className="ai-writing-disclosure">
    <div className="ai-writing-heading"><span className="ai-writing-symbol"><Sparkles size={19} /></span><strong>Tu texto, con tu autorización</strong><span className="ai-writing-provider">Groq</span></div>
    <div className="ai-writing-details">
      <div><FileText size={17} /><div><strong>Qué se comparte</strong><p className="ai-writing-copy">{summary ? "Para preparar este resumen se enviarán a Groq los fragmentos necesarios de tu profesión, funciones y habilidades." : "Para preparar la propuesta se enviarán a Groq el cargo, las responsabilidades de esta experiencia y el resultado opcional."} Evita incluir datos sensibles.</p></div></div>
      <div><LockKeyhole size={17} /><div><strong>Tú revisas el resultado</strong><p className="ai-writing-copy">La conexión utiliza retención cero de entradas y respuestas. El borrador se incorpora al perfil cuando tú lo decides.</p></div></div>
    </div>
    <ConsentChoice title="Autorizo enviar estos fragmentos a Groq para generar esta propuesta." checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} />
    <a className="ai-writing-privacy" href="https://console.groq.com/docs/your-data" target="_blank" rel="noopener noreferrer">Cómo trata Groq los datos<ArrowUpRight size={14} /></a>
  </div>;
}
