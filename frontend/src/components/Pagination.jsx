import { ChevronLeft, ChevronRight } from "lucide-react";
import { paginationState } from "../utils/pagination.js";

export function Pagination({ page, total, pageSize, onChange, label, busy = false }) {
  const state = paginationState(total, page, pageSize);
  return <nav aria-label={label} className="directory-pagination"><p>{state.start}–{state.end} de {state.total}</p><div><button type="button" className="button-secondary button-sm" disabled={busy || state.page === 1} onClick={() => onChange(state.page - 1)}><ChevronLeft size={15} />Anterior</button><span aria-live="polite">Página {state.page} de {state.pages}</span><button type="button" className="button-secondary button-sm" disabled={busy || state.page === state.pages} onClick={() => onChange(state.page + 1)}>Siguiente<ChevronRight size={15} /></button></div></nav>;
}
