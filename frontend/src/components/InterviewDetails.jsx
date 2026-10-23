import "../styles/interview-details.css";
import { ExternalLink, MapPin, Video } from "lucide-react";

export function InterviewDetails({ details = {}, collapsibleInstructions = false }) {
  const virtual = details.mode === "virtual";
  const safeLink = virtual && /^https:\/\//i.test(details.location || "");
  return <div className="interview-details">
    <span className="interview-format">{virtual ? <Video size={15} /> : <MapPin size={15} />}{virtual ? "Virtual" : details.mode === "in_person" ? "Presencial" : "Modalidad por confirmar"}{details.minutes ? ` · ${details.minutes} min` : ""}</span>
    {details.location && (safeLink ? <a className="interview-access-link" href={details.location} target="_blank" rel="noopener noreferrer">Abrir videollamada<ExternalLink size={14} /></a> : <p>{details.location}</p>)}
    {details.instructions && (collapsibleInstructions ? <details className="interview-instruction-disclosure"><summary>Indicaciones para la entrevista</summary><p className="interview-instructions">{details.instructions}</p></details> : <p className="interview-instructions">{details.instructions}</p>)}
  </div>;
}
