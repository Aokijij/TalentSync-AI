import { ArrowLeft, ArrowRight, Check, Eye, EyeOff, ShieldCheck } from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate, useLocation, useSearchParams } from "react-router-dom";
import { useState } from "react";
import { AuthFrame } from "../components/AuthFrame.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { getApiErrorMessage } from "../api/client.js";

export function RegisterPage() {
  const location = useLocation(), navigate = useNavigate(), [params] = useSearchParams();
  const invitation = params.get("invitation"), company = location.pathname.startsWith("/empresa"), role = company ? "company" : "candidate";
  const { register: createAccount, accessOptions } = useAuth();
  const { register, trigger, getValues, watch, formState: { errors } } = useForm({ defaultValues: { name: "", email: "", profession: "", skills: "", password: "", confirm_password: "" } });
  const [isSubmitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(0), [error, setError] = useState(""), [showPassword, setShowPassword] = useState(false);
  const steps = ["Tu cuenta", company ? invitation ? "Tu invitación" : "Tu empresa" : "Tu perfil", "Seguridad", "Confirmar"];
  const values = watch();
  const fields = [["name", "email"], company && !invitation ? ["company_name", "nit", "company_description"] : company ? [] : ["profession", "skills"], ["password", "confirm_password"]];
  if (invitation && !company) return <Navigate replace to={`/empresa/registro?invitation=${encodeURIComponent(invitation)}`} />;
  const field = (name, label, options = {}, props = {}) => <label className="block text-sm font-semibold">{label}<input className="field-control mt-2" {...props} {...register(name, options)} />{errors[name] && <span className="mt-1 block text-sm text-[var(--error)]">{errors[name].message}</span>}</label>;
  async function next(event) {
    event.preventDefault(); if (isSubmitting) return; setError("");
    if (step < 3) { if (await trigger(fields[step], { shouldFocus: true })) setStep(step + 1); return; }
    for (let index = 0; index < 3; index++) { if (!(await trigger(fields[index]))) { setStep(index); return; } }
    const data = getValues();
    setSubmitting(true);
    try {
      await createAccount({ name: data.name.trim(), email: data.email.trim(), password: data.password, role,
        ...(company ? invitation ? { invitation_token: invitation } : { company_name: data.company_name.trim(), nit: data.nit.trim(), company_description: data.company_description } : { profession: data.profession, skills: data.skills.split(",").map((skill) => skill.trim()).filter(Boolean) }) });
      navigate(company ? accessOptions.mode === "session" && accessOptions.company_mfa_required !== false ? `/seguridad${invitation ? `?invitation=${encodeURIComponent(invitation)}` : ""}` : "/empresa/equipo" : "/bienvenida");
    } catch (failure) { setError(getApiErrorMessage(failure, "No fue posible crear la cuenta. Revisa tus datos e inténtalo de nuevo.")); }
    finally { setSubmitting(false); }
  }
  return <AuthFrame company={company} registering>
    <div className="flex items-center justify-between gap-3"><span className="access-portal-tag">{company ? "Registro de empresa" : "Registro de candidato"}</span><Link className="text-sm text-[var(--accent)]" to={company ? "/empresa/login" : "/login"}>Ya tengo cuenta</Link></div>
    <h2 className="mt-5 text-3xl font-bold">{company ? "Construye tu espacio de contratación" : "Comienza tu próximo capítulo"}</h2>
    <p className="mt-2 text-sm text-[var(--muted)]">Cuatro pasos breves. Puedes volver y ajustar tus datos antes de confirmar.</p>
    <ol className="registration-steps" aria-label="Progreso de registro">{steps.map((title, index) => <li key={title} aria-current={step === index ? "step" : undefined} className={index <= step ? "reached" : ""}><span>{index < step ? <Check size={15} /> : index + 1}</span><small>{title}</small></li>)}</ol>
    <form onSubmit={next} noValidate className="space-y-5">
      <h3 className="text-xl font-bold" tabIndex={-1}>Paso {step + 1}: {steps[step]}</h3>
      {step === 0 && <>{field("name", company ? "Tu nombre como responsable" : "Nombre completo", { required: "Introduce tu nombre", minLength: { value: 2, message: "Usa al menos dos caracteres" }, maxLength: 120 }, { autoComplete: "name", placeholder: "Nombre y apellido" })}{field("email", company ? "Correo de tu cuenta empresarial" : "Correo electrónico", { required: "Introduce tu correo", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Introduce un correo válido" } }, { type: "email", autoComplete: "email", placeholder: company ? "nombre@tuempresa.com" : "tu@correo.com" })}<p className="text-xs text-[var(--muted)]">{company ? "Usa preferiblemente tu correo corporativo. La identidad de la empresa se verifica por separado." : "Aquí recibirás las comunicaciones sobre tus procesos."}</p></>}
      {step === 1 && (company ? invitation ? <div className="surface-card space-y-3 p-5"><ShieldCheck className="text-[var(--accent)]" /><h4 className="font-bold">Te unes a un equipo existente</h4><p className="text-sm">Usa el correo al que enviaron la invitación. No necesitas registrar otra empresa. El servidor comprobará la invitación al crear tu cuenta.</p></div> : <>{field("company_name", "Nombre de la empresa", { required: "Introduce el nombre de la empresa", minLength: { value: 2, message: "Usa al menos dos caracteres" }, maxLength: 180 }, { autoComplete: "organization", placeholder: "Nombre comercial" })}{field("nit", "NIT o identificación de la empresa", { required: "Introduce la identificación", minLength: { value: 3, message: "Revisa la identificación" }, maxLength: 80 }, { placeholder: "Ejemplo: 900123456-7" })}<label className="block text-sm font-semibold">¿A qué se dedica?<textarea className="field-control mt-2" rows={3} placeholder="Sector, actividad y qué ofrece tu equipo" {...register("company_description", { maxLength: 4000 })} /></label></> : <>{field("profession", "Profesión o cargo de interés", { required: "Indica tu profesión o cargo de interés", maxLength: 160 }, { placeholder: "Ejemplo: auxiliar contable, docente o diseñador" })}{field("skills", "Habilidades que ya tienes (opcional)", { maxLength: 2000 }, { placeholder: "Ejemplo: inventarios, Excel, atención al cliente" })}<p className="text-xs text-[var(--muted)]">Separa las habilidades con comas. Podrás completar tu experiencia y respaldarla después.</p></>)}
      {step === 2 && <><div className="flex justify-end"><button type="button" className="flex gap-2 text-sm text-[var(--accent)]" onClick={() => setShowPassword(!showPassword)}>{showPassword ? <EyeOff size={17} /> : <Eye size={17} />}{showPassword ? "Ocultar" : "Mostrar"} contraseñas</button></div>{field("password", "Crea tu contraseña", { required: "Crea una contraseña", minLength: { value: 12, message: "Usa al menos 12 caracteres" }, validate: (value) => new TextEncoder().encode(value).length <= 72 || "Máximo 72 bytes; reduce la longitud" }, { type: showPassword ? "text" : "password", autoComplete: "new-password" })}{field("confirm_password", "Repite tu contraseña", { required: "Repite la contraseña", validate: (value) => value === getValues("password") || "Las contraseñas no coinciden" }, { type: showPassword ? "text" : "password", autoComplete: "new-password" })}<p className="text-xs text-[var(--muted)]">Al menos 12 caracteres. {company && accessOptions.company_mfa_required !== false ? "Después del registro configurarás tu autenticador con un código QR." : "Puedes activar la verificación en dos pasos desde Seguridad de cuenta."}</p></>}
      {step === 3 && <div className="registration-review"><ShieldCheck size={26} /><h4 className="font-bold">Todo listo para crear tu {company ? "cuenta empresarial" : "perfil"}</h4><dl><dt>Responsable</dt><dd>{values.name}</dd><dt>Correo</dt><dd>{values.email}</dd><dt>{company ? "Organización" : "Profesión"}</dt><dd>{company ? invitation ? "Equipo de tu invitación" : values.company_name : values.profession}</dd>{!company && <><dt>Habilidades</dt><dd>{values.skills || "Las añadirás después"}</dd></>}</dl><p className="text-xs text-[var(--muted)]">{company ? "Podrás preparar tu perfil y enviar la verificación de tu organización al ingresar." : "Tu perfil comienza con habilidades declaradas. Las prácticas y evaluaciones te ayudarán a respaldarlas."}</p></div>}
      {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
      <div className="flex gap-3">{step > 0 && <button type="button" className="button-secondary" disabled={isSubmitting} onClick={() => { setStep(step - 1); setError(""); }}><ArrowLeft size={17} />Atrás</button>}<button className="button-primary flex-1" disabled={isSubmitting}>{isSubmitting ? "Creando cuenta…" : step === 3 ? "Confirmar y crear cuenta" : "Continuar"}<ArrowRight size={17} /></button></div>
    </form>
    <div className="access-switch"><span>{company ? "¿Buscas empleo?" : "¿Representas a una empresa?"}</span><Link to={company ? "/registro" : "/empresa/registro"}>{company ? "Crear perfil de candidato" : "Registrar una empresa"}</Link></div>
  </AuthFrame>;
}
