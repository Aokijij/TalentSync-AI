export const LANGUAGE_NAMES = ["inglés", "español", "francés", "portugués", "alemán", "italiano", "mandarín", "japonés"];
export const LANGUAGE_LEVELS = { A1: "A1 · Principiante", A2: "A2 · Básico", B1: "B1 · Intermedio", B2: "B2 · Intermedio alto", C1: "C1 · Avanzado", C2: "C2 · Dominio completo", NATIVE: "Nativo" };
export const languageLevelLabel = (level) => LANGUAGE_LEVELS[level] || level;
