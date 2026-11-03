import { useId, useState } from "react";
import { BriefcaseBusiness, Check, ChevronDown, Search } from "lucide-react";

export function VacancyPicker({ jobs, selected, query, onQuery, onSelect, loading, disabled, remaining = 0, onMore }) {
  const id = useId();
  const [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const choose = (job) => { onSelect(job); setOpen(false); setActive(-1); onQuery(""); };
  return <div className="vacancy-picker" onBlur={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false); }}>
    <label htmlFor={id}>Vacante para la búsqueda</label>
    <div className="vacancy-picker-control"><Search size={18} aria-hidden="true" /><input id={id} className="field-control" role="combobox" autoComplete="off" aria-expanded={open} aria-controls={`${id}-options`} aria-autocomplete="list" aria-activedescendant={open && active >= 0 && jobs[active] ? `${id}-${jobs[active].id}` : undefined} value={open ? query : selected?.title || ""} placeholder={selected ? `Cambiar: ${selected.title}` : "Busca y selecciona una de tus vacantes"} disabled={disabled} onFocus={() => { setOpen(true); setActive(-1); }} onChange={(event) => { onQuery(event.target.value); setActive(-1); setOpen(true); }} onKeyDown={(event) => {
      if (event.key === "Escape") { setOpen(false); setActive(-1); }
      if (jobs.length && ["ArrowDown", "ArrowUp"].includes(event.key)) { event.preventDefault(); setOpen(true); setActive((value) => value < 0 ? event.key === "ArrowDown" ? 0 : jobs.length - 1 : (value + (event.key === "ArrowDown" ? 1 : -1) + jobs.length) % jobs.length); }
      if (event.key === "Enter" && open) { event.preventDefault(); if (active >= 0 && jobs[active]) choose(jobs[active]); }
    }} /><ChevronDown size={17} aria-hidden="true" /></div>
    {open && <div className="vacancy-picker-menu"><p>{loading ? "Buscando vacantes…" : "Selecciona el cargo que quieres cubrir"}</p><ul id={`${id}-options`} role="listbox" aria-label="Mis vacantes">{jobs.map((job, index) => <li key={job.id} id={`${id}-${job.id}`} role="option" aria-selected={String(selected?.id) === String(job.id)} className={index === active ? "active" : ""} onMouseDown={(event) => { event.preventDefault(); choose(job); }}><BriefcaseBusiness size={17} /><span><strong>{job.title}</strong><small>{job.status === "active" ? "Activa" : job.status === "draft" ? "Borrador" : job.status === "closed" ? "Cerrada" : "Pausada"} · {job.applications_count || 0} postulaciones</small></span>{String(selected?.id) === String(job.id) && <Check size={17} />}</li>)}</ul>{!jobs.length && !loading && <p>No hay vacantes con ese nombre.</p>}{remaining > 0 && <button type="button" className="button-secondary button-sm" onClick={onMore}>Cargar más ({remaining})</button>}</div>}
    {selected && <p className="vacancy-picker-current"><Check size={14} />Buscando para: <strong>{selected.title}</strong></p>}
  </div>;
}
