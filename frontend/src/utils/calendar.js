export const dateKey = (date) => date.toISOString().slice(0, 10);
export function calendarDays(month) {
  const [year, number] = month.split("-").map(Number);
  const first = new Date(Date.UTC(year, number - 1, 1));
  const start = first.getTime() - ((first.getUTCDay() + 6) % 7) * 86400000;
  return Array.from({ length: 42 }, (_, index) => dateKey(new Date(start + index * 86400000)));
}
export function shiftDate(value, days) { return dateKey(new Date(new Date(`${value}T12:00:00Z`).getTime() + days * 86400000)); }
export function shiftMonth(value, months) {
  const [year, month] = value.split("-").map(Number);
  return dateKey(new Date(Date.UTC(year, month - 1 + months, 1))).slice(0, 7);
}
export function localToday() { const day = new Date(); return `${day.getFullYear()}-${String(day.getMonth() + 1).padStart(2, "0")}-${String(day.getDate()).padStart(2, "0")}`; }
