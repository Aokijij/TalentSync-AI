import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, BriefcaseBusiness, FileUp, MapPin, RotateCcw, Search, Wallet } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useFeedback } from "../contexts/FeedbackContext.jsx";
import { PageHeader } from "../components/PageHeader.jsx";
import { WorkPreferenceFields } from "../components/WorkPreferenceFields.jsx";
import { welcomeChanges, welcomePreferences } from "../utils/welcome.js";
import "../styles/welcome.css";

export function OnboardingPage({ adjusting = false }) {
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
    if (!Object.keys(changes).length) { navigate("/recomendaciones", { replace: !adjusting }); return; }
    inFlight.current = true; setBusy(true); setError("");
    try {
      // The endpoint replaces the profile: merge only edited preferences into a fresh read.
      const { data } = await api.get("/profiles/me");
      await api.put("/profiles/me", { ...data, ...changes }, { __successMessage: "Preferencias guardadas. Ya puedes explorar tus oportunidades." });
      navigate("/recomendaciones", { replace: !adjusting });
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos guardar tus preferencias. Tus cambios siguen aquí.")); }
    finally { inFlight.current = false; setBusy(false); }
  }
  return <div className={`space-y-6 candidate-welcome${adjusting ? " search-settings" : ""}`}><PageHeader kicker={adjusting ? "TUS PREFERENCIAS" : "A TU RITMO"} title={adjusting ? "Ajusta tu búsqueda" : "Empieza por lo que buscas"} description={adjusting ? "Actualiza tus preferencias laborales en un solo lugar. Son las mismas que verás en Mi perfil." : "Revisa tus preferencias o explora primero. Tu perfil puede crecer mientras avanzas."} />
    {!adjusting && <section className="welcome-guide-link"><div><h2>Conoce lo que puedes hacer en TalentSync</h2><p>Consulta la guía cuando necesites ayuda con una función o un resultado.</p></div><button type="button" className="button-secondary" onClick={() => leave("/guia")}>Abrir guía completa<ArrowRight size={16} /></button></section>}
    {loadError && <div className="welcome-alert" role="alert"><p>{loadError}</p><button type="button" className="button-secondary" onClick={() => setRevision((current) => current + 1)}><RotateCcw size={16} />Reintentar</button></div>}
    <div className="welcome-layout"><form onSubmit={submit} className="welcome-panel" aria-busy={loading || busy}><header><span className="public-demo-icon"><Search size={21} /></span><div><h2>{adjusting ? "Preferencias laborales" : "Dale dirección a tu búsqueda"}</h2><p>Todos estos datos son opcionales. Si ya los tienes, los conservamos.</p></div></header>
      {loading && <p role="status">Cargando tus preferencias guardadas…</p>}
      <fieldset className="welcome-fields" disabled={loading || busy || !profile}>
        <WorkPreferenceFields includeCareer value={{ profession: values.profession, location: values.city, preferred_modality: values.modality, desired_salary: values.salary, preferred_sector: values.sector, availability: values.availability }} onChange={(key, value) => change(({ location: "city", preferred_modality: "modality", desired_salary: "salary", preferred_sector: "sector" })[key] || key, value)} />
      </fieldset>
      {error && <p className="welcome-error" role="alert">{error}</p>}
      <div className="welcome-actions"><button type="submit" className="button-primary" disabled={loading || busy || !profile}>{busy ? "Guardando preferencias…" : dirty ? adjusting ? "Guardar preferencias" : "Guardar y ver oportunidades" : "Ver oportunidades"}<ArrowRight size={17} /></button><button type="button" className="button-secondary" disabled={busy} onClick={() => leave(adjusting ? "/candidato" : "/vacantes")}>{adjusting ? "Cancelar" : "Completar después"}</button></div>
    </form><aside className="welcome-aside">{adjusting ? <section className="welcome-panel"><Search size={25} className="text-[var(--accent)]" /><h2>Tu búsqueda, con contexto</h2><p>Estos datos actualizan tu perfil y se utilizan al recomendar oportunidades. Cambiarlos no modifica tus postulaciones.</p><p>En Recomendaciones puedes elegir qué condiciones son imprescindibles.</p><button type="button" className="button-secondary mt-4" disabled={busy} onClick={() => leave("/perfil#preferencias")}>Ver preferencias en mi perfil<ArrowRight size={16} /></button></section> : <section className="welcome-panel"><FileUp size={26} className="text-[var(--accent)]" /><h2>{profile?.cv_filename ? "Tu hoja de vida ya está guardada" : "¿Ya tienes una hoja de vida?"}</h2><p>{profile?.cv_filename ? "Puedes revisar su información y actualizarla desde tu perfil." : "Sube tu PDF desde el perfil y revisa la información extraída antes de guardarla. También puedes completarlo manualmente."}</p><button type="button" className="button-secondary mt-4" disabled={busy} onClick={() => leave("/perfil#profile-cv")}>{profile?.cv_filename ? "Revisar mi hoja de vida" : "Ir a subir mi CV"}<ArrowRight size={16} /></button><small>Acceder con Google o GitHub no analiza tus repositorios ni completa automáticamente tu trayectoria.</small></section>}<section className="welcome-panel"><h2>Información útil, paso a paso</h2><ul className="welcome-summary">{[[BriefcaseBusiness, "Tu dirección", values.profession || "Puedes empezar sin elegir un cargo"], [MapPin, "Tu ubicación", values.city || "La defines cuando quieras"], [Wallet, "Tus expectativas", values.salary ? `${Number(values.salary).toLocaleString("es-CO")} COP al mes` : "El salario sigue siendo opcional"]].map(([Icon, title, detail]) => <li key={title}><Icon size={19} /><div><strong>{title}</strong><span>{detail}</span></div></li>)}</ul><p className="mt-4">Las recomendaciones usan la información disponible. Completar un dato aporta contexto; no garantiza un porcentaje mayor ni una contratación.</p></section></aside></div>
  </div>;
}
