import { useState } from "react";
import { PageHeader } from "../src/components/PageHeader.jsx";
import { InlineNotice } from "../src/components/ui/Panel.jsx";
import { IntegrationStatus } from "../src/components/IntegrationStatus.jsx";
import { LearningFilters } from "../src/components/LearningFilters.jsx";
import { LearningResourceCard } from "../src/components/LearningResourceCard.jsx";
import { VacancyCard } from "../src/components/VacancyCard.jsx";
import { CoachDialog } from "../src/components/CoachDialog.jsx";
import { useFeedback } from "../src/contexts/FeedbackContext.jsx";

const integrations = [
  { id: "youtube", name: "YouTube", implemented: true, enabled: true, configured: true, operational_state: "observed", status: "Consulta e importación editorial disponibles.", last_attempt_at: "2026-10-22T15:00:00Z", last_success_at: "2026-10-22T15:00:00Z", last_error: "", next_steps: "Revisar contenido y habilidades antes de publicar.", action_url: "/admin/aprendizaje", action_label: "Revisar fuente" },
  { id: "learn", name: "Microsoft Learn", implemented: true, enabled: true, configured: true, operational_state: "error", status: "La configuración está disponible; la última consulta falló.", last_attempt_at: "2026-10-22T15:05:00Z", last_success_at: "2026-10-21T12:00:00Z", last_error: "La última operación no pudo completarse. Revisa la fuente desde su sección.", next_steps: "Revisar el acceso y los permisos de la aplicación." },
  { id: "social", name: "Acceso social", implemented: true, enabled: true, configured: false, operational_state: "not_configured", status: "No hay proveedores configurados.", next_steps: "Configurar un proveedor y comprobar el acceso." },
];
const resource = { id: "review", title: "Análisis de datos con hojas de cálculo", provider: "Formación de ejemplo", category: "administration", kind: "course", url: "https://example.org/course", instructions: "Organiza tablas y revisa sus datos con ejercicios del proveedor.", details: { languages: ["es"] }, skills: ["excel"], hours: 12, cost: "free", active: true };
export function SystemReview() {
  const feedback = useFeedback();
  const [filters, setFilters] = useState({}), [open, setOpen] = useState(false), [text, setText] = useState(""), [saved, setSaved] = useState(false);
  async function close() {
    if (text && !await feedback.confirm({ title: "Descartar los cambios", description: "Se perderá el texto que todavía no has guardado. El contenido guardado se conservará.", tone: "warning", confirmLabel: "Descartar cambios", cancelLabel: "Seguir editando" })) return;
    setOpen(false); setText("");
  }
  return <><section data-quality="system" className="system-review">
    <PageHeader kicker="Revisión de componentes" title="Componentes de la plataforma" description="Filtros, tarjetas y estados con el mismo lenguaje visual." />
    <InlineNotice tone="success" title="Preferencias guardadas">La vista del CV utiliza los apartados que seleccionaste.</InlineNotice>
    <InlineNotice tone="warning" title="Cambios sin guardar">Puedes seguir editando o guardar antes de salir.</InlineNotice>
    <div className="system-review-actions"><button type="button" className="button-primary" onClick={() => setOpen(true)}>Abrir editor de ejemplo</button><button type="button" className="button-secondary" onClick={() => {
      feedback.notify("Preferencias actualizadas.", { title: "Cambios guardados", tone: "success", duration: 0 });
      feedback.notify("No se pudo guardar el nombre del CV. Inténtalo de nuevo.", { tone: "error" });
    }}>Probar avisos</button><button type="button" className="button-danger" onClick={async () => { if (await feedback.confirm({ title: "Eliminar este borrador", description: "El borrador se eliminará definitivamente.", details: ["Los CV ya enviados se conservan.", "Esta acción no se puede deshacer."], destructive: true, confirmLabel: "Eliminar borrador" })) feedback.notify("Borrador eliminado."); }}>Eliminar borrador de ejemplo</button></div>
    <LearningFilters value={filters} onChange={setFilters} resources={[resource]} resultCount={1} />
    <div className="system-review-cards"><LearningResourceCard compact resource={resource} onPlan={() => {}} /><VacancyCard job={{ id: 101, company_id: 101, title: "Analista de datos", company_name: "Empresa de ejemplo", location: "Medellín", modality: "hybrid", skills: ["excel", "sql"], salary: 3000000, description: "Organiza los registros y presenta información útil al equipo." }} match={75} showMatch /></div>
    <IntegrationStatus rows={integrations} />
    {saved && <InlineNotice tone="success" title="Texto guardado">El cambio se ha conservado en este ejemplo.</InlineNotice>}
  </section><CoachDialog open={open} onClose={close} title="Editar el resumen"><div className="system-review-editor"><label className="ui-filter-field">Resumen<textarea className="field-control" value={text} onChange={(event) => setText(event.target.value)} /></label><button type="button" className="button-primary" onClick={() => { setSaved(true); setOpen(false); setText(""); feedback.notify("Resumen guardado."); }}>Guardar resumen</button></div></CoachDialog></>;
}
