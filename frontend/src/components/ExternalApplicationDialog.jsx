import { ExternalLink, Info, X } from "lucide-react";
import { externalPortal } from "../utils/externalPortal.js";
import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function ExternalApplicationDialog({ job, onClose }) {
  const [check, setCheck] = useState(null), [error, setError] = useState("");
  useEffect(() => {
    if (!job?.id) return;
    let active = true;
    api.post(`/jobs/${job.id}/external-access`, {}, { __quiet: true }).then(({ data }) => { if (active) setCheck(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [job?.id]);
  if (!job?.external_url) return null;

  const source = externalPortal(job);

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-slate-950/70 p-4 backdrop-blur-xs">
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
          <p role={error ? "alert" : "status"} className={`mt-3 text-sm font-semibold ${error ? "text-[var(--error)]" : "text-[var(--accent)]"}`}>{error || (check ? "Vigencia confirmada en la fuente original. Revisa sus condiciones antes de compartir datos." : "Comprobando que la oferta siga abierta…")}</p>
        </div>

        <footer className="mt-6 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <button type="button" className="button-secondary" onClick={onClose}>
            Quedarme en TalentSync
          </button>
          {check?.available && !error ? <a
            className="button-primary"
            href={check.url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={onClose}
          >
            <ExternalLink size={16} />
            Continuar a {source}
          </a> : <button type="button" className="button-primary" disabled>{error ? "Oferta sin confirmar" : "Comprobando…"}</button>}
        </footer>
      </section>
    </div>
  );
}
