import { processDate } from "./interviewAgenda.js";

export function isProcessClosed(row) {
  return !!row.released_at || ["rejected", "accepted", "hired"].includes(row.status);
}

export function recruitmentStage(row, stages = []) {
  if (isProcessClosed(row)) return row.released_at ? "Proceso cerrado" : row.status === "rejected" ? "No seleccionado" : "Contratado";
  const stage = row.effective_stage || row.pipeline_stage || row.stage;
  return stages.find((item) => item.id === stage)?.title || row.pipeline_stage_title || row.stage_title || ({ submitted: "Recibida", seen: "Recibida", reviewing: "En revisión", shortlisted: "Preselección", technical_interview: "Entrevista", psychometric_test: "Evaluación" }[row.status]) || "En seguimiento";
}

export function interviewState(row, now = new Date()) {
  if (isProcessClosed(row) || !row.interview_at) return null;
  if (row.interview_completed_at && !["technical_interview", "psychometric_test"].includes(row.status)) return null;
  if (row.interview_completed_at) return "awaiting_response";
  return processDate(row.interview_at) > now ? "scheduled" : "unconfirmed";
}

export const interviewStateLabels = { scheduled: "Entrevista programada", unconfirmed: "Por registrar resultado de asistencia", awaiting_response: "Entrevista realizada · Pendiente de respuesta" };
