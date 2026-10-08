import { ArrowRight, LockKeyhole, Mail, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";

import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { ThemeToggle } from "../components/ThemeToggle.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { api, getApiErrorMessage } from "../api/client.js";

export function AdminLoginPage() {
  const { user, login, accessOptions } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [mfaRequired, setMfaRequired] = useState(false);
  const [corporate, setCorporate] = useState(null);
  const [corporateBusy, setCorporateBusy] = useState(false);
  useEffect(() => { api.get("/auth/admin-sso/options", { __skipSessionEvent: true }).then(({ data }) => setCorporate(data)).catch(() => setError("No pudimos consultar los métodos de acceso administrativo.")); }, []);
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();

  if (user) return <Navigate to={user.role === "admin" ? "/admin" : "/"} replace />;

  async function onSubmit(values) {
    setError("");
    try {
      const result = await login(values.email, values.password, { admin: true, code: values.code });
      if (result.mfa_required) { setMfaRequired(true); return; }
      navigate(accessOptions.mode !== "session" || result.mfa_enabled ? "/admin" : "/seguridad", { replace: true });
    } catch {
      setError("No fue posible validar el acceso administrativo.");
    }
  }
  async function startCorporate() {
    setCorporateBusy(true); setError("");
    try { const { data } = await api.post("/auth/admin-sso/start"); window.location.assign(data.url); }
    catch (failure) { setError(getApiErrorMessage(failure)); setCorporateBusy(false); }
  }

  return (
    <main className="auth-shell role-admin relative">
      <ThemeToggle compact className="fixed right-5 top-5 z-20" />
      <section className="auth-stage">
        <aside className="auth-brand-panel" aria-label="Acceso administrativo">
          <div>
            <BrandLogo size="lg" subtitle="Administración segura" tone="inverse" />
            <p className="mt-16 text-sm font-bold uppercase tracking-[0.16em] text-violet-200">
              Acceso restringido
            </p>
            <h1 className="mt-4 max-w-md text-balance text-4xl font-bold text-white">
              Control de la plataforma en un espacio independiente.
            </h1>
            <p className="mt-5 max-w-md text-base leading-7 text-violet-100">
              Esta dirección está reservada para cuentas administradoras autorizadas.
            </p>
          </div>
          <div className="auth-signal-card flex gap-3">
            <ShieldCheck className="mt-0.5 shrink-0 text-violet-300" size={21} />
            <div>
              <p className="font-bold text-white">Sesión administrativa</p>
              <p className="mt-1 text-sm text-violet-100">
                Las cuentas de candidatos y empresas no pueden ingresar por este acceso.
              </p>
            </div>
          </div>
        </aside>
        <div className="auth-form-panel">
          <div className="auth-form">
            <p className="section-kicker">Administración</p>
            <h2 className="mt-3 text-3xl font-bold sm:text-4xl">Iniciar sesión</h2>
            <p className="mt-3 text-[var(--muted)]">
              {corporate?.required ? "Utiliza tu cuenta corporativa aprovisionada para administración." : "Ingresa las credenciales de una cuenta administradora."}
            </p>
            {!corporate && !error && <p className="mt-5 text-sm">Consultando métodos de acceso…</p>}
            {(corporate?.enabled || corporate?.required) && <div className="mt-6 space-y-3"><button className="button-primary w-full" type="button" disabled={!corporate.enabled || corporateBusy} onClick={startCorporate}>{corporateBusy ? "Abriendo proveedor…" : `Continuar con ${corporate.provider}`}</button><p className="text-xs text-[var(--muted)]">{corporate.enabled ? "Solo admite cuentas corporativas vinculadas previamente a una cuenta administradora." : "El acceso corporativo obligatorio aún no está configurado. Contacta al responsable del entorno."}</p></div>}
            {error && <p role="alert" className="mt-4 text-sm text-[var(--error)]">{error}</p>}
            {corporate && !corporate.required && <form className="mt-8 space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
              {mfaRequired && <label className="block text-sm font-semibold">Código de autenticación o recuperación<input className="field-control mt-2" autoComplete="one-time-code" {...register("code", { required: "Introduce tu código" })} /></label>}
              <label className="block text-sm font-semibold">
                Correo administrativo
                <div className="field-control mt-2 flex items-center">
                  <Mail size={18} className="mr-3 text-[var(--accent)]" />
                  <input
                    className="min-h-0 p-0"
                    type="email"
                    autoComplete="username"
                    {...register("email", { required: "El correo es obligatorio" })}
                  />
                </div>
                {errors.email ? <span className="mt-1 block text-sm text-[var(--error)]">{errors.email.message}</span> : null}
              </label>
              <label className="block text-sm font-semibold">
                Contraseña
                <div className="field-control mt-2 flex items-center">
                  <LockKeyhole size={18} className="mr-3 text-[var(--accent)]" />
                  <input
                    className="min-h-0 p-0"
                    type="password"
                    autoComplete="current-password"
                    {...register("password", { required: "La contraseña es obligatoria" })}
                  />
                </div>
                {errors.password ? <span className="mt-1 block text-sm text-[var(--error)]">{errors.password.message}</span> : null}
              </label>
              <button className="button-primary w-full" type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Validando…" : <>Entrar al panel <ArrowRight size={17} /></>}
              </button>
            </form>}
          </div>
        </div>
      </section>
    </main>
  );
}
