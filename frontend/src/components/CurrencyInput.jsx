import { currencyDigits, formatCurrencyInput } from "../utils/currency.js";

export function CurrencyInput({ value, onChange, className = "field-control", placeholder = "0", ...props }) {
  return (
    <div className="relative">
      <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-sm text-[var(--muted)]">$</span>
      <input
        {...props}
        className={`${className} !pl-7`}
        type="text"
        inputMode="numeric"
        value={formatCurrencyInput(value)}
        placeholder={placeholder}
        onChange={(event) => onChange(currencyDigits(event.target.value))}
      />
    </div>
  );
}
