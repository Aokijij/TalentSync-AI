const fold = (value) => String(value || "").normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase().trim();
const frequent = ["Bogotá", "Medellín", "Santiago De Cali", "Barranquilla", "Cartagena De Indias", "Bucaramanga", "Pereira"];

export function citySuggestions(options, value, limit = 8) {
  const query = fold(value);
  if (!query) {
    const preferred = frequent.map((city) => options.find((option) => fold(option.split(",")[0]) === fold(city))).filter(Boolean);
    return [...new Set([...preferred, ...options])].slice(0, limit);
  }
  return options.filter((item) => fold(item).includes(query)).sort((a, b) => Number(fold(b).startsWith(query)) - Number(fold(a).startsWith(query))).slice(0, limit);
}
