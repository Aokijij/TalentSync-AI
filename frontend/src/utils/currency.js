export function currencyDigits(value) {
  const digits = String(value ?? "").replace(/\D/g, "");
  return digits ? Number(digits) : null;
}

export function formatCurrencyInput(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount <= 0) return "";
  return Math.trunc(amount).toLocaleString("es-CO");
}
