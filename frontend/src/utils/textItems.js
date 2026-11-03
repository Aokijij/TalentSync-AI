export const textItemKey = (value) => String(value).normalize("NFD").replace(/\p{Diacritic}/gu, "").trim().toLowerCase();
export function textItems(value) {
  const items = Array.isArray(value) ? value : typeof value === "string" ? value.split(",") : [];
  return [...new Map(items.map((item) => String(item).trim()).filter(Boolean).map((item) => [textItemKey(item), item])).values()];
}
