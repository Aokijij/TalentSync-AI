export const exportSections = [["contact", "Datos de contacto y enlaces"], ["summary", "Resumen profesional"], ["experiences", "Experiencia laboral"], ["educations", "Formación académica"], ["certifications", "Cursos y certificaciones"], ["skills", "Habilidades"], ["languages", "Idiomas"], ["preferences", "Preferencias laborales"], ["evidence", "Muestras de trabajo"]];
const fields = ["profession", "skills", "skill_levels", "languages", "experience", "education", "location", "department", "availability", "preferred_modality", "preferred_sector", "desired_salary", "phone", "experiences", "educations", "certifications", "mobility", "links"];

export function resumeExportPayload(profile, name, options) {
  return { sections: options.sections, include_photo: options.includePhoto, profile: {
    ...Object.fromEntries(fields.filter((key) => profile[key] !== undefined).map((key) => [key, profile[key]])),
    name, resume_style: options.style, resume_color: options.color,
  } };
}
