import {
  BriefcaseBusiness,
  Building2,
  LockKeyhole,
  Mail,
  UserRound,
} from "lucide-react";
import { useForm, useWatch } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";

import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { ThemeToggle } from "../components/ThemeToggle.jsx";

export function RegisterPage() {
  const {
    control,
    register,
    handleSubmit,
    getValues,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm({ defaultValues: { role: "candidate", skills: "" } });
  const role = useWatch({ control, name: "role" });
  const { register: createAccount } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const isCompany = role === "company";

  async function onSubmit(values) {
    setError("");
    const payload = {
      ...values,
      skills: values.skills
        ? values.skills
            .split(",")
            .map((skill) => skill.trim())
            .filter(Boolean)
        : [],
    };
    try {
      const user = await createAccount(payload);
      navigate(user.role === "company" ? "/empresa" : "/candidato");
    } catch (requestError) {
      const detail = requestError.response?.data?.detail;
      setError(
        Array.isArray(detail)
          ? detail.map((item) => item.msg).join(". ")
          : detail || "No fue posible crear la cuenta. Inténtalo de nuevo.",
      );
    }
  }

  return (
    <main className="auth-shell relative">
      <ThemeToggle compact className="fixed right-5 top-5 z-20" />
      <section className="auth-stage">
        <aside
          className="auth-brand-panel"
          aria-label="Beneficios de TalentSync"
        >
          <div>
            <BrandLogo
              size="lg"
              subtitle="Tu siguiente paso"
              tone="inverse"
            />
            <p className="mt-16 text-sm font-bold uppercase tracking-[0.16em] text-sky-300">
              Registro guiado
            </p>
            <h1 className="mt-4 max-w-md text-balance text-4xl font-bold text-white">
              {isCompany
                ? "Construye un proceso de selección con evidencia."
                : "Convierte tu experiencia en oportunidades concretas."}
            </h1>
            <p className="mt-5 max-w-md text-base leading-7 text-sky-100">
              {isCompany
                ? "Publica vacantes, identifica compatibilidad y gestiona cada proceso desde un solo lugar."
                : "Agrega una base profesional hoy; podrás enriquecer tu perfil y CV después."}
            </p>
          </div>
          <div className="auth-signal-card">
            <p className="text-sm font-bold text-white">
              Un perfil, decisiones más precisas
            </p>
            <p className="mt-1 text-sm leading-5 text-sky-100">
              Mantén tus habilidades actualizadas para que las recomendaciones sean
              realmente útil.
            </p>
          </div>
        </aside>
        <div className="auth-form-panel">
          <div className="auth-form">
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="section-kicker">Crear cuenta</p>
                <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
                  Comienza en TalentSync
                </h2>
              </div>
              <Link
                className="text-sm font-bold text-[var(--accent)] underline-offset-4 hover:underline focus-ring"
                to="/login"
              >
                Ingresar
              </Link>
            </div>
            <p className="mt-3 text-base leading-6 text-[var(--muted)]">
              Elige tu espacio de trabajo y completa los datos esenciales.
            </p>
            <form
              className="mt-7 space-y-5"
              onSubmit={handleSubmit(onSubmit)}
              noValidate
            >
              <input type="hidden" {...register("role")} />
              <div className="role-switch" aria-label="Tipo de cuenta">
                <button
                  type="button"
                  aria-pressed={role === "candidate"}
                  onClick={() => setValue("role", "candidate")}
                >
                  <UserRound
                    className="mr-2 inline"
                    size={17}
                    aria-hidden="true"
                  />
                  Candidato
                </button>
                <button
                  type="button"
                  aria-pressed={role === "company"}
                  onClick={() => setValue("role", "company")}
                >
                  <Building2
                    className="mr-2 inline"
                    size={17}
                    aria-hidden="true"
                  />
                  Empresa
                </button>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Nombre completo" error={errors.name?.message}>
                  <input
                    className="field-control"
                    autoComplete="name"
                    placeholder="Tu nombre"
                    {...register("name", {
                      required: "El nombre es obligatorio",
                    })}
                  />
                </Field>
                <Field label="Correo electrónico" error={errors.email?.message}>
                  <div className="field-control flex items-center">
                    <Mail
                      size={18}
                      className="mr-3 shrink-0 text-[var(--accent)]"
                      aria-hidden="true"
                    />
                    <input
                      className="min-h-0 p-0"
                      type="email"
                      autoComplete="email"
                      placeholder="correo@ejemplo.com"
                      {...register("email", {
                        required: "El correo es obligatorio",
                      })}
                    />
                  </div>
                </Field>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Field label="Contraseña" error={errors.password?.message}>
                  <div className="field-control flex items-center">
                    <LockKeyhole
                      size={18}
                      className="mr-3 shrink-0 text-[var(--accent)]"
                      aria-hidden="true"
                    />
                    <input
                      className="min-h-0 p-0"
                      type="password"
                      autoComplete="new-password"
                      placeholder="Mínimo 8 caracteres"
                      {...register("password", {
                        required: "La contraseña es obligatoria",
                        minLength: {
                          value: 8,
                          message: "Usa al menos 8 caracteres",
                        },
                      })}
                    />
                  </div>
                </Field>
                <Field
                  label="Confirmar contraseña"
                  error={errors.confirm_password?.message}
                >
                  <input
                    className="field-control"
                    type="password"
                    autoComplete="new-password"
                    placeholder="Repite tu contraseña"
                    {...register("confirm_password", {
                      required: "Confirma tu contraseña",
                      validate: (value) =>
                        value === getValues("password") ||
                        "Las contraseñas no coinciden",
                    })}
                  />
                </Field>
              </div>
              {isCompany ? (
                <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
                  <p className="text-sm font-bold text-[var(--ink-strong)]">
                    Información de la empresa
                  </p>
                  <div className="mt-4 grid gap-4 sm:grid-cols-2">
                    <Field
                      label="Nombre de la empresa"
                      error={errors.company_name?.message}
                    >
                      <input
                        className="field-control"
                        placeholder="TalentSoft Labs"
                        {...register("company_name", {
                          required: "El nombre de la empresa es obligatorio",
                        })}
                      />
                    </Field>
                    <Field label="NIT" error={errors.nit?.message}>
                      <input
                        className="field-control"
                        placeholder="900123456-7"
                        {...register("nit", {
                          required: "El NIT es obligatorio",
                        })}
                      />
                    </Field>
                  </div>
                  <Field label="Descripción" className="mt-4">
                    <textarea
                      className="field-control min-h-24 resize-y"
                      placeholder="Sector, cultura y propuesta de valor…"
                      {...register("company_description")}
                    />
                  </Field>
                </section>
              ) : (
                <section className="rounded-xl border border-[var(--line)] bg-[var(--surface-subtle)] p-4">
                  <p className="text-sm font-bold text-[var(--ink-strong)]">
                    Base de tu perfil
                  </p>
                  <div className="mt-4 space-y-4">
                    <Field label="Profesión">
                      <input
                        className="field-control"
                        placeholder="Ej. auxiliar administrativo o diseñador"
                        {...register("profession")}
                      />
                    </Field>
                    <Field label="Habilidades">
                      <input
                        className="field-control"
                        placeholder="Ej. comunicación, organización, trabajo en equipo"
                        {...register("skills")}
                      />
                      <p className="mt-1 text-xs text-[var(--muted)]">
                        Sepáralas con comas.
                      </p>
                    </Field>
                  </div>
                </section>
              )}
              {error ? (
                <p
                  role="alert"
                  className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm font-medium text-[var(--error)]"
                >
                  {error}
                </p>
              ) : null}
              <button
                className="button-primary pressed focus-ring w-full"
                type="submit"
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  "Creando cuenta…"
                ) : (
                  <>
                    {isCompany ? (
                      <Building2 size={17} aria-hidden="true" />
                    ) : (
                      <BriefcaseBusiness size={17} aria-hidden="true" />
                    )}
                    Crear cuenta
                  </>
                )}
              </button>
            </form>
          </div>
        </div>
      </section>
    </main>
  );
}

function Field({ label, error, className = "", children }) {
  return (
    <label
      className={`block text-sm font-semibold text-[var(--ink-strong)] ${className}`}
    >
      {label}
      <div className="mt-2">{children}</div>
      {error ? (
        <span
          role="alert"
          className="mt-1 block text-sm font-medium text-[var(--error)]"
        >
          {error}
        </span>
      ) : null}
    </label>
  );
}
