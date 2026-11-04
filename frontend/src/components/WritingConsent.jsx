import "../styles/writing-consent.css";

export function WritingConsent({ service, checked, onChange, disabled = false, summary = false }) {
  if (!service?.external) return null;
  return <div className="ai-writing-disclosure">
    <p>{summary ? "Para preparar este resumen se enviarán a Groq los fragmentos necesarios de tu profesión, funciones y habilidades." : "Para preparar la propuesta se enviarán a Groq el cargo, las responsabilidades de esta experiencia y el resultado opcional."} Revisa el contenido y evita incluir datos sensibles.</p>
    <p>La conexión utiliza retención cero para las entradas y respuestas. Puedes revisar el borrador antes de incorporarlo a tu perfil. <a href="https://console.groq.com/docs/your-data" target="_blank" rel="noopener noreferrer">Cómo trata Groq los datos</a></p>
    <label><input type="checkbox" checked={checked} disabled={disabled} onChange={(event) => onChange(event.target.checked)} /><span>Autorizo enviar estos fragmentos a Groq para generar esta propuesta.</span></label>
  </div>;
}
