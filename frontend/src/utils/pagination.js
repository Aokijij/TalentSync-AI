export function totalPages(items, pageSize) {
  return Math.max(1, Math.ceil(items.length / pageSize));
}

export function pageItems(items, page, pageSize) {
  const safePage = Math.max(1, Math.min(page, totalPages(items, pageSize)));
  return items.slice((safePage - 1) * pageSize, safePage * pageSize);
}
