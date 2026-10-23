import { useState } from "react";
import { ProcessWorkspace } from "../src/components/ProcessWorkspace.jsx";

export function ResponseDeadlineReview({ role, state = "paused" }) {
  const [process, setProcess] = useState({ application_id: 101, job_id: 101, company_name: "Empresa de ejemplo", candidate_name: "Persona de ejemplo", status: "reviewing", stage: "reviewing", stage_title: "En revisión", response_days: 5, version: 3,
    response_due_at: "2020-10-20T15:00:00", response_overdue_at: "2020-10-21T15:00:00", response_paused_at: state === "paused" ? "2020-10-26T15:00:00" : null, response_state: state, deadline_extension_count: 0, can_manage: role === "company", created_at: "2020-10-10T15:00:00", response_owner: "Equipo de selección de Empresa de ejemplo",
    deadline_policy: { extension_limit: 1 }, job_conditions: { pipeline_stages: [{ id: "submitted", title: "Recibidas" }, { id: "reviewing", title: "En revisión" }, { id: "interview", title: "Entrevistas" }, { id: "hired", title: "Contratados" }, { id: "rejected", title: "No seleccionados" }] },
    events: [{ id: 1, type: "application.response_paused", at: "2020-10-26T15:00:00", source: "system" }] });
  return <><h1>Seguimiento de selección · Datos de prueba</h1><ProcessWorkspace process={process} role={role} onProcessUpdated={setProcess} communication={role === "company" ? <p>Comunica el siguiente avance de la selección.</p> : undefined} evaluation={role === "company" ? <p>La evaluación interna se conserva.</p> : undefined} /></>;
}
