import { ArrowLeft, KeyRound, ShieldCheck, Smartphone } from "lucide-react";
import { useState } from "react";

export function MfaChallenge({ email, busy, error, onVerify, onBack }) {
  const [recovery, setRecovery] = useState(false), [code, setCode] = useState("");
  return <section className="mfa-challenge">
    <span className="mfa-symbol"><ShieldCheck size={34} /></span>
    <p className="section-kicker">Paso 2 de 2 · Verificación</p>
    <h2 className="text-3xl font-bold">Confirma que eres tú</h2>
    <p className="text-sm text-[var(--muted)]">La contraseña se validó para <strong>{email}</strong>. {recovery ? "Introduce uno de tus códigos de recuperación sin usar." : "Abre tu aplicación autenticadora e introduce su código de seis dígitos."}</p>
    <div className="flex flex-wrap gap-2" aria-label="Método de verificación"><button type="button" className={recovery ? "button-secondary" : "button-primary"} onClick={() => { setRecovery(false); setCode(""); }} disabled={busy}><Smartphone size={17} />Aplicación</button><button type="button" className={recovery ? "button-primary" : "button-secondary"} onClick={() => { setRecovery(true); setCode(""); }} disabled={busy}><KeyRound size={17} />Recuperación</button></div>
    <form className="space-y-4" onSubmit={(event) => { event.preventDefault(); onVerify(code.trim()); }}>
      <label className="block font-semibold" htmlFor="mfa-code">{recovery ? "Código de recuperación" : "Código de seis dígitos"}</label>
      <input id="mfa-code" className={`field-control ${recovery ? "" : "mfa-code"}`} autoFocus autoComplete="one-time-code" inputMode={recovery ? "text" : "numeric"} pattern={recovery ? undefined : "[0-9]{6}"} maxLength={recovery ? 128 : 6} required value={code} onChange={(event) => setCode(recovery ? event.target.value : event.target.value.replace(/\D/g, ""))} placeholder={recovery ? "Tu código de recuperación" : "000000"} disabled={busy} />
      {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
      <button className="button-primary w-full" disabled={busy || !code || !recovery && code.length !== 6}>{busy ? "Verificando…" : "Verificar y entrar"}</button>
    </form>
    <button type="button" className="flex items-center gap-2 text-sm text-[var(--accent)]" onClick={onBack} disabled={busy}><ArrowLeft size={16} />Usar otra cuenta</button>
  </section>;
}
