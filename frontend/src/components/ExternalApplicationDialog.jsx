import { ExternalLink, Info, X } from "lucide-react";

export function ExternalApplicationDialog({ job, onClose }) {
  if (!job?.external_url) return null;

  const source = job.source_name || "el portal de origen";

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/70 p-4 backdrop-blur-sm">
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="external-application-title"
        className="w-full max-w-lg rounded-[var(--radius-2xl)] border border-[var(--line)] bg-[var(--surface)] p-6 shadow-2xl"
      >
        <header className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <span className="grid h-11 w-11 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]">
              <Info size={21} />
            </span>
            <div>
              <p className="section-kicker">Postulación externa</p>
              <h2 id="external-application-title" className="mt-1 text-xl font-bold">
                Continuarás en {source}
              </h2>
            </div>
          </div>
          <button
            type="button"
            className="button-secondary !h-10 !w-10 !p-0"
            onClick={onClose}
            aria-label="Cerrar advertencia"
          >
            <X size={18} />
          </button>
        </header>

        <div className="mt-5 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
          <p className="text-sm leading-6 text-[var(--muted)]">
            TalentSync solo recibe un resumen de esta oferta y no puede registrar
            la postulación dentro de la plataforma. Revisa en el sitio original la
            vigencia, los requisitos, el salario y la identidad del empleador antes
            de compartir tus datos.
          </p>
        </div>

        <footer className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" className="button-secondary" onClick={onClose}>
            Quedarme en TalentSync
          </button>
          <a
            className="button-primary"
            href={job.external_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
          >
            <ExternalLink size={16} />
            Continuar a {source}
          </a>
        </footer>
      </section>
    </div>
  );
}
