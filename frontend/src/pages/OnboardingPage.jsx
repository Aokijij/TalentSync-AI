import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { BriefcaseBusiness, MapPin, Sparkles, Wallet } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { Autocomplete } from "../components/Autocomplete.jsx";
import { CurrencyInput } from "../components/CurrencyInput.jsx";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
import { OCCUPATIONS } from "../constants/occupations.js";
const cities = [...new Set(Object.values(COLOMBIA_LOCATIONS).flat())].sort((a, b) => a.localeCompare(b, "es"));
export function OnboardingPage() {
 const navigate = useNavigate();
 const [error, setError] = useState(""), [busy, setBusy] = useState(false);
 const [profession, setProfession] = useState(""), [city, setCity] = useState(""), [salary, setSalary] = useState("");
 async function submit(event) {
  event.preventDefault(); setBusy(true); setError(""); const data = new FormData(event.currentTarget);
  try { const existing = await api.get("/profiles/me"); await api.put("/profiles/me", { ...existing.data, profession: profession.trim(), location: city.trim(), preferred_modality: data.get("modality"), desired_salary: salary ? Number(salary) : null }); navigate("/recomendaciones"); }
  catch (failure) { setError(getApiErrorMessage(failure)); } finally { setBusy(false); }
 }
 return <div className="space-y-5"><PageHeader kicker="Tu siguiente paso" title="Tu próxima oportunidad empieza contigo" description="Cuatro preferencias para orientar tu búsqueda. Puedes cambiarlas cuando quieras." />
 <div className="grid items-start gap-5 lg:grid-cols-[1.5fr_1fr]">
 <form onSubmit={submit} className="surface-card space-y-6 p-6 sm:p-8"><div className="flex items-center gap-3"><span className="learning-area-icon"><BriefcaseBusiness /></span><div><h2 className="text-xl font-bold">Dale dirección a tu búsqueda</h2><p className="text-sm text-[var(--muted)]">Elige una sugerencia o escribe tu propio cargo.</p></div></div>
 <Autocomplete label="Cargo o área de interés" options={OCCUPATIONS} value={profession} onChange={setProfession} name="profession" required maxLength={160} placeholder="Empieza a escribir: analista, auxiliar…" />
 <div className="grid gap-5 sm:grid-cols-2"><Autocomplete label="Ciudad" options={cities} value={city} onChange={setCity} maxLength={160} placeholder="Busca tu ciudad" /><label className="block text-sm font-semibold">Modalidad<select name="modality" className="field-control mt-2"><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option></select></label></div>
 <label className="block text-sm font-semibold">Aspiración mensual en COP <span className="font-normal text-[var(--muted)]">· opcional</span><div className="mt-2"><CurrencyInput aria-label="Aspiración mensual en COP" value={salary} onChange={setSalary} maxLength={18} placeholder="2.500.000" /></div></label>
 {error && <p role="alert" className="text-[var(--error)]">{error}</p>}<div className="flex flex-wrap gap-3"><button disabled={busy} className="button-primary">{busy ? "Guardando…" : "Ver mis oportunidades →"}</button><Link className="button-secondary" to="/candidato">Completar después</Link></div></form>
 <aside className="surface-card space-y-5 p-6"><Sparkles className="text-[var(--accent)]" size={30} /><h2 className="text-xl font-bold">Así te ayuda tu perfil</h2>{[[BriefcaseBusiness, "Un cargo que te represente", profession || "Explora opciones de diferentes sectores"], [MapPin, "Un lugar para crecer", city || "Combina ciudad y modalidad"], [Wallet, "Expectativas claras", salary ? `$ ${Number(salary).toLocaleString("es-CO")} al mes` : "El salario es opcional"]].map(([Icon, title, detail]) => <div className="flex gap-3 rounded-xl bg-[var(--surface-subtle)] p-4" key={title}><Icon size={20} className="shrink-0 text-[var(--accent)]" /><div><h3 className="text-sm font-bold">{title}</h3><p className="mt-1 text-sm text-[var(--muted)]">{detail}</p></div></div>)}<p className="text-sm text-[var(--muted)]">Después podrás subir tu hoja de vida y añadir experiencia y muestras de trabajo.</p></aside>
 </div></div>;
}
