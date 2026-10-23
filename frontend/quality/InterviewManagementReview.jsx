import { useState } from "react";
import { api } from "../src/api/client.js";
import { CompanyInterviewAgenda } from "../src/components/CompanyInterviewAgenda.jsx";
import { RecruiterProcessDialog } from "../src/components/RecruiterProcessDialog.jsx";
import { ProcessInterview } from "../src/components/InterviewAgenda.jsx";

export function InterviewManagementReview() {
  const [row, setRow] = useState({ id: 101, version: 1, job_title: "Analista de operaciones", candidate_name: "Candidata de ejemplo", recruiter_notes: "Nota privada", status: "technical_interview", interview_at: "2030-10-30T14:00:00", interview_details: { mode: "virtual", location: "https://meet.google.com/example", minutes: 60, instructions: "Prepara un ejemplo de tu trabajo." } });
  const [editing, setEditing] = useState(false);
  async function save(changes) {
    const { data } = await api.put(`/applications/${row.id}/status`, { ...changes, expected_version: row.version }, { __quiet: true });
    setRow((current) => ({ ...current, ...data })); setEditing(false);
  }
  return <><h1>Agenda de selección</h1><CompanyInterviewAgenda applications={[row]} onManage={() => setEditing(true)} /><ProcessInterview process={{ ...row, application_id: row.id }} />{editing && <RecruiterProcessDialog application={row} onSave={save} onClose={() => setEditing(false)} onDelete={async () => {}} />}</>;
}
