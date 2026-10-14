import { CheckCircle2, Circle } from "lucide-react";

const checks = [
  {
    label: "Título profesional",
    weight: 8,
    test: (profile) => (profile?.profession?.trim().length ?? 0) >= 5,
  },
  {
    label: "Teléfono, ciudad y departamento",
    weight: 9,
    test: (profile) =>
      Boolean(profile?.phone?.trim() && profile?.location?.trim() && profile?.department?.trim()),
  },
  {
    label: "6 habilidades específicas",
    weight: 12,
    test: (profile) => (profile?.skills?.length ?? 0) >= 6,
  },
  {
    label: "Resumen profesional de 120 caracteres",
    weight: 9,
    test: (profile) => (profile?.experience?.trim().length ?? 0) >= 120,
  },
  {
    label: "2 experiencias completas",
    weight: 18,
    test: (profile) => (profile?.experiences || []).filter((item) => item.role?.trim() && item.company?.trim() && (item.start_date || item.start_year) && (item.description?.trim().length ?? 0) >= 50).length >= 2,
  },
  {
    label: "Formación académica completa",
    weight: 12,
    test: (profile) => (profile?.educations || []).some((item) => item.degree?.trim() && item.institution?.trim() && item.start_year),
  },
  {
    label: "Curso o certificación",
    weight: 7,
    test: (profile) => (profile?.certifications || []).some((item) => item.name?.trim() && item.issuer?.trim()),
  },
  {
    label: "Idioma con nivel",
    weight: 6,
    test: (profile) => (profile?.languages?.length ?? 0) >= 1,
  },
  {
    label: "Preferencias laborales completas",
    weight: 9,
    test: (profile) => Boolean(profile?.availability && profile?.preferred_modality && profile?.preferred_sector && Number(profile?.desired_salary) > 0),
  },
  {
    label: "Hoja de vida",
    weight: 10,
    test: (profile) => Boolean(profile?.cv_filename && profile?.cv_text),
  },
];

export function getProfileCompletion(profile) {
  const completed = checks.filter((item) => item.test(profile));
  return {
    percentage: completed.reduce((sum, item) => sum + item.weight, 0),
    completed: completed.length,
    total: checks.length,
    missing: checks
      .filter((item) => !item.test(profile))
      .map((item) => item.label),
  };
}

export function ProfileCompletionRing({ profile, compact = false, variant = "ring" }) {
  const result = getProfileCompletion(profile);
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (result.percentage / 100) * circumference;

  if (variant === "bar") return <div className="profile-completion">
    <div className="profile-completion-label"><span>Información de tu perfil</span><strong>{result.percentage}%</strong></div>
    <div className="profile-completion-track" role="progressbar" aria-label="Información completada del perfil" aria-valuemin={0} aria-valuemax={100} aria-valuenow={result.percentage}><span style={{ width: `${result.percentage}%` }} /></div>
    <p>{result.percentage === 100 ? "Tus campos están completos. Mantenlos actualizados." : `Puedes completar: ${result.missing.slice(0, 2).join(", ").toLowerCase()}.`}</p>
    <small>Orientativo; no mide tu compatibilidad con una vacante.</small>
  </div>;

  return (
    <div
      className={`flex ${compact ? "items-center gap-4" : "flex-col items-center text-center"}`}
    >
      <div
        className="relative h-28 w-28 shrink-0"
        role="img"
        aria-label={`Perfil completado al ${result.percentage}%`}
      >
        <svg
          className="h-full w-full -rotate-90"
          viewBox="0 0 112 112"
          aria-hidden="true"
        >
          <circle
            cx="56"
            cy="56"
            r={radius}
            fill="none"
            stroke="var(--line)"
            strokeWidth="9"
          />
          <circle
            cx="56"
            cy="56"
            r={radius}
            fill="none"
            stroke="var(--accent)"
            strokeLinecap="round"
            strokeWidth="9"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="absolute inset-0 grid place-items-center">
          <div>
            <p className="text-2xl font-bold text-[var(--ink-strong)]">
              {result.percentage}%
            </p>
            <p className="text-[10px] font-bold uppercase tracking-wider text-[var(--muted)]">
              completo
            </p>
          </div>
        </div>
      </div>
      <div className={compact ? "min-w-0" : "mt-3"}>
        <p className="font-bold text-[var(--ink-strong)]">
          {result.percentage === 100 ? "Perfil listo para comparar" : "Fortalece tu perfil"}
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {result.percentage === 100
            ? "Incluyes evidencia suficiente para una comparación rigurosa."
            : `Te falta: ${result.missing.slice(0, 3).join(", ").toLowerCase()}${result.missing.length > 3 ? ` y ${result.missing.length - 3} elemento${result.missing.length - 3 === 1 ? "" : "s"} más` : ""}.`}
        </p>
        {!compact ? (
          <div className="mt-4 space-y-2 text-left">
            {checks.map((item) => {
              const done = item.test(profile);
              return (
                <div
                  key={item.label}
                  className="flex items-center gap-2 text-xs text-[var(--muted)]"
                >
                  {done ? (
                    <CheckCircle2 size={15} className="text-[var(--success)]" />
                  ) : (
                    <Circle size={15} />
                  )}
                  <span>{item.label} · {item.weight}%</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
}
