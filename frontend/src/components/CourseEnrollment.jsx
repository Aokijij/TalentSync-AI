import { CalendarDays, MapPin } from "lucide-react";
import { courseAvailability, courseModalities, enrollmentStatuses } from "../utils/learningPresentation.js";

export function CourseEnrollment({ resource, compact = false }) {
  if (!resource.url || !resource.availability?.checked_on && !resource.details?.enrollment) return null;
  const value = courseAvailability(resource);
  return <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-3 text-xs">
    <div className="flex flex-wrap items-center justify-between gap-2"><span className="inline-flex items-center gap-2 font-semibold"><CalendarDays size={14} />{enrollmentStatuses[value.status]}</span><span className="text-[var(--muted)]">{courseModalities[value.modality] || "Consultar modalidad"}</span></div>
    {!compact && <><p className="mt-2 flex items-start gap-2 text-[var(--muted)]"><MapPin size={14} className="shrink-0" />{value.region || "Consulta cobertura en el proveedor"}{value.minimum_age != null && ` · Desde ${value.minimum_age} años`}</p>{(value.opens_on || value.closes_on) && <p className="mt-2">{value.opens_on && `Apertura: ${value.opens_on}`}{value.closes_on && ` · Cierre: ${value.closes_on}`}</p>}<p className="mt-2 text-[var(--muted)]">{value.notes || "Confirma los requisitos, fechas y cupos en la fuente oficial."}</p><p className="mt-2 text-[var(--muted)]">{value.checked_on ? `Última consulta: ${value.checked_on}` : "Sin fecha de comprobación"}{value.stale && " · Información pendiente de actualizar"}</p></>}
  </section>;
}
