export const exportSections = [["contact", "Datos de contacto, personales y enlaces"], ["summary", "Resumen profesional"], ["experiences", "Experiencia laboral"], ["educations", "Formación académica"], ["certifications", "Formación complementaria"], ["driving_licenses", "Licencias de conducción"], ["professional_cards", "Tarjetas profesionales"], ["skills", "Habilidades"], ["languages", "Idiomas"], ["preferences", "Preferencias laborales"], ["evidence", "Proyectos y logros"]];
const fields = ["birth_date", "identification", "personal_visibility","profession", "skills", "skill_levels", "languages", "experience", "education", "location", "department", "availability", "preferred_modality", "preferred_sector", "desired_salary", "phone", "experiences", "educations", "certifications", "driving_licenses", "professional_cards", "mobility", "links"];

export function resumeExportPayload(profile, name, options) {
  return { sections: options.sections, include_photo: options.includePhoto, profile: {
    ...Object.fromEntries(fields.filter((key) => profile[key] !== undefined).map((key) => [key, profile[key]])),
    name, resume_style: options.style, resume_color: options.color,
  } };
}

export function savedResumeSections(profile) {
  const options = profile.resume_export_options;
  if (!options?.sections) return exportSections.map(([key]) => key);
  const saved = [...options.sections];
  // Before version 2, the certifications switch included both document groups.
  return options.version !== 2 && saved.includes("certifications") ? [...new Set([...saved, "driving_licenses", "professional_cards"])] : saved;
}
