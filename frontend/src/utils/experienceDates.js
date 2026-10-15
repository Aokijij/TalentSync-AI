export function experiencePeriod(item) {
  const format = (value) => {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value || "")) return value || "Sin fecha";
    const [year, month] = value.split("-").map(Number);
    return new Intl.DateTimeFormat("es-CO", { month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(Date.UTC(year, month - 1, 1)));
  };
  return `${format(item.start_date || item.start_year)} — ${item.is_current || /^(presente|actualidad|actual)$/i.test(item.end_year || "") ? "Actualidad" : format(item.end_date || item.end_year)}`;
}
export function experienceDuration(months) {
  if (!Number.isFinite(Number(months)) || Number(months) < 1) return "Sin duración registrada";
  const total = Math.floor(Number(months));
  const years = Math.floor(total / 12), rest = total % 12;
  return [years ? `${years} año${years === 1 ? "" : "s"}` : "", rest ? `${rest} mes${rest === 1 ? "" : "es"}` : ""].filter(Boolean).join(" y ");
}
