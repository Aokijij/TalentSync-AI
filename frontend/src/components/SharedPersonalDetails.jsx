import { personalDetailLines } from "../utils/personalDetails.js";
export function SharedPersonalDetails({ profile }) {
  const rows = personalDetailLines(profile, true);
  return rows.length ? <dl className="shared-personal-details">{rows.map(([label, value]) => <div key={label}><dt>{label}</dt><dd>{value}</dd></div>)}</dl> : null;
}
