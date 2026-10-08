import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

export function OnboardingPage() {
  const navigate = useNavigate();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event) {
    event.preventDefault(); setBusy(true);
    const data = new FormData(event.currentTarget);
    try {
      const existing = await api.get("/profiles/me");
      await api.put("/profiles/me", { ...existing.data, profession: data.get("profession"), location: data.get("location"), preferred_modality: data.get("modality"), desired_salary: data.get("salary") ? Number(data.get("salary")) : null });
      navigate("/recomendaciones");
    } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  return <div className="space-y-5"><PageHeader kicker="Tu siguiente paso" title="Cuéntanos qué estás buscando" description="Empieza por tus preferencias. Después podrás añadir experiencia, CV y evidencias para mejorar tus recomendaciones." />
    <form onSubmit={submit} className="surface-card max-w-2xl space-y-4 p-6">
      <label className="block text-sm font-semibold">Cargo o área de interés<input name="profession" required className="field-control mt-2" placeholder="Ej. analista de datos o atención al cliente" /></label>
      <label className="block text-sm font-semibold">Ciudad<input name="location" className="field-control mt-2" placeholder="Ej. Bogotá" /></label>
      <label className="block text-sm font-semibold">Modalidad<select name="modality" className="field-control mt-2"><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option></select></label>
      <label className="block text-sm font-semibold">Aspiración mensual en COP (opcional)<input name="salary" type="number" min="0" className="field-control mt-2" /></label>
      {error && <p role="alert">{error}</p>}
      <div className="flex flex-wrap gap-3"><button disabled={busy} className="button-primary">Guardar y ver oportunidades</button><Link className="button-secondary" to="/candidato">Completar después</Link></div>
    </form>
  </div>;
}
