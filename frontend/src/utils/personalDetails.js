export const identificationTypes = { CC: "Cédula de ciudadanía", CE: "Cédula de extranjería", TI: "Tarjeta de identidad", PPT: "Permiso por Protección Temporal", passport: "Pasaporte", other: "Otro documento" };
export function personalDetailLines(profile, shared = false) {
  const visible = (key) => shared || profile.personal_visibility?.[key] === true;
  const rows = [];
  if (profile.birth_date && visible("birth_date")) rows.push(["Nacimiento", profile.birth_date.split("-").reverse().join("/")]);
  if (profile.identification?.number && visible("identification")) rows.push([identificationTypes[profile.identification.type] || "Identificación", profile.identification.number]);
  return rows;
}
