function Signal({ label, value, weight, description, color }) {
  const safe = Math.max(0, Math.min(100, Number(value ?? 0)));
  return (
    <div>
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-sm font-bold text-[var(--ink-strong)]">{label}</p>
          <p className="mt-0.5 text-xs text-[var(--muted)]">{description}</p>
        </div>
        <div className="text-right">
          <p className="font-bold tabular-nums text-[var(--ink-strong)]">
            {safe.toFixed(0)}%
          </p>
          <p className="text-[11px] font-semibold text-[var(--muted)]">
            Peso {weight}%
          </p>
        </div>
      </div>
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--surface-hover)]">
        <div
          className="h-full rounded-full"
          style={{ width: `${safe}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function MatchBreakdown({ skillMatch = 0, semanticMatch = 0 }) {
  return (
    <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <h3 className="font-bold text-[var(--ink-strong)]">¿Cómo se calcula?</h3>
      <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
        Tener todas las habilidades aporta 60 puntos. Los otros 40 comparan el
        contexto completo: profesión, experiencia, formación y responsabilidades
        del CV frente a la vacante.
      </p>
      <div className="mt-4 space-y-4">
        <Signal
          label="Habilidades requeridas"
          value={skillMatch}
          weight={60}
          description="Cobertura exacta de las skills de la oferta"
          color="var(--success)"
        />
        <Signal
          label="Contexto profesional"
          value={semanticMatch}
          weight={40}
          description="Afinidad entre el CV y el contenido de la vacante"
          color="var(--accent)"
        />
      </div>
    </section>
  );
}
