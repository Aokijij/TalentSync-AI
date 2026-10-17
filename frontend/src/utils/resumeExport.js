export const exportSections = [["contact", "Datos de contacto y enlaces"], ["summary", "Resumen profesional"], ["experiences", "Experiencia laboral"], ["educations", "Formación académica"], ["certifications", "Certificaciones, licencias y tarjetas"], ["skills", "Habilidades"], ["languages", "Idiomas"], ["preferences", "Preferencias laborales"], ["evidence", "Proyectos y logros"]];
const fields = ["profession", "skills", "skill_levels", "languages", "experience", "education", "location", "department", "availability", "preferred_modality", "preferred_sector", "desired_salary", "phone", "experiences", "educations", "certifications", "driving_licenses", "professional_cards", "mobility", "links"];

export function resumeExportPayload(profile, name, options) {
  return { sections: options.sections, include_photo: options.includePhoto, profile: {
    ...Object.fromEntries(fields.filter((key) => profile[key] !== undefined).map((key) => [key, profile[key]])),
    name, resume_style: options.style, resume_color: options.color,
  } };
}
