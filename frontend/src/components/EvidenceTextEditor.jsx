import { useId, useState } from "react";
import { LoaderCircle, PencilLine, Save } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { CoachDialog } from "./CoachDialog.jsx";

export function EvidenceTextEditor({ row, onClose, onSaved }) {
  const [title, setTitle] = useState(row.title || "");
  const [description, setDescription] = useState(row.description || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const helpId = useId();
  const valid = title.trim().length >= 3 && title.trim().length <= 160 && description.trim().length >= 10 && description.trim().length <= 2000;

  async function save(event) {
    event.preventDefault();
    if (saving || !valid) return;
    setSaving(true); setError("");
    try {
      const { data } = await api.patch(`/matching/evidence/${row.id}`, { title: title.trim(), description: description.trim() });
      onSaved(data);
    } catch (failure) {
      setError(getApiErrorMessage(failure, "No pudimos guardar los cambios. Tu texto sigue aquí para volver a intentarlo."));
    } finally { setSaving(false); }
  }

  return <CoachDialog open title="Editar texto de la evidencia" Icon={PencilLine} className="evidence-edit-dialog" closeDisabled={saving} onClose={onClose}>
    <form className="evidence-edit-form" onSubmit={save} aria-busy={saving}>
      <p id={helpId}>Cuenta con tus propias palabras qué construiste y cuál fue tu aporte. El enlace y las habilidades de esta evidencia se conservan.</p>
      <fieldset disabled={saving}>
        <label>Título<input className="field-control" value={title} onChange={(event) => setTitle(event.target.value)} required minLength={3} maxLength={160} /></label>
        <label>Tu aporte y resultado<textarea className="field-control" value={description} onChange={(event) => setDescription(event.target.value)} rows={7} required minLength={10} maxLength={2000} aria-describedby={helpId} /></label>
        <span className="evidence-edit-count">{description.length}/2000 caracteres</span>
      </fieldset>
      {error && <p className="evidence-feedback evidence-feedback-error" role="alert">{error}</p>}
      {saving && <p className="evidence-field-help" role="status">Guardando cambios…</p>}
      <footer><button type="button" className="button-secondary" disabled={saving} onClick={onClose}>Cancelar</button><button type="submit" className="button-primary" disabled={saving || !valid}>{saving ? <LoaderCircle size={16} className="animate-spin" /> : <Save size={16} />}{saving ? "Guardando…" : "Guardar cambios"}</button></footer>
    </form>
  </CoachDialog>;
}
