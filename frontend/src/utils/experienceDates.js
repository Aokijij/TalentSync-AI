export function experiencePeriod(item) {
  const format = (value) => {
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(value || "")) return value || "Sin fecha";
    const [year, month] = value.split("-").map(Number);
    return new Intl.DateTimeFormat("es-CO", { month: "short", year: "numeric", timeZone: "UTC" }).format(new Date(Date.UTC(year, month - 1, 1)));
  };
  return `${format(item.start_date || item.start_year)} — ${item.is_current || /^(presente|actualidad|actual)$/i.test(item.end_year || "") ? "Actualidad" : format(item.end_date || item.end_year)}`;
}
