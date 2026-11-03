// These fields are public contact information, never application credentials.
export function legalIdentity(env = {}) {
  const fields = {
    name: env.VITE_LEGAL_NAME?.trim() || "José Alejandro Blanquicett Herrera",
    email: env.VITE_LEGAL_EMAIL?.trim() || "talentsyncadmin@gmail.com",
    city: env.VITE_LEGAL_CITY?.trim() || "",
    country: env.VITE_LEGAL_COUNTRY?.trim() || "",
    address: env.VITE_LEGAL_ADDRESS?.trim() || "",
    phone: env.VITE_LEGAL_PHONE?.trim() || "",
    effectiveDate: env.VITE_LEGAL_EFFECTIVE_DATE?.trim() || "",
  };
  return { ...fields, complete: Object.values(fields).every(Boolean) };
}

export const publicLegal = legalIdentity({
  VITE_LEGAL_NAME: import.meta.env.VITE_LEGAL_NAME,
  VITE_LEGAL_EMAIL: import.meta.env.VITE_LEGAL_EMAIL,
  VITE_LEGAL_CITY: import.meta.env.VITE_LEGAL_CITY,
  VITE_LEGAL_COUNTRY: import.meta.env.VITE_LEGAL_COUNTRY,
  VITE_LEGAL_ADDRESS: import.meta.env.VITE_LEGAL_ADDRESS,
  VITE_LEGAL_PHONE: import.meta.env.VITE_LEGAL_PHONE,
  VITE_LEGAL_EFFECTIVE_DATE: import.meta.env.VITE_LEGAL_EFFECTIVE_DATE,
});
