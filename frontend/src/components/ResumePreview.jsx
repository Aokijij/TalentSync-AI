import { Mail, Phone, MapPin } from "lucide-react";
import { AuthenticatedImage } from "./AuthenticatedImage.jsx";
import { getResumePalette } from "../constants/resumePalettes.js";
import { languageLevelLabel } from "../constants/languages.js";
import { experiencePeriod } from "../utils/experienceDates.js";
import { isOngoing } from "../utils/profileStatus.js";
const availabilityLabels = { immediate: "Inmediata", two_weeks: "En 15 días", one_month: "En 30 días", negotiable: "Fecha acordada" };
const modalityLabels = { remote: "Remoto", hybrid: "Híbrido", onsite: "Presencial" };
const resumeStyles = {
  classic: {
    header: "bg-slate-950 text-white",
    photo: "rounded-xl",
  },
  modern: {
    header: "bg-white text-slate-950",
    photo: "rounded-full",
  },
  minimal: {
    header: "bg-white text-slate-950",
    photo: "rounded-full",
  },
};

export function ResumePreview({ profile, name, email, photoVersion }) {
  const style = resumeStyles[profile.resume_style] || resumeStyles.classic;
  const palette = getResumePalette(profile.resume_style, profile.resume_color);
  const location = [profile.location, profile.department]
    .filter(Boolean)
    .join(", ");
  const initials = String(name || "Candidato")
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
  return (
    <article
      className={`resume-print-area resume-${profile.resume_style} mx-auto w-full max-w-6xl overflow-hidden bg-white text-slate-900 shadow-2xl`}
      style={palette.variables}
    >
      <header className={`resume-header ${style.header}`}>
        <div className="resume-identity">
          {profile.photo_url ? (
            <AuthenticatedImage
              src={`${profile.photo_url}?v=${photoVersion}`}
              alt=""
              className={`resume-photo shrink-0 object-cover ${style.photo}`}
              fallback={<span className={`resume-photo resume-monogram ${style.photo}`}>{initials}</span>}
            />
          ) : (
            <span className={`resume-photo resume-monogram ${style.photo}`}>
              {initials}
            </span>
          )}
          <div className="min-w-0">
            <p className="resume-eyebrow">Hoja de vida</p>
            <p className="resume-name">{name}</p>
            <p className="resume-profession">
              {profile.profession || "Perfil profesional"}
            </p>
          </div>
        </div>
        <div className="resume-contact-list">
          {email ? <span><Mail size={14} />{email}</span> : null}
          {profile.phone ? <span><Phone size={14} />{profile.phone}</span> : null}
          {location ? <span><MapPin size={14} />{location}</span> : null}
        </div>
      </header>
      <div className="resume-body">
        <aside className="resume-sidebar">
          {profile.languages?.length ? <ResumeSection title="Idiomas" compact>{profile.languages.map((item, index) => <p className="resume-compact-item capitalize" key={index}><b>{item.name}</b><br />{languageLevelLabel(item.level)}</p>)}</ResumeSection> : null}
          <ResumeSection title="Habilidades" compact>
            <div className="resume-skills">
              {(profile.skills || []).map((item) => (
                <span key={item} className="resume-skill">
                  {item}
                </span>
              ))}
              {!profile.skills?.length ? <span className="text-sm opacity-70">Sin habilidades registradas</span> : null}
            </div>
          </ResumeSection>
          {profile.certifications?.length ? (
            <ResumeSection title="Certificaciones" compact>
              {profile.certifications.map((item, index) => (
                <div key={`${item.name}-${index}`} className="resume-compact-item">
                  <p className="font-bold">{item.name}</p>
                  <p className="opacity-70">
                    {item.issuer}
                    {item.year ? ` · ${item.year}` : ""}
                  </p>
                </div>
              ))}
            </ResumeSection>
          ) : null}
          {(profile.preferred_sector || profile.preferred_modality || profile.availability) ? (
            <ResumeSection title="Preferencias" compact>
              <div className="space-y-3 text-sm">
                {profile.preferred_sector ? <p><b>Sector</b><span>{profile.preferred_sector}</span></p> : null}
                {profile.preferred_modality ? <p><b>Modalidad</b><span>{modalityLabels[profile.preferred_modality] || profile.preferred_modality}</span></p> : null}
                {profile.availability ? <p><b>Disponibilidad</b><span>{availabilityLabels[profile.availability] || profile.availability}</span></p> : null}
              </div>
            </ResumeSection>
          ) : null}
        </aside>
        <main className="resume-main">
          {profile.experience ? (
            <ResumeSection title="Perfil profesional">
              <p className="resume-summary">{profile.experience}</p>
            </ResumeSection>
          ) : null}
          {profile.experiences?.length ? (
            <ResumeSection title="Experiencia">
              {profile.experiences.map((item, index) => (
                <div
                  key={`${item.company}-${index}`}
                  className="resume-timeline-item break-inside-avoid"
                >
                  <div className="resume-item-heading">
                    <div>
                      <p className="resume-item-title">{item.role || "Cargo"}</p>
                      <p className="resume-item-company">{item.company}</p>
                    </div>
                    <p className="resume-item-date">
                      {experiencePeriod(item)}
                    </p>
                  </div>
                  {item.description ? (
                    <p className="resume-item-description">
                      {item.description}
                    </p>
                  ) : null}
                </div>
              ))}
            </ResumeSection>
          ) : null}
          {profile.educations?.length ? (
            <ResumeSection title="Formación">
              {profile.educations.map((item, index) => (
                <div
                  key={`${item.degree}-${index}`}
                  className="resume-education-item break-inside-avoid"
                >
                  <div>
                    <p className="resume-item-title">{item.degree}</p>
                    <p className="resume-item-company">{item.institution}</p>
                  </div>
                  <p className="resume-item-date">{item.start_year}{isOngoing(item) ? " – En curso" : item.end_year ? ` - ${item.end_year}` : ""}</p>
                </div>
              ))}
            </ResumeSection>
          ) : profile.education ? (
            <ResumeSection title="Formación">
              <p className="resume-summary">{profile.education}</p>
            </ResumeSection>
          ) : null}
        </main>
      </div>
    </article>
  );
}

function ResumeSection({ title, children, compact = false }) {
  return (
    <section className={compact ? "resume-section resume-section-compact" : "resume-section"}>
      <h2>{title}</h2>
      {children}
    </section>
  );
}
