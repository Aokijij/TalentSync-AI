import { useId, useState } from "react";

export function Input({
  type = "text",
  label,
  placeholder,
  value,
  onChange,
  error,
  helperText,
  disabled = false,
  className = "",
  size = "md",
  id: suppliedId,
  ...props
}) {
  const generatedId = useId();
  const inputId = suppliedId ?? generatedId;
  const [touched, setTouched] = useState(false);
  const hasError = Boolean(error && touched);
  const helpId = error || helperText ? `${inputId}-help` : undefined;
  const sizeClass =
    { sm: "input-sm", md: "input-md", lg: "input-lg" }[size] ?? "input-md";

  return (
    <div className="space-y-1.5">
      {label ? (
        <label
          htmlFor={inputId}
          className="block text-sm font-semibold text-[var(--ink-strong)]"
        >
          {label}
        </label>
      ) : null}
      <input
        id={inputId}
        type={type}
        placeholder={placeholder}
        value={value}
        onChange={onChange}
        onBlur={() => setTouched(true)}
        disabled={disabled || props.readOnly}
        aria-invalid={hasError || undefined}
        aria-describedby={helpId}
        className={`field-control ${sizeClass} ${hasError ? "field-control-error" : ""} ${className}`}
        {...props}
      />
      {hasError ? (
        <p
          id={helpId}
          role="alert"
          className="text-sm font-medium text-[var(--error)]"
        >
          {error}
        </p>
      ) : null}
      {!hasError && helperText ? (
        <p id={helpId} className="text-sm text-[var(--muted)]">
          {helperText}
        </p>
      ) : null}
    </div>
  );
}
