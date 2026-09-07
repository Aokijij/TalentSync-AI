import { CheckCircle2, Circle } from "lucide-react";

const checks = [
  {
    label: "Título profesional",
    test: (profile) => Boolean(profile?.profession?.trim()),
  },
  {
    label: "Datos de contacto",
    test: (profile) =>
      Boolean(profile?.phone?.trim() && profile?.location?.trim()),
  },
  {
    label: "3 o más habilidades",
    test: (profile) => (profile?.skills?.length ?? 0) >= 3,
  },
  {
    label: "Experiencia",
    test: (profile) =>
      Boolean(profile?.experience?.trim() || profile?.experiences?.length),
  },
  {
    label: "Formación académica",
    test: (profile) =>
      Boolean(profile?.education?.trim() || profile?.educations?.length),
  },
  {
    label: "Preferencias laborales",
    test: (profile) =>
      Boolean(profile?.availability || profile?.preferred_modality),
  },
  {
    label: "Hoja de vida",
    test: (profile) => Boolean(profile?.cv_filename || profile?.cv_text),
  },
];

export function getProfileCompletion(profile) {
  const completed = checks.filter((item) => item.test(profile));
  return {
    percentage: Math.round((completed.length / checks.length) * 100),
    completed: completed.length,
    total: checks.length,
    missing: checks
      .filter((item) => !item.test(profile))
      .map((item) => item.label),
  };
}

export function ProfileCompletionRing({ profile, compact = false }) {
  const result = getProfileCompletion(profile);
  const radius = 48;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (result.percentage / 100) * circumference;

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
          {result.percentage === 100 ? "Perfil estelar" : "Impulsa tu perfil"}
        </p>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {result.percentage === 100
            ? "Tu información está lista para el matching."
            : `Completa ${result.missing[0]?.toLowerCase()} para mejorar tus recomendaciones.`}
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
                  <span>{item.label}</span>
                </div>
              );
            })}
          </div>
        ) : null}
      </div>
    </div>
  );
}
