export function isOngoing(item) {
  return item.is_current === true || /^(presente|actualidad|actual|en curso)$/i.test(item.end_year || "");
}

export function selectCurrentEmployment(items, index, checked) {
  return items.map((item, i) => i === index ? { ...item, is_current: checked, end_date: "", end_year: checked ? "Presente" : "" } : checked && isOngoing(item) ? { ...item, is_current: false, end_date: "", end_year: "" } : item);
}
