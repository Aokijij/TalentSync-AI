export const linkPlatforms = [
  { value: "linkedin", label: "LinkedIn", domain: "linkedin.com", placeholder: "Pega el enlace de tu perfil en LinkedIn" },
  { value: "github", label: "GitHub", domain: "github.com", placeholder: "Pega el enlace de tu perfil en GitHub" },
  { value: "portfolio", label: "Portafolio personal", placeholder: "Pega el enlace de tu portafolio" },
  { value: "gitlab", label: "GitLab", domain: "gitlab.com", placeholder: "Pega el enlace de tu perfil en GitLab" },
  { value: "behance", label: "Behance", domain: "behance.net", placeholder: "Pega el enlace de tu perfil en Behance" },
  { value: "dribbble", label: "Dribbble", domain: "dribbble.com", placeholder: "Pega el enlace de tu perfil en Dribbble" },
  { value: "kaggle", label: "Kaggle", domain: "kaggle.com", placeholder: "Pega el enlace de tu perfil en Kaggle" },
  { value: "stackoverflow", label: "Stack Overflow", domain: "stackoverflow.com", placeholder: "Pega el enlace de tu perfil en Stack Overflow" },
  { value: "medium", label: "Medium", domain: "medium.com", placeholder: "Pega el enlace de tu perfil en Medium" },
  { value: "youtube", label: "YouTube", domain: "youtube.com", placeholder: "Pega el enlace de tu canal de YouTube" },
  { value: "other", label: "Otro enlace", placeholder: "Pega el enlace completo que quieres compartir" },
];

export function normalizeProfessionalUrl(value) {
  const text = String(value || "").trim();
  return text && !/^[a-z][a-z\d+.-]*:/i.test(text) ? `https://${text}` : text;
}

export function profileLinksPayload(rows = []) {
  const invalid = (path, message) => { const error = new Error(message); error.fieldPath = path; throw error; };
  if (rows.length > 10) invalid("links", "Puedes añadir hasta 10 enlaces profesionales.");
  const urls = new Set();
  return rows.map((row, index) => {
    const platform = linkPlatforms.find((item) => item.value === row.platform);
    let url;
    try { url = new URL(normalizeProfessionalUrl(row.url)); } catch { /* Show a field-specific message below. */ }
    if (!platform || !url || !["http:", "https:"].includes(url.protocol) || url.username || url.password || /[\s\\]/.test(String(row.url).trim()) || url.href.length > 500) {
      invalid(`links.${index}.url`, "Escribe una dirección web válida o elimina este enlace.");
    }
    if (platform.domain && url.hostname !== platform.domain && !url.hostname.endsWith(`.${platform.domain}`)) invalid(`links.${index}.url`, `El enlace de ${platform.label} debe pertenecer a ${platform.domain}.`);
    if (urls.has(url.href)) invalid(`links.${index}.url`, "Este enlace ya está añadido. Usa otro o elimina el duplicado.");
    urls.add(url.href);
    const label = (row.label || "").trim();
    if (label.length > 60) invalid(`links.${index}.label`, "El nombre de un enlace admite hasta 60 caracteres.");
    return { platform: platform.value, url: url.href, label };
  });
}
