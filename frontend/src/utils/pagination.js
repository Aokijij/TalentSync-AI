export function pageNumber(value, fallback = 1) {
  const number = Number(value);
  return Number.isFinite(number) && number >= 1 ? Math.floor(number) : fallback;
}

export function paginationState(total, page, pageSize) {
  const count = Math.max(0, Number.isFinite(Number(total)) ? Math.floor(Number(total)) : 0);
  const size = pageNumber(pageSize, 12);
  const pages = Math.max(1, Math.ceil(count / size));
  const current = Math.min(pageNumber(page), pages);
  return { page: current, pages, pageSize: size, start: count ? (current - 1) * size + 1 : 0, end: Math.min(current * size, count), offset: (current - 1) * size, total: count };
}

export function totalPages(items, pageSize) {
  return paginationState(items.length, 1, pageSize).pages;
}

export function pageItems(items, page, pageSize) {
  const state = paginationState(items.length, page, pageSize);
  return items.slice(state.offset, state.end);
}
