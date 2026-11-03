export function monthChoice(year, index, minimum, maximum) {
  const value = `${year}-${String(index + 1).padStart(2, "0")}`;
  return { value, disabled: !/^\d{4}$/.test(String(year)) || index < 0 || index > 11 || value < minimum || value > maximum };
}
