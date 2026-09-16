import { useEffect, useState } from "react";
import { Building2, CheckCircle2, ImagePlus, Save, Upload } from "lucide-react";
import { useForm } from "react-hook-form";

import { api, apiFileUrl } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function CompanySettingsPage() {
  const { register, handleSubmit, reset } = useForm();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [company, setCompany] = useState(null);
  const [imageVersion, setImageVersion] = useState(0);

  useEffect(() => {
    api
      .get("/companies/me")
      .then(({ data }) => {
        setCompany(data);
        reset({
          ...data,
          values: (data.values || []).join(", "),
          benefits: (data.benefits || []).join(", "),
        });
      })
      .catch((requestError) =>
        setError(
          requestError.response?.data?.detail ||
            "No fue posible cargar la empresa",
        ),
      );
  }, [reset]);

  async function save(values) {
    setMessage("");
    setError("");
    try {
      const payload = {
        ...values,
        values: splitList(values.values),
        benefits: splitList(values.benefits),
      };
      const { data } = await api.put("/companies/me", payload);
      setCompany(data);
      reset({
        ...data,
        values: (data.values || []).join(", "),
        benefits: (data.benefits || []).join(", "),
      });
      setMessage("Perfil de empresa actualizado correctamente");
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "No fue posible actualizar la empresa",
      );
    }
  }

  async function uploadBrandImage(kind, event) {
    const file = event.target.files?.[0];
    if (!file) return;
    const form = new FormData();
    form.append("file", file);
    setMessage("");
    setError("");
    try {
      const { data } = await api.post(`/companies/me/${kind}`, form);
      setCompany(data);
      setImageVersion((current) => current + 1);
      setMessage(
        kind === "logo"
          ? "Logo actualizado correctamente."
          : "Imagen de portada actualizada correctamente.",
      );
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail || "No fue posible guardar la imagen",
      );
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Empresa"
        title="Identidad de tu empresa"
        description="Actualiza la información que verán los candidatos cuando revisen tus vacantes."
      />

      {(message || error) && (
        <p
          className={
            error
              ? "rounded-[var(--radius-lg)] border px-4 py-3 text-sm border-[var(--error)] bg-[var(--error)]/10 text-[var(--error)]"
              : "rounded-[var(--radius-lg)] border px-4 py-3 text-sm border-[var(--success)] bg-[var(--success)]/10 text-[var(--success)]"
          }
        >
          {error || message}
        </p>
      )}

      <form
        className="surface-card mx-auto max-w-5xl overflow-hidden !p-0 hover-lift"
        onSubmit={handleSubmit(save)}
      >
        <div
          className="relative min-h-52 overflow-hidden bg-gradient-to-br from-sky-950 via-sky-800 to-cyan-600"
          style={
            company?.cover_url
              ? {
                  backgroundImage: `linear-gradient(90deg, rgba(2, 15, 35, .82), rgba(2, 15, 35, .3)), url(${apiFileUrl(company.cover_url)}?v=${imageVersion})`,
                  backgroundPosition: "center",
                  backgroundSize: "cover",
                }
              : undefined
          }
        >
          <div className="absolute inset-x-0 bottom-0 flex flex-col gap-4 p-6 sm:flex-row sm:items-end sm:justify-between sm:p-8">
            <div className="flex items-end gap-4">
              <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-2xl border-4 border-white bg-white text-3xl font-black text-sky-900 shadow-xl">
                {company?.logo_url ? (
                  <img
                    src={`${apiFileUrl(company.logo_url)}?v=${imageVersion}`}
                    alt="Logo de la empresa"
                    className="h-full w-full object-contain p-2"
                  />
                ) : (
                  (company?.name || "E").slice(0, 1).toUpperCase()
                )}
              </div>
              <div className="pb-1 text-white">
                <p className="text-2xl font-bold">{company?.name || "Tu empresa"}</p>
                <p className="mt-1 text-sm text-sky-100">Vista previa del perfil público</p>
              </div>
            </div>
            <div className="flex flex-wrap gap-2">
              <label className="button-secondary button-sm cursor-pointer !border-white/30 !bg-white/10 !text-white hover:!bg-white/20">
                <ImagePlus size={15} /> Cambiar logo
                <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => uploadBrandImage("logo", event)} />
              </label>
              <label className="button-secondary button-sm cursor-pointer !border-white/30 !bg-white/10 !text-white hover:!bg-white/20">
                <Upload size={15} /> Cambiar portada
                <input className="hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => uploadBrandImage("cover", event)} />
              </label>
            </div>
          </div>
        </div>
        <div className="p-6 sm:p-8">
        <div className="flex items-start gap-4 border-b border-[var(--line)] pb-5">
          <div className="grid h-11 w-11 place-items-center rounded-[var(--radius-xl)] bg-[var(--accent)]/10 text-[var(--accent)]">
            <Building2 size={22} />
          </div>
          <div>
            <h2 className="font-bold text-[var(--ink)]">Perfil público</h2>
            <p className="mt-1 text-sm text-[var(--muted)]">
              Los datos empresariales se muestran junto a las oportunidades
              publicadas.
            </p>
          </div>
        </div>
        <div className="mt-6 grid gap-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Nombre de la empresa">
              <input className="field-control mt-1.5" {...register("name", { required: true })} />
            </Field>
            <Field label="NIT">
              <input className="field-control mt-1.5" {...register("nit", { required: true })} />
            </Field>
            <Field label="Sector">
              <input className="field-control mt-1.5" placeholder="Ej. Servicios financieros" {...register("sector")} />
            </Field>
            <Field label="Tamaño de la empresa">
              <select className="field-control mt-1.5" {...register("size")}>
                <option value="">Seleccionar</option>
                <option value="1-10 personas">1-10 personas</option>
                <option value="11-50 personas">11-50 personas</option>
                <option value="51-200 personas">51-200 personas</option>
                <option value="201-1000 personas">201-1000 personas</option>
                <option value="Más de 1000 personas">Más de 1000 personas</option>
              </select>
            </Field>
            <Field label="Ubicación principal">
              <input className="field-control mt-1.5" placeholder="Ciudad, departamento" {...register("location")} />
            </Field>
            <Field label="Sitio web">
              <input className="field-control mt-1.5" type="url" placeholder="https://empresa.com" {...register("website")} />
            </Field>
          </div>
          <label className="text-sm font-semibold text-[var(--muted)]/60">
            Descripción
            <textarea
              className="field-control input-md mt-1.5 min-h-36"
              placeholder="Cuenta a los candidatos a que se dedica tu empresa..."
              {...register("description")}
            />
          </label>
          <Field label="Propósito de la empresa">
            <textarea className="field-control mt-1.5 min-h-28" placeholder="Qué busca lograr la empresa y cómo aporta a sus clientes o comunidad" {...register("mission")} />
          </Field>
          <div className="grid gap-5 sm:grid-cols-2">
            <Field label="Valores y cultura">
              <textarea className="field-control mt-1.5 min-h-28" placeholder="Colaboración, transparencia, aprendizaje" {...register("values")} />
              <span className="mt-1 block text-xs text-[var(--muted)]">Separa cada elemento con una coma.</span>
            </Field>
            <Field label="Beneficios para el equipo">
              <textarea className="field-control mt-1.5 min-h-28" placeholder="Trabajo híbrido, formación, horario flexible" {...register("benefits")} />
              <span className="mt-1 block text-xs text-[var(--muted)]">Separa cada beneficio con una coma.</span>
            </Field>
          </div>
        </div>
        <div className="mt-7 flex flex-wrap items-center justify-between gap-3 border-t border-[var(--line)] pt-5">
          <p className="flex items-center gap-2 text-sm text-[var(--muted)]">
            <CheckCircle2 size={16} className="text-[var(--success)]" /> Cambios
            visibles en nuevas consultas.
          </p>
          <button
            className="button-primary w-auto hover-lift pressed focus-ring"
            type="submit"
          >
            <Save size={16} />
            Guardar cambios
          </button>
        </div>
        </div>
      </form>
    </div>
  );
}

function splitList(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function Field({ label, children }) {
  return (
    <label className="text-sm font-semibold text-[var(--muted)]/60">
      {label}
      {children}
    </label>
  );
}
