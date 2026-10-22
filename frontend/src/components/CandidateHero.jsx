import { Clock3, Mail, MapPin, Phone, UserRound } from "lucide-react";
import { AuthenticatedImage } from "./AuthenticatedImage.jsx";
import { SharedPersonalDetails } from "./SharedPersonalDetails.jsx";
import "../styles/profile-page.css";

const availabilityLabels = { immediate: "Disponibilidad inmediata", two_weeks: "Disponible en 15 días", one_month: "Disponible en un mes", negotiable: "Disponibilidad a convenir" };

export function CandidateHero({ candidate, children }) {
  return <section className={`candidate-profile-hero${children ? " candidate-profile-has-score" : ""}`}><header className="profile-identity"><div className="profile-identity-heading"><span className="profile-identity-avatar"><AuthenticatedImage src={candidate.photo_url} alt="" fallback={<UserRound size={28} />} /></span><div><p className="profile-eyebrow">PERFIL DE CANDIDATO</p><h1 className="profile-name">{candidate.name}</h1>{candidate.profession && <p className="profile-profession">{candidate.profession}</p>}</div></div><div className="candidate-profile-contact">{[[Mail, candidate.email], [Phone, candidate.phone], [MapPin, [candidate.location, candidate.department].filter(Boolean).join(", ")], [Clock3, availabilityLabels[candidate.availability] || candidate.availability]].filter(([, value]) => value).map(([Icon, value]) => <span key={value}><Icon size={16} />{value}</span>)}<SharedPersonalDetails profile={candidate} showAge /></div></header>{children && <aside className="candidate-profile-score">{children}</aside>}</section>;
}
