import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";

export function welcomePreferences(profile = {}) {
  return { profession: profile.profession || "", city: profile.location || "", modality: profile.preferred_modality || "", salary: profile.desired_salary == null ? "" : String(profile.desired_salary), sector: profile.preferred_sector || "", availability: profile.availability || "" };
}
const cityKey = (value) => value.trim().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLocaleLowerCase("es");
export function welcomeChanges(initial, values) {
  const changes = {};
  for (const [key, field] of [["sector", "preferred_sector"], ["availability", "availability"]]) {
    if (values[key] !== initial[key]) changes[field] = values[key] || null;
  }
  if (values.profession.trim() !== initial.profession.trim()) changes.profession = values.profession.trim() || null;
  if (values.modality !== initial.modality) changes.preferred_modality = values.modality || null;
  if (values.salary !== initial.salary) {
    const salary = values.salary ? Number(values.salary) : null;
    if (salary != null && (!Number.isFinite(salary) || salary <= 0 || salary > 1_000_000_000)) throw new Error("Indica una aspiración mayor que cero y de hasta mil millones de COP, o deja el campo vacío.");
    changes.desired_salary = salary;
  }
  if (values.city.trim() !== initial.city.trim()) {
    const key = cityKey(values.city);
    const matches = Object.entries(COLOMBIA_LOCATIONS).flatMap(([department, cities]) => cities.filter((city) => cityKey(city) === key).map((city) => ({ city, department })));
    if (key && !matches.length) throw new Error("Elige una ciudad del catálogo o deja la ubicación vacía para completarla después.");
    changes.location = matches[0]?.city || null;
    // Do not guess a department when several cities share the same name.
    changes.department = matches.length === 1 ? matches[0].department : null;
  }
  return changes;
}

export function companyWelcomeState(organization, user, accessOptions = {}) {
  const status = organization.verification_status;
  const exempt = organization.verification_required === false;
  const approved = status === "verified";
  const allowed = status !== "suspended" && (approved || exempt);
  const mfaReady = accessOptions.company_mfa_required === false || user.mfa_enabled === true;
  return {
    owner: organization.role === "owner", allowed, ready: allowed && !!user.email_verified && mfaReady,
    submitted: !!organization.submission?.submitted_at || ["reviewing", "information_required", "rejected", "verified"].includes(status),
    reviewLabel: ({ pending: "Por presentar", reviewing: "En revisión", information_required: "Requiere correcciones", rejected: "Solicitud rechazada", verified: "Verificada", suspended: "Suspendida" })[status] || "Estado por confirmar",
    reviewText: status === "suspended" ? "La actividad está suspendida. Revisa el motivo y la solicitud con el propietario." : approved ? "La administración aprobó la organización. Las vacantes conservan su propia revisión de calidad." : exempt ? "Esta organización no tiene la verificación obligatoria activada. Esto no equivale a una aprobación administrativa." : status === "reviewing" ? "La solicitud está presentada y espera revisión administrativa. Puedes preparar borradores mientras tanto." : ["information_required", "rejected"].includes(status) ? "Revisa la respuesta de administración, corrige la solicitud y vuelve a presentarla." : "El propietario debe presentar los datos y soportes de la organización. La revisión es manual.",
    mfaReady,
  };
}
