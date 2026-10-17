import { AcademicMatchDetails } from "./AcademicMatchDetails.jsx";
import { useId, useState } from "react";
import { CircleHelp } from "lucide-react";

const improvements = {
  skills: "Compara los requisitos de la vacante con tus habilidades. Añade a tu perfil solo las que ya tienes, usando nombres claros, y practica las que te falten. Puedes incorporar habilidades desde tus evidencias en Mi perfil.",
  context: "Describe tus cargos, responsabilidades y resultados con ejemplos concretos relacionados con esta vacante. Completa tu profesión y experiencia; evita añadir palabras o experiencia que no te correspondan.",
  education: "Completa el título, institución y estado de tus estudios. La formación en curso debe indicarse como tal. Revisa el nivel y área que pide la empresa: declarar un estudio no equivale a haberlo terminado.",
  certifications: "Añade los cursos y certificados que hayas obtenido, con nombre, emisor y habilidades relacionadas. Si tienes un documento público puedes adjuntarlo. TalentSync lo registra como aportado, sin validar su autenticidad.",
  languages: "Registra los idiomas y tu nivel real en Mi perfil. Se compara con el nivel mínimo solicitado. Para mejorar, refuerza el idioma requerido y actualiza tu nivel cuando hayas progresado.",
};

function Signal({ signalKey, label, value, weight, description, color }) {
  const [helpOpen, setHelpOpen] = useState(false);
  const helpId = useId();
  const safe = Math.max(0, Math.min(100, Number(value ?? 0)));
  return (
    <div className="match-signal" onMouseEnter={() => setHelpOpen(true)} onMouseLeave={() => setHelpOpen(false)} onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setHelpOpen(false); }}>
      <div className="flex items-end justify-between gap-4">
        <div>
          <div className="match-signal-label"><p className="text-sm font-bold text-[var(--ink-strong)]">{label}</p><button type="button" className="match-help-trigger" aria-label={`Cómo mejorar: ${label}`} aria-expanded={helpOpen} aria-describedby={helpOpen ? helpId : undefined} onFocus={(event) => { if (event.currentTarget.matches(":focus-visible")) setHelpOpen(true); }} onClick={() => setHelpOpen(!helpOpen)} onKeyDown={(event) => { if (event.key === "Escape") { setHelpOpen(false); event.stopPropagation(); } }}><CircleHelp size={15} aria-hidden="true" /></button></div>
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
      {helpOpen && <div className="match-signal-help" id={helpId} role="tooltip"><strong>Cómo mejorar {label.toLocaleLowerCase("es")}</strong><p>{improvements[signalKey] || "Revisa los requisitos de la vacante y completa la información real de tu perfil relacionada con esta señal."}</p><small>Esta señal aporta hasta {weight}% del total. Completar datos no garantiza una puntuación concreta.</small></div>}
      <div className="mt-2 h-2 overflow-hidden rounded-full bg-[var(--surface-hover)]">
        <div
          className="h-full rounded-full"
          style={{ width: `${safe}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

export function MatchBreakdown({ skillMatch = 0, semanticMatch = 0, languageMatch = null, details = null }) {
  const hasLanguages = languageMatch !== null && languageMatch !== undefined;
  if (details?.components?.length) return <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4"><h3 className="font-bold">¿Cómo se calcula?</h3><p className="mt-1 text-xs text-[var(--muted)]">Cada señal aporta su puntuación multiplicada por el peso. Pasa por una señal o pulsa su ayuda para saber cómo mejorarla.</p><div className="mt-4 space-y-4">{details.components.map((row) => <Signal key={row.key} signalKey={row.key} label={row.label} value={row.score} weight={Math.round(row.weight * 100)} description={`Aporta ${row.points.toFixed(1)} puntos`} color="var(--accent)" />)}</div><AcademicMatchDetails value={details.education_requirement} /><p className="mt-3 text-xs text-[var(--muted)]">Las preferencias se muestran por separado. Los datos externos incompletos reducen el resultado.</p></section>;
  return (
    <section className="rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
      <h3 className="font-bold text-[var(--ink-strong)]">¿Cómo se calcula?</h3>
      <p className="mt-1 text-xs leading-5 text-[var(--muted)]">
        {hasLanguages ? "Las habilidades aportan hasta 60 puntos, tu trayectoria hasta 30 y los idiomas hasta 10. El nivel registrado se compara con el mínimo solicitado." : "Tener todas las habilidades aporta 60 puntos. Los otros 40 comparan tu profesión, cargos, responsabilidades, formación y logros con la vacante."}
      </p>
      <div className="mt-4 space-y-4">
        <Signal
          signalKey="skills"
          label="Habilidades requeridas"
          value={skillMatch}
          weight={60}
          description="Cuántas habilidades solicitadas ya tienes"
          color="var(--success)"
        />
        <Signal
          signalKey="context"
          label="Contexto profesional"
          value={semanticMatch}
          weight={hasLanguages ? 30 : 40}
          description="Relación entre tu trayectoria y las funciones del cargo"
          color="var(--accent)"
        />
        {hasLanguages && <Signal signalKey="languages" label="Idiomas" value={languageMatch} weight={10} description="Tu nivel frente al mínimo solicitado por la empresa" color="var(--success)" />}
      </div>
    </section>
  );
}
