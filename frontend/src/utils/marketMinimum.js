import { TALENT_MINIMUM_OPTIONS, talentMinimum } from "./talentMinimum.js";

// Exploring the market includes vacancies whose match has not been calculated.
// Recommendation screens keep their own minimum of 40%.
export const MARKET_MINIMUM_OPTIONS = [0, ...TALENT_MINIMUM_OPTIONS];
export function marketMinimum(value) {
  const number = Number(value);
  return !Number.isFinite(number) || number <= 0 ? 0 : talentMinimum(number);
}
export function meetsMarketMinimum(score, minimum) {
  return minimum === 0 || Number.isFinite(score) && score >= minimum;
}
