import { useState } from "react";
import { AccountDataPanel } from "../src/components/AccountDataPanel.jsx";
import { GoogleCalendarPanel } from "../src/components/GoogleCalendarPanel.jsx";
import { ProcessInterview } from "../src/components/InterviewAgenda.jsx";
import { OperationsPanel } from "../src/components/OperationsPanel.jsx";

export function AccountControlsReview() {
  const [panel, setPanel] = useState("data"), [deleted, setDeleted] = useState(false);
  return <><h1>Controles de cuenta y operación</h1><nav className="workspace-tabs" aria-label="Revisión de controles">{[["data", "Datos"], ["calendar", "Calendario"], ["operations", "Operaciones"]].map(([id, label]) => <button key={id} aria-pressed={panel === id} onClick={() => setPanel(id)}>{label}</button>)}</nav>
    {deleted && <p role="status">Cuenta de ejemplo eliminada</p>}
    {panel === "data" && <AccountDataPanel user={{ role: "candidate", mfa_enabled: false }} onDeleted={async () => setDeleted(true)} />}
    {panel === "calendar" && <><GoogleCalendarPanel /><ProcessInterview process={{ application_id: 101, status: "technical_interview", interview_at: "2026-10-26T14:00:00" }} now={new Date("2026-10-23T12:00:00Z")} /></>}
    {panel === "operations" && <OperationsPanel />}</>;
}
