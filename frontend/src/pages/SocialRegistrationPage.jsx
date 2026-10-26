import { useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { ArrowRight, CheckCircle2, LogOut, UserRound } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { useAuth } from "../hooks/useAuth.js";
import { OCCUPATIONS } from "../constants/occupations.js";
import "../styles/search-settings.css";

export function SocialRegistrationPage() {
  const { user, refreshUser, logout } = useAuth(), navigate = useNavigate();
  const [name, setName] = useState(user.name || ""), [profession, setProfession] = useState("");
  const [confirmed, setConfirmed] = useState(false), [busy, setBusy] = useState(false), [error, setError] = useState("");
  const flight = useRef(false), completed = useRef(false);
  if (!user.registration_pending) return <Navigate to={completed.current ? "/bienvenida" : "/"} replace />;
  async function submit(event) {
    event.preventDefault(); if (flight.current) return;
    flight.current = true; setBusy(true); setError("");
    try {
      if (!completed.current) {
        await api.post("/auth/social/registration", { name: name.trim(), profession: profession.trim(), confirmed }, { __successMessage: "Tu cuenta está lista. Continúa con tu búsqueda." });
        completed.current = true;
      }
      await refreshUser(); navigate("/bienvenida", { replace: true });
    } catch (failure) { setError(getApiErrorMessage(failure, "No pudimos completar el registro. Revisa tus datos e inténtalo de nuevo.")); }
    finally { flight.current = false; setBusy(false); }
  }
  return <main className="social-registration"><section className="social-registration-card">
    <header><span className="social-registration-icon"><UserRound size={26} /></span><p className="section-kicker">TU CUENTA PROFESIONAL</p><h1>Presentémonos bien</h1><p>Confirma cómo te identificarás en TalentSync antes de empezar.</p></header>
    <div className="social-verified-email"><CheckCircle2 size={20} /><span><strong>Correo verificado por tu proveedor</strong><span>{user.email}</span></span></div>
    <form onSubmit={submit}><fieldset disabled={busy}>
      <label>Tu nombre<input aria-label="Tu nombre" className="field-control" required minLength={2} maxLength={120} autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Escribe tu nombre y apellidos" aria-describedby="social-name-help" /><small id="social-name-help">Usa el nombre con el que quieres presentarte profesionalmente; revisa si tu proveedor envió un alias.</small></label>
      <label>Profesión o cargo de interés<input aria-label="Profesión o cargo de interés" aria-describedby="social-profession-help" className="field-control" required minLength={2} maxLength={160} list="social-occupations" value={profession} onChange={(event) => setProfession(event.target.value)} placeholder="Indica a qué te dedicas o qué cargo buscas" /><datalist id="social-occupations">{OCCUPATIONS.map((value) => <option key={value} value={value} />)}</datalist><small id="social-profession-help">Podrás completar tu experiencia y tus habilidades desde Mi perfil.</small></label>
      <label className="social-confirm-identity"><input type="checkbox" required checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} /><span>Confirmo que este nombre y esta profesión corresponden a mi perfil.</span></label>
    </fieldset>{error && <p role="alert" className="welcome-error">{error}</p>}
    <footer><button type="submit" disabled={busy} className="button-primary">{busy ? "Preparando tu cuenta…" : "Confirmar y continuar"}<ArrowRight size={17} /></button><button type="button" className="button-secondary" disabled={busy} onClick={async () => { try { await logout(); navigate("/login", { replace: true }); } catch (failure) { setError(getApiErrorMessage(failure)); } }}><LogOut size={16} />Salir</button></footer></form>
  </section></main>;
}
