export function resumeFilename(name) {
  const safe = String(name || "Candidato").replace(/[\x00-\x1f\\/:*?"<>|]/g, " ").replace(/\s+/g, " ").trim().replace(/[. ]+$/, "").slice(0, 120) || "Candidato";
  return `${safe} - TalentSync - Hoja de vida.pdf`;
}
