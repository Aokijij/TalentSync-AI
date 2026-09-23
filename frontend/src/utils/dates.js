const minute = 60 * 1000;
const hour = 60 * minute;
const day = 24 * hour;

export function formatRelativeTime(value, now = new Date()) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Fecha no disponible";
  const difference = Math.max(0, now.getTime() - date.getTime());
  if (difference < minute) return "Hace un momento";
  if (difference < hour) {
    const minutes = Math.floor(difference / minute);
    return `Hace ${minutes} min`;
  }
  if (difference < day) {
    const hours = Math.floor(difference / hour);
    return `Hace ${hours} ${hours === 1 ? "hora" : "horas"}`;
  }
  const days = Math.floor(difference / day);
  if (days < 7) return `Hace ${days} ${days === 1 ? "día" : "días"}`;
  if (days < 30) {
    const weeks = Math.floor(days / 7);
    return `Hace ${weeks} ${weeks === 1 ? "semana" : "semanas"}`;
  }
  if (days < 365) {
    const months = Math.floor(days / 30);
    return `Hace ${months} ${months === 1 ? "mes" : "meses"}`;
  }
  const years = Math.floor(days / 365);
  return `Hace ${years} ${years === 1 ? "año" : "años"}`;
}

export function isWithinDays(value, days, now = new Date()) {
  if (!days) return true;
  const date = new Date(value);
  return !Number.isNaN(date.getTime()) && now.getTime() - date.getTime() <= days * day;
}
