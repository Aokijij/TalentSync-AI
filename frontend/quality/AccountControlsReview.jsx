import { useState } from "react";
import { AccountDataPanel } from "../src/components/AccountDataPanel.jsx";
import { GoogleCalendarPanel } from "../src/components/GoogleCalendarPanel.jsx";
import { CalendarSync } from "../src/components/CalendarSync.jsx";
import { OperationsPanel } from "../src/components/OperationsPanel.jsx";

export function AccountControlsReview() {
  const [panel, setPanel] = useState("data"), [deleted, setDeleted] = useState(false);
  return <><h1>Controles de cuenta y operación</h1><nav className="workspace-tabs" aria-label="Revisión de controles">{[["data", "Datos"], ["calendar", "Calendario"], ["operations", "Operaciones"]].map(([id, label]) => <button key={id} aria-pressed={panel === id} onClick={() => setPanel(id)}>{label}</button>)}</nav>
    {deleted && <p role="status">Cuenta de ejemplo eliminada</p>}
    {panel === "data" && <AccountDataPanel user={{ role: "candidate", mfa_enabled: false }} onDeleted={async () => setDeleted(true)} />}
    {panel === "calendar" && <><GoogleCalendarPanel /><section className="surface-card p-5"><h2>Entrevista de ejemplo</h2><CalendarSync applicationId={101} /></section></>}
    {panel === "operations" && <OperationsPanel />}</>;
}
