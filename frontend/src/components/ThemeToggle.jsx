import { Moon, Sun } from "lucide-react";
import { useTheme } from "../hooks/useTheme.js";

export function ThemeToggle({ compact = false, className = "" }) {
  const { theme, toggleTheme } = useTheme();
  const dark = theme === "dark";
  return (
    <button
      type="button"
      className={`${compact ? "button-secondary !h-11 !w-11 !p-0" : "flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm font-semibold text-[var(--sidebar-ink)] transition-colors hover:bg-white/10"} ${className}`}
      onClick={toggleTheme}
      aria-label={dark ? "Activar modo claro" : "Activar modo oscuro"}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
      {compact ? null : <span>{dark ? "Modo claro" : "Modo oscuro"}</span>}
    </button>
  );
}
