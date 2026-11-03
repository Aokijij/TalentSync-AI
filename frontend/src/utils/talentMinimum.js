export const TALENT_MINIMUM_OPTIONS = [40, 50, 60, 70, 80, 90, 100];

export function talentMinimum(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return 40;
  return Math.max(40, Math.min(100, Math.ceil(number / 10) * 10));
}
