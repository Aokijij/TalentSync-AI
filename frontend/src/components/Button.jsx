export function Button({
  children,
  variant = "primary",
  size = "md",
  disabled = false,
  loading = false,
  className = "",
  type = "button",
  ...props
}) {
  const variantClass =
    {
      primary: "button-primary",
      secondary: "button-secondary",
      outline: "button-outline",
      ghost: "button-ghost",
    }[variant] ?? "button-primary";

  const sizeClass =
    { sm: "button-sm", md: "button-md", lg: "button-lg" }[size] ?? "button-md";

  return (
    <button
      type={type}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      className={`${variantClass} ${sizeClass} pressed focus-ring ${className}`}
      {...props}
    >
      {loading ? (
        <span
          className="h-4 w-4 animate-spin rounded-full border-2 border-current border-r-transparent"
          aria-hidden="true"
        />
      ) : null}
      <span>{children}</span>
    </button>
  );
}
