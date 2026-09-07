import { useEffect, useState } from "react";
import { Building2, CheckCircle2, Save } from "lucide-react";
import { useForm } from "react-hook-form";

import { api } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function CompanySettingsPage() {
  const { register, handleSubmit, reset } = useForm();
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/companies/me")
      .then(({ data }) => reset(data))
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
      const { data } = await api.put("/companies/me", values);
      reset(data);
      setMessage("Perfil de empresa actualizado correctamente");
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
          "No fue posible actualizar la empresa",
      );
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Empresa"
        title="Identidad de tu empresa"
        description="Actualiza la informacion que veran los candidatos cuando revisen tus vacantes."
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
        className="surface-card mx-auto max-w-3xl p-6 sm:p-8 hover-lift"
        onSubmit={handleSubmit(save)}
      >
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
          <label className="text-sm font-semibold text-[var(--muted)]/60">
            Nombre de la empresa
            <input
              className="field-control input-md mt-1.5"
              {...register("name", { required: true })}
            />
          </label>
          <label className="text-sm font-semibold text-[var(--muted)]/60">
            NIT
            <input
              className="field-control input-md mt-1.5"
              {...register("nit", { required: true })}
            />
          </label>
          <label className="text-sm font-semibold text-[var(--muted)]/60">
            Descripción
            <textarea
              className="field-control input-md mt-1.5 min-h-36"
              placeholder="Cuenta a los candidatos a que se dedica tu empresa..."
              {...register("description")}
            />
          </label>
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
      </form>
    </div>
  );
}
