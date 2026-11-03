import { useState } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { Check, FileCheck2, List } from "lucide-react";
import { AuthContext } from "../src/contexts/AuthContext.jsx";
import { ThemeContext } from "../src/contexts/ThemeContext.jsx";
import { FeedbackProvider } from "../src/contexts/FeedbackContext.jsx";
import { AppLayout } from "../src/layouts/AppLayout.jsx";
import { PageHeader } from "../src/components/PageHeader.jsx";
import { ConfirmModal } from "../src/components/ConfirmModal.jsx";
import { FormField, ProfileFormFeedback } from "../src/components/ProfileFormFeedback.jsx";
import { Panel, WorkspaceTabs } from "../src/components/ui/Panel.jsx";

export function DesignClosureReview({ role, theme }) {
  return <MemoryRouter initialEntries={["/revision"]}><ThemeContext.Provider value={{ theme, toggleTheme() {} }}><AuthContext.Provider value={{ user: { id: 1, name: "Persona de revisión", role }, logout() {} }}><FeedbackProvider><Routes><Route element={<AppLayout />}><Route path="*" element={<Controls />} /></Route></Routes></FeedbackProvider></AuthContext.Provider></ThemeContext.Provider></MemoryRouter>;
}

function Controls() {
  const [tab, setTab] = useState("summary"), [description, setDescription] = useState("");
  const [open, setOpen] = useState(false), [attempts, setAttempts] = useState(0);
  async function save() {
    const next = attempts + 1; setAttempts(next);
    await new Promise((resolve) => setTimeout(resolve, 400));
    if (next === 1) {
      const error = new Error("Simulated failure");
      error.response = { data: { detail: "No se pudo guardar. Revisa la conexión y vuelve a intentarlo." } };
      throw error;
    }
    setOpen(false);
  }
  return <div className="space-y-6"><PageHeader kicker="Datos ficticios" title="Revisión de diseño y accesibilidad" description="Componentes reales de candidato, empresa y administración." />
    <WorkspaceTabs id="design" label="Secciones de revisión" value={tab} onChange={setTab} items={[["summary", "Resumen", List], ["preview", "Vista previa", FileCheck2]]} />
    <div role="tabpanel" id="design-panel-summary" aria-labelledby="design-tab-summary" hidden={tab !== "summary"}><Panel title="Información del proceso" description="Los campos mantienen sus etiquetas y ayudas durante la edición.">
      <ProfileFormFeedback errors={{ required: "Revisa este dato antes de guardar." }} clearError={() => {}}><div className="ui-filter-grid" style={{ "--filter-columns": 2 }}>
        <FormField label="Descripción" path="description" help="Indica la información que quieres compartir con el equipo."><input className="field-control" placeholder="Describe el contenido que quieres registrar" value={description} onChange={(event) => setDescription(event.target.value)} /></FormField>
        <FormField label="Dato requerido" path="required" help="Esta explicación permanece visible si hay un error."><input className="field-control" defaultValue="" /></FormField>
        <FormField label="Estado" path="state"><select className="field-control"><option>En revisión</option><option>Finalizado</option></select></FormField>
        <FormField label="Referencia guardada" path="reference"><input className="field-control" value="Consulta de solo lectura" readOnly /></FormField>
      </div></ProfileFormFeedback>
      <div className="ui-panel-actions ui-card-actions mt-5"><button type="button" className="button-primary design-primary" onClick={() => setOpen(true)}><Check size={17} />Guardar preferencias</button><button type="button" className="button-secondary">Cancelar edición</button><button type="button" className="button-primary" disabled>Acción no disponible</button><button type="button" className="button-danger design-danger">Acción de eliminación</button></div>
      <output aria-label="Intentos de guardado">{attempts}</output>
    </Panel></div>
    <div role="tabpanel" id="design-panel-preview" aria-labelledby="design-tab-preview" hidden={tab !== "preview"}><Panel title="Vista previa"><p>Los datos de la edición se conservan al cambiar de sección.</p></Panel></div>
    <ConfirmModal open={open} title="Guardar preferencias" description="Solo se actualizarán las preferencias de esta revisión." confirmLabel="Confirmar guardado" onClose={() => setOpen(false)} onConfirm={save} />
  </div>;
}
