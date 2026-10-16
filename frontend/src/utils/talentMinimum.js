export const TALENT_MINIMUM_OPTIONS = [60, 70, 80, 90, 100];

export function talentMinimum(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 60;
  return Math.max(60, Math.min(100, Math.ceil(number / 10) * 10));
}
