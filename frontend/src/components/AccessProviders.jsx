import { Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth.js";

export function AccessProviders() {
  const { accessOptions } = useAuth();
  return <div className="mt-5 space-y-2">
    {accessOptions.providers?.map((provider) => <button key={provider.id} type="button" disabled title={provider.reason} className="button-secondary w-full opacity-60">
      Continuar con {({ google: "Google", github: "GitHub", linkedin: "LinkedIn" })[provider.id]} · Próximamente
    </button>)}
    {accessOptions.providers?.length > 0 && <p className="text-xs text-[var(--muted)]">Por ahora puedes ingresar con correo. Los accesos sociales requieren configurar su integración.</p>}
    {accessOptions.local_mail && <Link className="block text-xs font-semibold text-[var(--accent)]" to="/desarrollo/correos">Abrir bandeja de correo local</Link>}
  </div>;
}
