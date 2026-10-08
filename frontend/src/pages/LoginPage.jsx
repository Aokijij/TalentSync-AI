import { ArrowRight, Eye, EyeOff, LockKeyhole, Mail } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "../hooks/useAuth.js";
import { AuthFrame } from "../components/AuthFrame.jsx";
import { MfaChallenge } from "../components/MfaChallenge.jsx";
import { AccessProviders } from "../components/AccessProviders.jsx";
import { getApiErrorMessage } from "../api/client.js";

export function LoginPage() {
  const { register, handleSubmit, resetField, formState: { errors, isSubmitting } } = useForm();
  const { login, accessOptions } = useAuth();
  const navigate = useNavigate(), location = useLocation();
  const company = location.pathname.startsWith("/empresa"), portal = company ? "company" : "candidate";
  const [credentials, setCredentials] = useState(null), [showPassword, setShowPassword] = useState(false), [error, setError] = useState(""), [verifying, setVerifying] = useState(false);
  async function authenticate(values, code) {
    setError("");
    try {
      const user = await login(values.email, values.password, { code, remember: values.remember, portal });
      if (user.mfa_required) { setCredentials({ ...values }); resetField("password"); return; }
      setCredentials(null);
      if (accessOptions.mode === "session" && company && !user.mfa_enabled) { navigate("/seguridad"); return; }
      const from = location.state?.from;
      const allowed = typeof from === "string" && from.startsWith("/") && !from.startsWith("//") && (company ? from.startsWith("/empresa") : !/^\/(empresa|admin|administracion)/.test(from));
      navigate(allowed ? from : company ? "/empresa" : "/candidato", { replace: true });
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos validar este acceso. Revisa tu cuenta y el portal seleccionado.")); }
  }
  return <AuthFrame company={company}>
    {credentials ? <MfaChallenge email={credentials.email} busy={verifying} error={error} onBack={() => { setCredentials(null); setError(""); }} onVerify={async (code) => { setVerifying(true); await authenticate(credentials, code); setVerifying(false); }} /> : <>
      <div className="access-portal-tag">{company ? "Acceso de empresa" : "Acceso de candidato"}</div>
      <h2 className="mt-5 text-3xl font-bold sm:text-4xl">{company ? "Bienvenido a tu equipo" : "Qué bueno verte de nuevo"}</h2>
      <p className="mt-3 text-[var(--muted)]">{company ? "Gestiona oportunidades y personas desde tu espacio empresarial." : "Continúa con tus oportunidades y tu desarrollo profesional."}</p>
      <form className="mt-7 space-y-5" onSubmit={handleSubmit((values) => authenticate(values))} noValidate>
        <label className="block text-sm font-semibold">{company ? "Correo de tu cuenta empresarial" : "Correo electrónico"}<div className="field-control mt-2 flex items-center gap-3"><Mail size={18} className="shrink-0 text-[var(--accent)]" /><input className="min-h-0 p-0" type="email" autoComplete="username" placeholder={company ? "nombre@tuempresa.com" : "tu@correo.com"} {...register("email", { required: "Introduce tu correo", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Revisa el formato del correo" } })} /></div>{errors.email && <span className="text-[var(--error)]">{errors.email.message}</span>}</label>
        <label className="block text-sm font-semibold">Contraseña<div className="field-control mt-2 flex items-center gap-3"><LockKeyhole size={18} className="shrink-0 text-[var(--accent)]" /><input className="min-h-0 p-0" type={showPassword ? "text" : "password"} autoComplete="current-password" placeholder="Tu contraseña" {...register("password", { required: "Introduce tu contraseña" })} /><button type="button" aria-label={showPassword ? "Ocultar contraseña" : "Mostrar contraseña"} onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={18} /> : <Eye size={18} />}</button></div>{errors.password && <span className="text-[var(--error)]">{errors.password.message}</span>}</label>
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm">{!company && <label className="flex items-center gap-2"><input type="checkbox" {...register("remember")} />Recordarme en este dispositivo</label>}<Link className="text-[var(--accent)]" to="/recuperar-acceso">Olvidé mi contraseña</Link></div>
        {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
        <button className="button-primary w-full" disabled={isSubmitting}>{isSubmitting ? "Validando…" : <>{company ? "Entrar a mi empresa" : "Entrar a mi espacio"}<ArrowRight size={18} /></>}</button>
      </form>
      {!company && accessOptions.providers.some((provider) => provider.enabled) && <div className="mt-5"><AccessProviders availableOnly /></div>}
      <p className="mt-6 text-sm">{company ? "¿Tu empresa aún no tiene cuenta?" : "¿Es tu primera vez aquí?"} <Link className="font-bold text-[var(--accent)]" to={company ? "/empresa/registro" : "/registro"}>{company ? "Registrar mi empresa" : "Crear mi perfil"}</Link></p>
      <div className="access-switch"><span>{company ? "¿Buscas empleo?" : "¿Quieres contratar?"}</span><Link to={company ? "/login" : "/empresa/login"}>{company ? "Ir al acceso de candidato" : "Ir al acceso de empresa"}<ArrowRight size={16} /></Link></div>
    </>}
  </AuthFrame>;
}
