function normalize(value) {
  return String(value ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

export function matchingSkills(candidateSkills = [], requiredSkills = []) {
  const available = new Set((candidateSkills || []).map(normalize));
  return (requiredSkills || []).filter((skill) => available.has(normalize(skill)));
}

export function talentInvitation(candidate) {
  if (candidate.has_applied) return { allowed: false, reason: "Esta persona ya se postuló." };
  if (candidate.has_pending_invitation) return { allowed: false, reason: "Estamos esperando que decida si desea postularse." };
  if (candidate.location_fit?.invitation_allowed === false) return { allowed: false, reason: "La vacante no cumple las preferencias o la disponibilidad registradas." };
  const percentage = candidate.professional_match_percentage ?? candidate.match_percentage;
  if (percentage == null || !Number.isFinite(Number(percentage))) return { allowed: false, reason: "La compatibilidad está pendiente de cálculo." };
  if (Number(percentage) < 50) return { allowed: false, reason: "La invitación requiere al menos 50% de compatibilidad profesional." };
  return { allowed: true, reason: "Le enviaremos la vacante. Tú decides después a quién contratar." };
}
