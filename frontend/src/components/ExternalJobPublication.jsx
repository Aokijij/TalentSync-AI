import { useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

const states = { active: "Publicada", draft: "Borrador", paused: "Pausada", closed: "Cerrada" };
export function ExternalJobPublication({ data, busy, setBusy, onError, onSaved }) {
  const [status, setStatus] = useState(data.status in states ? data.status : "draft"), [note, setNote] = useState("");
  const blockers = (data.review?.checks || []).slice(1).filter(row => !row.passed);
  async function submit(event) {
    event.preventDefault(); setBusy(true); onError("");
    try {
      const { data: updated } = await api.patch(`/admin/jobs/${data.id}/catalog-status`, { status, revision: data.moderation_revision, note: note.trim() }, { __skipRetry: true });
      await onSaved(updated);
    } catch (error) { onError(getApiErrorMessage(error)); } finally { setBusy(false); }
  }
  return <form className="admin-editorial-form" onSubmit={submit}>
    <h4>Estado de la vacante en TalentSync</h4>
    <p>Publicar la incorpora al catálogo cuando cumple los controles. Borrador, Pausada y Cerrada la ocultan. Puedes volver a editar su información en cualquiera de estos estados.</p>
    <label>Estado en TalentSync<select className="field-control" disabled={busy} value={status} onChange={event => setStatus(event.target.value)}>{Object.entries(states).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    {status === "active" && blockers.length > 0 && <div role="status"><strong>Antes de publicar:</strong><ul>{blockers.map(row => <li key={row.label}>{row.label}</li>)}</ul><p>Completa la información en Contenido y edición o usa Comprobar fuente para actualizar su vigencia.</p></div>}
    <label>Motivo de la decisión<textarea className="field-control" rows={3} minLength={5} maxLength={2000} required placeholder="Explica qué revisaste y por qué eliges este estado" disabled={busy} value={note} onChange={event => setNote(event.target.value)} /></label>
    <button type="submit" className="button-primary" disabled={busy}>{busy ? "Guardando…" : status === "active" ? "Publicar vacante" : "Guardar estado"}</button>
    <small>Estado actual: {states[data.status] || data.status}{data.moderation_status === "held" ? " · fuera del catálogo por decisión editorial" : ""}. Los cambios de estado y contenido quedan registrados.</small>
  </form>;
}
