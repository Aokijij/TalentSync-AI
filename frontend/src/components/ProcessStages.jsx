import "../styles/offer-editing.css";

const DEFAULT_STAGES = [{ id: "submitted", title: "Recibida" }, { id: "reviewing", title: "En revisión" }, { id: "interview", title: "Entrevista" }, { id: "hired", title: "Contratación" }, { id: "rejected", title: "No seleccionada" }];

export function ProcessStages({ stages }) {
  return <section className="offer-process-stages"><h3>Etapas del proceso</h3><ol>{(stages?.length ? stages : DEFAULT_STAGES).map((row, index) => <li key={row.id}><span>{index + 1}</span>{row.title}</li>)}</ol><p>Puedes personalizarlas en Postulaciones después de guardar.</p></section>;
}
