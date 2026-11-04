import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, CheckCircle2, LogOut, UserRound } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { ProfessionPicker } from "../components/ProfessionPicker.jsx";
import { RegistrationConsent, registrationLegalPayload } from "../components/RegistrationConsent.jsx";
import { ConsentChoice } from "../components/ConsentChoice.jsx";
import "../styles/search-settings.css";

export function SocialRegistrationPage() {
  const { user, refreshUser, logout } = useAuth(), navigate = useNavigate();
  const company = user.role === "company", destination = company ? "/empresa/bienvenida" : "/bienvenida";
  const [name, setName] = useState(user.name || ""), [profession, setProfession] = useState("");
  const [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const flight = useRef(false), completed = useRef(false);
  const [legal, setLegal] = useState({ data_processing_accepted: false, terms_accepted: false });
  const [legalError, setLegalError] = useState("");
  if (!user.registration_pending) return <Navigate to={completed.current ? destination : "/"} replace />;
  async function submit(event) {
    event.preventDefault(); if (flight.current) return;
    if (!legal.data_processing_accepted || !legal.terms_accepted) { setLegalError("Autoriza el tratamiento de datos y acepta los términos para completar tu registro."); return; }
    flight.current = true; setBusy(true); setError("");
    try {
      if (!completed.current) {
        await api.post(company ? "/auth/company/registration/complete" : "/auth/social/registration", { name: name.trim(), ...(!company ? { profession: profession.trim() } : {}), confirmed, ...registrationLegalPayload(legal) }, { __successMessage: company ? "Tu cuenta empresarial está lista." : "Tu cuenta está lista. Continúa con tu búsqueda." });
        completed.current = true;
      }
      await refreshUser(); navigate(destination, { replace: true });
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos completar el registro. Revisa tus datos e inténtalo de nuevo.")); }
    finally { flight.current = false; setBusy(false); }
  }
  return <main className="social-registration"><section className="social-registration-card">
    <header><span className="social-registration-icon"><UserRound size={26} /></span><p className="section-kicker">{company ? "TU CUENTA EMPRESARIAL" : "TU CUENTA PROFESIONAL"}</p><h1>{company ? "Prepara tu acceso empresarial" : "Presentémonos bien"}</h1><p>{company ? "Revisa cómo se mostrará tu cuenta y confirma tus autorizaciones para administrar la empresa." : "Confirma cómo te identificarás en TalentSync antes de empezar."}</p></header>
    <div className="social-verified-email"><CheckCircle2 size={20} /><span><strong>{company ? "Correo de acceso confirmado" : "Correo verificado por tu proveedor"}</strong><span>{user.email}</span></span></div>
    <form onSubmit={submit}><fieldset disabled={busy}>
      <label>{company ? "Nombre mostrado en el equipo" : "Tu nombre"}<input aria-label={company ? "Nombre mostrado en el equipo" : "Tu nombre"} className="field-control" required minLength={2} maxLength={120} autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder={company ? "Nombre con el que administrarás el equipo" : "Escribe tu nombre y apellidos"} aria-describedby="social-name-help" /><small id="social-name-help">{company ? "Este nombre identifica tu cuenta dentro del equipo. La empresa conserva su propia ficha y verificación." : "Usa el nombre con el que quieres presentarte profesionalmente; revisa si tu proveedor envió un alias."}</small></label>
      {!company && <ProfessionPicker value={profession} onChange={setProfession} required />}
      <ConsentChoice title={company ? "Confirmo que administraré esta cuenta empresarial." : "Confirmo que este nombre y esta profesión corresponden a mi perfil."} required checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />
    </fieldset><RegistrationConsent values={legal} onChange={(key, value) => { setLegal((current) => ({ ...current, [key]: value })); setLegalError(""); }} error={legalError} disabled={busy} />{error && <p role="alert" className="welcome-error">{error}</p>}
    <footer><button type="submit" disabled={busy} className="button-primary">{busy ? "Preparando tu cuenta…" : "Confirmar y continuar"}<ArrowRight size={17} /></button><button type="button" className="button-secondary" disabled={busy} onClick={async () => { try { await logout(); navigate(company ? "/empresa/login" : "/login", { replace: true }); } catch (failure) { setError(getApiErrorMessage(failure)); } }}><LogOut size={16} />Salir</button></footer></form>
  </section></main>;
}
