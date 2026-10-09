import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({ page, pages, total, pageSize, onChange, label }) {
  const safePage = Math.max(1, Math.min(page, pages));
  return <nav aria-label={label} className="directory-pagination"><p>{total ? (safePage - 1) * pageSize + 1 : 0}–{Math.min(safePage * pageSize, total)} de {total}</p><div><button className="button-secondary button-sm" disabled={safePage === 1} onClick={() => onChange(safePage - 1)}><ChevronLeft size={15} />Anterior</button><span aria-live="polite">Página {safePage} de {pages}</span><button className="button-secondary button-sm" disabled={safePage === pages} onClick={() => onChange(safePage + 1)}>Siguiente<ChevronRight size={15} /></button></div></nav>;
}
