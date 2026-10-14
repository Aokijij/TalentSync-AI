export function groupWritingHistory(rows) {
  const groups = new Map();
  for (const row of rows) {
    const record = row.record || {};
    const key = JSON.stringify([record.role, record.company, record.start_date || record.start_year, record.end_date || record.end_year, record.is_current]);
    if (!groups.has(key)) groups.set(key, { key, record, rows: [] });
    groups.get(key).rows.push(row);
  }
  return [...groups.values()].map((group) => ({ ...group, rows: [...group.rows].sort((a, b) => String(b.created_at).localeCompare(String(a.created_at))) }));
}
