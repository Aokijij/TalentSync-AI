import { profileLinksPayload } from "./profileLinks.js";
import { DRIVING_CATEGORIES } from "../constants/credentials.js";
import { localToday } from "./calendar.js";
import { validationMessage } from "../api/errors.js";

export function profileValidation(profile, name, today = localToday()) {
  const errors = {};
  if (!name?.trim() || name.trim().length < 2) errors.name = "Escribe tu nombre completo, con al menos dos caracteres.";
  try { profileLinksPayload(profile.links); } catch (error) { errors[error.fieldPath || "links"] = error.message; }
  if (profile.birth_date && (!/^\d{4}-\d{2}-\d{2}$/.test(profile.birth_date) || profile.birth_date < "1900-01-01" || profile.birth_date > today)) errors.birth_date = "Elige una fecha de nacimiento válida, que no esté en el futuro.";
  if (profile.identification && (!/^[\w .\-/]{3,40}$/.test(profile.identification.number?.trim() || ""))) errors["identification.number"] = "Escribe entre 3 y 40 caracteres o quita la identificación.";
  const categories = new Set();
  (profile.driving_licenses || []).forEach((row, index) => {
    if (!DRIVING_CATEGORIES.includes(row.category)) errors[`driving_licenses.${index}.category`] = "Elige la categoría de esta licencia.";
    else if (categories.has(row.category)) errors[`driving_licenses.${index}.category`] = "Esta categoría ya está añadida.";
    categories.add(row.category);
  });
  (profile.professional_cards || []).forEach((row, index) => { if (row.profession?.trim().length < 2 || !row.profession?.trim()) errors[`professional_cards.${index}.profession`] = "Indica la profesión de esta tarjeta."; });
  (profile.certifications || []).forEach((row, index) => {
    if (row.year && (!/^\d{4}$/.test(String(row.year)) || Number(row.year) < 1900 || Number(row.year) > Number(today.slice(0, 4)))) errors[`certifications.${index}.year`] = "Indica un año entre 1900 y el año actual.";
    if (row.url?.trim()) {
      try { const url = new URL(row.url); if (url.protocol !== "https:" || url.username || url.password) throw new Error(); }
      catch { errors[`certifications.${index}.url`] = "Usa un enlace completo que comience por https:// o deja el campo vacío."; }
    }
  });
  return errors;
}

export function profileServerErrors(error) {
  const detail = error?.response?.data?.detail;
  if (!Array.isArray(detail)) return {};
  return Object.fromEntries(detail.map((row) => { const parts = (row.loc || []).filter((part) => part !== "body"); if (parts[0] === "links" && parts.length === 2) parts.push("url"); return [parts.join("."), validationMessage(row)]; }));
}

export function focusProfileError(errors, root = document) {
  const sections = { experiences: "profile-experiences", educations: "profile-educations", certifications: "profile-certifications", languages: "profile-languages", skills: "profile-skills", links: "profile-links", driving_licenses: "profile-driving-licenses", professional_cards: "profile-professional-cards", birth_date: "profile-private", identification: "profile-private", personal_visibility: "profile-private", mobility: "preferencias", skill_levels: "profile-skills" };
  const path = Object.keys(errors)[0];
  let target = [...root.querySelectorAll("[data-field-path]")].find((element) => element.dataset.fieldPath === path);
  if (!target) target = [...root.querySelectorAll("[data-field-path]")].filter((element) => path?.startsWith(`${element.dataset.fieldPath}.`)).sort((a, b) => b.dataset.fieldPath.length - a.dataset.fieldPath.length)[0];
  if (!target) target = root.getElementById?.(sections[path?.split(".")[0]]);
  target?.scrollIntoView({ block: "center", behavior: "smooth" });
  (target?.querySelector('[aria-invalid="true"],input,select,textarea,button') || target)?.focus?.({ preventScroll: true });
}
