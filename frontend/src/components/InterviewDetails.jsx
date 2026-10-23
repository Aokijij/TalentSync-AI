import { ExternalLink, MapPin, Video } from "lucide-react";

export function InterviewDetails({ details = {} }) {
  const virtual = details.mode === "virtual";
  const safeLink = virtual && /^https:\/\//i.test(details.location || "");
  return <div className="interview-details">
    <span className="interview-format">{virtual ? <Video size={15} /> : <MapPin size={15} />}{virtual ? "Virtual" : details.mode === "in_person" ? "Presencial" : "Modalidad por confirmar"}{details.minutes ? ` · ${details.minutes} min` : ""}</span>
    {details.location && (safeLink ? <a href={details.location} target="_blank" rel="noopener noreferrer">Abrir videollamada<ExternalLink size={14} /></a> : <p>{details.location}</p>)}
    {details.instructions && <p className="interview-instructions">{details.instructions}</p>}
  </div>;
}
