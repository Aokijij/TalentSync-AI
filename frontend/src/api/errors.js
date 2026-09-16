const fields = { title: "Cargo", description: "Descripción", requirements: "Requisitos", salary: "Salario", sector: "Sector laboral", languages: "Idiomas", name: "Nombre", level: "Nivel" };
export function validationMessage(item) {
  if (typeof item === "string") return item;
  const field = fields[item?.loc?.find((part) => fields[part])] || "Información";
  const type = item?.type;
  if (type === "string_too_short") return `${field}: escribe al menos ${item.ctx?.min_length || 2} caracteres`;
  if (type === "string_too_long") return `${field}: usa como máximo ${item.ctx?.max_length} caracteres`;
  if (type === "missing") return `${field}: completa este campo`;
  if (type === "float_parsing" || type === "int_parsing") return `${field}: escribe un número válido`;
  if (type === "value_error") return `${field}: ${item.msg?.replace(/^Value error, /, "")}`;
  return `${field}: revisa el valor ingresado`;
}
