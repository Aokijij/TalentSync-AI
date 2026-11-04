const keys = ["title", "description", "requirements", "salary", "location", "department", "modality", "employment_type", "sector", "benefits", "languages", "required_education_level", "required_study_fields", "external_published_at"];
export function externalJobFields(data) {
  const values = Object.fromEntries(keys.map(key => [key, data[key] ?? (["benefits", "languages", "required_study_fields"].includes(key) ? [] : ["title", "description", "requirements"].includes(key) ? "" : null)]));
  values.skill_requirements = data.skill_requirements?.length ? structuredClone(data.skill_requirements) : (data.skills || []).map(skill => ({ skill, essential: false, level: "unspecified", weight: 1 }));
  values.quality_details = structuredClone(data.quality_details || {});
  return values;
}
export function externalJobChanges(before, after) {
  const changed = Object.fromEntries(Object.entries(after).filter(([key, value]) => key !== "quality_details" && JSON.stringify(value) !== JSON.stringify(before[key])));
  const quality = Object.fromEntries(Object.entries(after.quality_details).filter(([key, value]) => JSON.stringify(value) !== JSON.stringify(before.quality_details[key])));
  if (Object.keys(quality).length) changed.quality_details = quality;
  return changed;
}
