import {
  ArrowRight,
  BrainCircuit,
  BriefcaseBusiness,
  Building2,
  LockKeyhole,
  Mail,
  ScanSearch,
  UsersRound,
} from "lucide-react";
import { useForm } from "react-hook-form";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";

import { BrandLogo } from "../components/brand/BrandLogo.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { ThemeToggle } from "../components/ThemeToggle.jsx";
import { api } from "../api/client.js";

const signals = [
  {
    icon: BrainCircuit,
    title: "Compatibilidad explicada",
    detail: "Habilidades y contexto, no solo palabras clave.",
  },
  {
    icon: ScanSearch,
    title: "Análisis de hoja de vida",
    detail: "Convierte tu experiencia en señales accionables.",
  },
  {
    icon: BriefcaseBusiness,
    title: "Tres espacios",
    detail: "Candidato, empresa y administración en una sola plataforma.",
  },
];

export function LoginPage() {
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm();
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api
      .get("/jobs/public-stats")
      .then(({ data }) => setStats(data))
      .catch(() => setStats(null));
  }, []);

  async function onSubmit(values) {
    setError("");
    try {
      const user = await login(values.email, values.password);
      navigate(
        user.role === "company"
          ? "/empresa"
          : user.role === "admin"
            ? "/admin"
            : "/candidato",
      );
    } catch {
      setError(
        "No pudimos validar tus credenciales. Revisa el correo y la contraseña.",
      );
    }
  }

  return (
    <main className="auth-shell relative">
      <ThemeToggle compact className="fixed right-5 top-5 z-20" />
      <section className="auth-stage">
        <aside
          className="auth-brand-panel"
          aria-label="Presentación de TalentSync"
        >
          <div>
            <BrandLogo
              size="lg"
              subtitle="Inteligencia laboral"
              tone="inverse"
            />
            <p className="mt-16 text-sm font-bold uppercase tracking-[0.16em] text-sky-300">
              Decisiones más claras
            </p>
            <h1 className="mt-4 max-w-md text-balance text-4xl font-bold text-white">
              El talento correcto merece un proceso más claro.
            </h1>
            <p className="mt-5 max-w-md text-base leading-7 text-sky-100">
              Una plataforma que convierte perfiles y vacantes en decisiones
              claras y fáciles de revisar.
            </p>
            <div className="mt-7 grid max-w-lg grid-cols-3 gap-3" aria-label="Actividad de la plataforma">
              {[
                { icon: BriefcaseBusiness, value: stats?.active_jobs, label: "Vacantes activas" },
                { icon: Building2, value: stats?.companies, label: "Empresas" },
                { icon: UsersRound, value: stats?.applications, label: "Procesos iniciados" },
              ].map(({ icon: Icon, value, label }) => (
                <div key={label} className="rounded-2xl border border-white/15 bg-white/[0.06] p-3 backdrop-blur-sm">
                  <Icon size={17} className="text-sky-300" aria-hidden="true" />
                  <strong className="mt-2 block text-xl text-white">{value == null ? "—" : value.toLocaleString("es-CO")}</strong>
                  <span className="mt-0.5 block text-[11px] leading-4 text-sky-100">{label}</span>
                </div>
              ))}
            </div>
          </div>
          <div className="grid gap-3">
            {signals.map(({ icon: Icon, title, detail }) => (
              <article key={title} className="auth-signal-card">
                <div className="flex gap-3">
                  <Icon
                    size={19}
                    className="mt-0.5 shrink-0 text-sky-300"
                    aria-hidden="true"
                  />
                  <div>
                    <h2 className="text-sm font-bold text-white">{title}</h2>
                    <p className="mt-1 text-sm leading-5 text-sky-100">
                      {detail}
                    </p>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </aside>
        <div className="auth-form-panel">
          <div className="auth-form">
            <p className="section-kicker">Acceso seguro</p>
            <h2 className="mt-3 text-3xl font-bold sm:text-4xl">
              Bienvenido de nuevo
            </h2>
            <p className="mt-3 text-base leading-6 text-[var(--muted)]">
              Inicia sesión para continuar con tu espacio de trabajo.
            </p>
            <form
              className="mt-8 space-y-5"
              onSubmit={handleSubmit(onSubmit)}
              noValidate
            >
              <label className="block text-sm font-semibold text-[var(--ink-strong)]">
                Correo electrónico
                <div className="field-control relative mt-2 flex items-center">
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
                    aria-invalid={errors.email ? "true" : undefined}
                    {...register("email", {
                      required: "El correo es obligatorio",
                    })}
                  />
                </div>
                {errors.email ? (
                  <span
                    role="alert"
                    className="mt-1 block text-sm font-medium text-[var(--error)]"
                  >
                    {errors.email.message}
                  </span>
                ) : null}
              </label>
              <label className="block text-sm font-semibold text-[var(--ink-strong)]">
                Contraseña
                <div className="field-control relative mt-2 flex items-center">
                  <LockKeyhole
                    size={18}
                    className="mr-3 shrink-0 text-[var(--accent)]"
                    aria-hidden="true"
                  />
                  <input
                    className="min-h-0 p-0"
                    type="password"
                    autoComplete="current-password"
                    placeholder="Ingresa tu contraseña"
                    aria-invalid={errors.password ? "true" : undefined}
                    {...register("password", {
                      required: "La contraseña es obligatoria",
                    })}
                  />
                </div>
                {errors.password ? (
                  <span
                    role="alert"
                    className="mt-1 block text-sm font-medium text-[var(--error)]"
                  >
                    {errors.password.message}
                  </span>
                ) : null}
              </label>
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
                  "Validando acceso…"
                ) : (
                  <>
                    Iniciar sesión <ArrowRight size={17} aria-hidden="true" />
                  </>
                )}
              </button>
            </form>
            <p className="mt-7 text-center text-sm text-[var(--muted)]">
              ¿Aún no tienes cuenta?{" "}
              <Link
                className="font-bold text-[var(--accent)] underline-offset-4 hover:underline focus-ring"
                to="/registro"
              >
                Crear cuenta
              </Link>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
