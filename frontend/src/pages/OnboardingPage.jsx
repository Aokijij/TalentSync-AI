import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, BriefcaseBusiness, FileUp, MapPin, RotateCcw, Search, Wallet } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { Autocomplete } from "../components/Autocomplete.jsx";
import { CurrencyInput } from "../components/CurrencyInput.jsx";
import { COLOMBIA_LOCATIONS } from "../constants/colombianCities.js";
import { OCCUPATIONS } from "../constants/occupations.js";
import { welcomeChanges, welcomePreferences } from "../utils/welcome.js";
import "../styles/welcome.css";

const cities = [...new Set(Object.values(COLOMBIA_LOCATIONS).flat())].sort((a, b) => a.localeCompare(b, "es"));
export function OnboardingPage() {
  const navigate = useNavigate(), { confirm } = useFeedback();
  const [profile, setProfile] = useState(null), [values, setValues] = useState(welcomePreferences());
  const [loadError, setLoadError] = useState(""), [error, setError] = useState(""), [busy, setBusy] = useState(false), [loading, setLoading] = useState(true), [revision, setRevision] = useState(0);
  const inFlight = useRef(false);
  useEffect(() => {
    let active = true;
    setLoading(true); setLoadError("");
    api.get("/profiles/me").then(({ data }) => { if (active) { setProfile(data); setValues(welcomePreferences(data)); } }).catch((failure) => { if (active) setLoadError(getApiErrorMessage(failure, "No pudimos cargar tu perfil. Reintenta para conservar tus datos guardados.")); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [revision]);
  const initial = welcomePreferences(profile || {});
  const dirty = Object.keys(values).some((key) => values[key] !== initial[key]);
  useEffect(() => {
    if (!dirty) return;
    const warn = (event) => { event.preventDefault(); event.returnValue = ""; };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  function change(key, value) { setValues((current) => ({ ...current, [key]: value })); setError(""); }
  async function leave(path) {
    if (busy) return;
    if (dirty && !await confirm({ title: "Continuar sin guardar preferencias", description: "Las preferencias que acabas de editar no se guardarán. Tu perfil y los datos guardados anteriormente se conservan.", confirmLabel: "Continuar sin guardar", cancelLabel: "Seguir editando", tone: "warning" })) return;
    navigate(path);
  }
  async function submit(event) {
    event.preventDefault(); if (inFlight.current || !profile) return;
    let changes;
    try { changes = welcomeChanges(initial, values); }
    catch (failure) { setError(failure.message); return; }
    if (!Object.keys(changes).length) { navigate("/recomendaciones"); return; }
    inFlight.current = true; setBusy(true); setError("");
    try {
      // The endpoint replaces the profile: merge only edited preferences into a fresh read.
      const { data } = await api.get("/profiles/me");
      await api.put("/profiles/me", { ...data, ...changes }, { __successMessage: "Preferencias guardadas. Ya puedes explorar tus oportunidades." });
      navigate("/recomendaciones");
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos guardar tus preferencias. Tus cambios siguen aquí.")); }
    finally { inFlight.current = false; setBusy(false); }
  }
  return <div className="space-y-6 candidate-welcome"><PageHeader kicker="A TU RITMO" title="Empieza por lo que buscas" description="Revisa tus preferencias o explora primero. Tu perfil puede crecer mientras avanzas." />
    {loadError && <div className="welcome-alert" role="alert"><p>{loadError}</p><button type="button" className="button-secondary" onClick={() => setRevision((current) => current + 1)}><RotateCcw size={16} />Reintentar</button></div>}
    <div className="welcome-layout"><form onSubmit={submit} className="welcome-panel" aria-busy={loading || busy}><header><span className="public-demo-icon"><Search size={21} /></span><div><h2>Dale dirección a tu búsqueda</h2><p>Todos estos datos son opcionales. Si ya los tienes, los conservamos.</p></div></header>
      {loading && <p role="status">Cargando tus preferencias guardadas…</p>}
      <fieldset className="welcome-fields" disabled={loading || busy || !profile}>
        <label>Cargo o área de interés<input className="field-control" aria-label="Cargo o área de interés" aria-describedby="welcome-profession-help" list="welcome-occupations" maxLength={160} placeholder="Indica el cargo o área que quieres explorar" value={values.profession} onChange={(event) => change("profession", event.target.value)} /><datalist id="welcome-occupations">{OCCUPATIONS.map((value) => <option key={value} value={value} />)}</datalist><small id="welcome-profession-help">Puedes usar tu profesión actual o el cargo al que quieres orientar tu búsqueda.</small></label>
        <div><Autocomplete label="Ciudad" options={cities} value={values.city} onChange={(value) => change("city", value)} maxLength={160} placeholder="Busca y elige tu ciudad" aria-describedby="welcome-city-help" /><small id="welcome-city-help">Elige una ciudad del catálogo; podrás ampliar tu búsqueda después.</small></div>
        <label>Modalidad<select aria-label="Modalidad" className="field-control" value={values.modality} onChange={(event) => change("modality", event.target.value)}><option value="">Sin preferencia definida</option><option value="remote">Remoto</option><option value="hybrid">Híbrido</option><option value="onsite">Presencial</option>{values.modality && !["remote", "hybrid", "onsite"].includes(values.modality) && <option value={values.modality}>Preferencia guardada: {values.modality}</option>}</select></label>
        <label>Aspiración mensual en COP<CurrencyInput aria-label="Aspiración mensual en COP" value={values.salary} onChange={(value) => change("salary", value)} maxLength={18} placeholder="Indica el importe mensual que buscas" aria-describedby="welcome-salary-help" /><small id="welcome-salary-help">Déjala vacía si prefieres definirla más adelante.</small></label>
      </fieldset>
      {error && <p className="welcome-error" role="alert">{error}</p>}
      <div className="welcome-actions"><button type="submit" className="button-primary" disabled={loading || busy || !profile}>{busy ? "Guardando preferencias…" : dirty ? "Guardar y ver oportunidades" : "Ver oportunidades"}<ArrowRight size={17} /></button><button type="button" className="button-secondary" disabled={busy} onClick={() => leave("/vacantes")}>Completar después</button></div>
    </form><aside className="welcome-aside"><section className="welcome-panel"><FileUp size={26} className="text-[var(--accent)]" /><h2>{profile?.cv_filename ? "Tu hoja de vida ya está guardada" : "¿Ya tienes una hoja de vida?"}</h2><p>{profile?.cv_filename ? "Puedes revisar su información y actualizarla desde tu perfil." : "Sube tu PDF desde el perfil y revisa la información extraída antes de guardarla. También puedes completarlo manualmente."}</p><button type="button" className="button-secondary mt-4" disabled={busy} onClick={() => leave("/perfil#profile-cv")}>{profile?.cv_filename ? "Revisar mi hoja de vida" : "Ir a subir mi CV"}<ArrowRight size={16} /></button><small>Acceder con Google o GitHub no analiza tus repositorios ni completa automáticamente tu trayectoria.</small></section><section className="welcome-panel"><h2>Información útil, paso a paso</h2><ul className="welcome-summary">{[[BriefcaseBusiness, "Tu dirección", values.profession || "Puedes empezar sin elegir un cargo"], [MapPin, "Tu ubicación", values.city || "La defines cuando quieras"], [Wallet, "Tus expectativas", values.salary ? `${Number(values.salary).toLocaleString("es-CO")} COP al mes` : "El salario sigue siendo opcional"]].map(([Icon, title, detail]) => <li key={title}><Icon size={19} /><div><strong>{title}</strong><span>{detail}</span></div></li>)}</ul><p className="mt-4">Las recomendaciones usan la información disponible. Completar un dato aporta contexto; no garantiza un porcentaje mayor ni una contratación.</p></section></aside></div>
  </div>;
}
