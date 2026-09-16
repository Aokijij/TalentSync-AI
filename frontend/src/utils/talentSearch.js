function normalize(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

export function matchingSkills(candidateSkills = [], requiredSkills = []) {
  const available = new Set((candidateSkills || []).map(normalize));
  return (requiredSkills || []).filter((skill) => available.has(normalize(skill)));
}

export function searchTalent(candidates, { query = "", audience = "new", minMatch = 50 } = {}) {
  const terms = normalize(query).split(/\s+/).filter(Boolean);
  return candidates.filter((candidate) => {
    const searchable = normalize(`${candidate.name} ${candidate.profession || ""} ${(candidate.skills || []).join(" ")}`);
    return Number(candidate.match_percentage) >= minMatch && Boolean(candidate.has_applied) === (audience === "applied") && terms.every((term) => searchable.includes(term));
  }).sort((a, b) => b.match_percentage - a.match_percentage);
}
