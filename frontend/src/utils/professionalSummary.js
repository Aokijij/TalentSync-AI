import { isOngoing } from "./profileStatus.js";

export function summaryInput(profile) {
  return {
    profession: profile.profession || "", skills: profile.skills || [], experience: profile.experience || "", education: profile.education || "",
    experiences: (profile.experiences || []).map((row) => ({ role: row.role || "", description: row.description || "", is_current: isOngoing(row), start_date: row.start_date || "", end_date: row.end_date || "", start_year: String(row.start_year || ""), end_year: String(row.end_year || "") })),
    educations: (profile.educations || []).map((row) => ({ degree: row.degree || "", is_current: isOngoing(row) })),
  };
}

export function withCustomSummary(profile, text) {
  return { ...profile, experience: text, summary_mode: "custom" };
}
