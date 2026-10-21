import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { renderToStaticMarkup } from "react-dom/server";

const require = createRequire(import.meta.url);
async function component(file, name) {
  const compiled = await build({ entryPoints: [fileURLToPath(new URL(`../src/components/${file}.jsx`, import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" }, plugins: [{ name: "no-network-in-render", setup(builder) { builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" })); builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {};", loader: "js" })); } }] });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return name ? module.exports[name] : module.exports;
}

const StructuredJobText = await component("StructuredJobText", "StructuredJobText");
const VacancyPicker = await component("VacancyPicker", "VacancyPicker");
const ScreeningQuestionsEditor = await component("ScreeningQuestionsEditor", "ScreeningQuestionsEditor");
const OfferPublicationStatus = await component("OfferPublicationStatus", "OfferPublicationStatus");
const OfferQualityBreakdown = await component("OfferQualityBreakdown", "OfferQualityBreakdown");
const WorkScheduleEditor = await component("WorkScheduleEditor", "WorkScheduleEditor");
const ExperienceRequirementEditor = await component("ExperienceRequirementEditor", "ExperienceRequirementEditor");
const RemoteScopeEditor = await component("RemoteScopeEditor", "RemoteScopeEditor");
const OfferConditions = await component("OfferConditions", "OfferConditions");
const ProcessStages = await component("ProcessStages", "ProcessStages");
const EducationRequirementsEditor = await component("EducationRequirementsEditor", "EducationRequirementsEditor");
const AcademicMatchDetails = await component("AcademicMatchDetails", "AcademicMatchDetails");
const LearningResourceCard = await component("LearningResourceCard", "LearningResourceCard");
const ExperienceFields = await component("ExperienceFields", "ExperienceFields");
const TextItemsEditor = await component("TextItemsEditor", "TextItemsEditor");
const ProfileCredentials = await component("ProfileCredentials", "ProfileCredentials");
const CredentialRequirementsEditor = await component("CredentialRequirementsEditor", "CredentialRequirementsEditor");
const CredentialRequirementsSummary = await component("CredentialSummary", "CredentialRequirementsSummary");
const CredentialMatchDetails = await component("CredentialSummary", "CredentialMatchDetails");
const CertificationFields = await component("CertificationFields", "CertificationFields");
const ProfileIdentity = await component("ProfileIdentity", "ProfileIdentity");
const DatePicker = await component("DatePicker", "DatePicker");

test("training records expose a selectable type and preserve older untyped entries", () => {
  const edit = renderToStaticMarkup(createElement(CertificationFields, { items: [{ name: "Gestión", kind: "diploma" }], editing: true, onChange() {} }));
  assert.match(edit, /Tipo de formación/);
  assert.match(edit, /value="diploma" selected/);
  assert.match(edit, /Seminario/);
  const legacy = renderToStaticMarkup(createElement(CertificationFields, { items: [{ name: "Formación anterior" }] }));
  assert.match(legacy, /Tipo sin indicar/);
});

test("profile identity labels name, title and contact fields independently", () => {
  const edit = renderToStaticMarkup(createElement(ProfileIdentity, { profile: {}, name: "Nombre ejemplo", email: "example@example.com", editing: true, onNameChange() {}, onChange() {} }));
  assert.match(edit, /Nombre completo/);
  assert.match(edit, /Título profesional/);
  assert.match(edit, /autoComplete="tel"/);
  assert.match(edit, /profile-identity-contact/);
});

test("date picker uses a themed dialog trigger and submits ISO dates separately", () => {
  const html = renderToStaticMarkup(createElement(DatePicker, { label: "Fecha", name: "checked", defaultValue: "2026-10-17" }));
  assert.match(html, /aria-haspopup="dialog"/);
  assert.match(html, /name="checked" value="2026-10-17"/);
  assert.match(html, /17 de octubre de 2026/);
  assert.ok(!html.includes('type="date"'));
});

test("document editors distinguish exact requested alternatives from academic affinity", () => {
  const html = renderToStaticMarkup(createElement(CredentialRequirementsEditor, { value: { driving_categories: ["B1"], professional_cards: ["Ingeniería civil"] }, onChange() {} }));
  assert.equal((html.match(/type="checkbox"/g) || []).length, 8);
  assert.match(html, /solicitará licencia de conducción y tarjeta profesional/);
  assert.match(html, /tener al menos una de ellas/);
  assert.match(html, /no sustituyen automáticamente/);
  assert.ok(!html.includes("Los nombres no reconocidos quedan por revisar"));
  const summary = renderToStaticMarkup(createElement(CredentialRequirementsSummary, { value: { driving_categories: ["B1", "C1"], professional_cards: ["Ingeniería civil"] } }));
  assert.match(summary, /B1 o C1/);
  assert.match(summary, /Ingeniería civil/);
  assert.equal(renderToStaticMarkup(createElement(CredentialRequirementsSummary, { value: {} })), "");
});

test("profile forms retain status and expiry while categories use the corresponding vehicle icon", () => {
  const props = { drivingLicenses: [{ category: "B1", status: "valid", expires_on: "2000-01-01" }], professionalCards: [{ profession: "Ingeniería civil", number: "CARD-123", status: "valid" }] };
  const html = renderToStaticMarkup(createElement(ProfileCredentials, props));
  assert.match(html, /Vencida por fecha/);
  assert.match(html, /credential-state expired/);
  assert.match(html, /CARD-123/);
  const edit = renderToStaticMarkup(createElement(ProfileCredentials, { ...props, editing: true, onChange() {} }));
  assert.match(edit, /aria-label="Quitar licencia 1"/);
  assert.match(edit, /Añadir tarjeta profesional/);
  assert.match(edit, /Fecha de vencimiento/);
  assert.match(edit, /Estado declarado/);
  assert.ok(!edit.includes('type="date"'));
});

test("document comparison communicates declarations and missing records without claiming verification", () => {
  const html = renderToStaticMarkup(createElement(CredentialMatchDetails, { value: { groups: [{ key: "license", label: "Licencia", accepted: ["B1"], status: "recorded", reason: "Pendiente de verificación documental." }, { key: "card", label: "Tarjeta", accepted: ["Ingeniería civil"], status: "missing", reason: "No hay registro." }], notice: "Revisión separada de la afinidad profesional." } }));
  assert.match(html, /Documento registrado · por verificar/);
  assert.match(html, /Sin registro/);
  assert.match(html, /Revisión separada/);
});

test("inline AI experience bullets render as separate safe list items", () => {
  const html = renderToStaticMarkup(createElement(StructuredJobText, { text: "• Revisé inventarios. • Analicé movimientos. • Registré <script>datos</script>." }));
  assert.equal((html.match(/<li /g) || []).length, 3);
  assert.match(html, /<ul /);
  assert.ok(!html.includes("<script>"));
  assert.match(html, /&lt;script&gt;datos/);
});

test("the vacancy search exposes one labelled combobox with the selected job", () => {
  const html = renderToStaticMarkup(createElement(VacancyPicker, { jobs: [], selected: { id: 7, title: "Analista de datos" }, query: "", onQuery() {}, onSelect() {} }));
  assert.equal((html.match(/<input /g) || []).length, 1);
  assert.ok(!html.includes("<select"));
  assert.match(html, /role="combobox"/);
  assert.match(html, /value="Analista de datos"/);
  assert.match(html, /Buscando para:/);
});

test("question editor renders saved choice scores and open answer controls", () => {
  const value = [{ id: "availability", prompt: "¿Puedes asistir los sábados?", type: "choice", required: true, options: ["Sí", "No"], option_scores: { "Sí": 3, "No": -1 } }, { id: "approach", prompt: "¿Cómo organizarías tus tareas?", type: "open", required: false, options: [] }];
  const html = renderToStaticMarkup(createElement(ScreeningQuestionsEditor, { value, onChange() {} }));
  assert.match(html, /value="3" selected=""/);
  assert.match(html, /value="-1" selected=""/);
  assert.match(html, /¿Cómo organizarías tus tareas\?/);
  assert.match(html, /Respuesta obligatoria/);
});

test("publication status separates the numeric minimum from missing required information", () => {
  const quality = { score: 74, minimum_publish_score: 60, can_publish: false, blockers: [{ label: "Contrato definido" }], issues: [] };
  const html = renderToStaticMarkup(createElement(OfferPublicationStatus, { quality }));
  assert.match(html, /Puntaje suficiente/);
  assert.match(html, /60\/100/);
  assert.match(html, /Contrato definido/);
  const ready = renderToStaticMarkup(createElement(OfferPublicationStatus, { quality: { ...quality, can_publish: true, blockers: [] } }));
  assert.match(ready, /Puedes publicar/);
  const published = renderToStaticMarkup(createElement(OfferPublicationStatus, { status: "active", quality: { ...quality, can_publish: true } }));
  assert.match(published, /Oferta publicada/);
  assert.ok(!published.includes("Lista para publicar") && !published.includes("Puedes publicar"));
});

test("quality breakdown shows earned responsibility points independently of missions", () => {
  const html = renderToStaticMarkup(createElement(OfferQualityBreakdown, { quality: { score: 15, checks: [{ key: "description", label: "Responsabilidades", step: 1, points: 15, weight: 15, passed: true, required: true }, { key: "missions", label: "Misiones", step: 1, points: 0, weight: 9, passed: false }] } }));
  assert.match(html, /70 puntos/);
  assert.match(html, /30 \(30%\)/);
  assert.match(html, /15\/24/);
  assert.match(html, /15\/15/);
  assert.match(html, /0\/9/);
});

test("schedule editor keeps legacy free text editable", () => {
  const html = renderToStaticMarkup(createElement(WorkScheduleEditor, { details: { schedule: "Sábados de 7:00 a 12:00" }, onChange() {} }));
  assert.match(html, /<textarea/);
  assert.match(html, /Sábados de 7:00 a 12:00/);
  assert.match(html, /Escribir horario/);
});

test("structured schedule displays calculated hours and custom time triggers", () => {
  const html = renderToStaticMarkup(createElement(WorkScheduleEditor, { details: { work_schedule: { mode: "fixed", days: ["mon", "tue", "wed", "thu", "fri"], start: "05:30", end: "15:30", break_minutes: 60, notes: "" } }, onChange() {} }));
  assert.match(html, /45 horas semanales/);
  assert.match(html, /descanso ya descontado/);
  assert.ok(!html.includes("Sin descuento") && !html.includes("sin descansos"));
  assert.match(html, /Se calculan y guardan automáticamente/);
  assert.equal((html.match(/aria-haspopup="dialog"/g) || []).length, 2);
  assert.ok(!html.includes('type="time"'));
  assert.ok(!html.includes("Usar estas horas"));
});

test("monthly experience and remote restrictions are visible to both editors and candidates", () => {
  const details = { seniority: "junior", experience_months: 6, remote_scope: { mode: "regions", countries: ["CO", "MX"], continents: ["EU"] } };
  const experience = renderToStaticMarkup(createElement(ExperienceRequirementEditor, { details, onChange() {} }));
  assert.match(experience, /6 meses/);
  assert.match(experience, /value="months" selected/);
  const remote = renderToStaticMarkup(createElement(RemoteScopeEditor, { value: details.remote_scope, onChange() {} }));
  assert.match(remote, /Continentes admitidos/);
  assert.match(remote, /Quitar CO/);
  assert.match(remote, /Quitar MX/);
  const publicView = renderToStaticMarkup(createElement(OfferConditions, { job: { modality: "remote", quality_details: details } }));
  assert.match(publicView, /6 meses/);
  assert.match(publicView, /Europa · Colombia · México/);
});

test("education levels appear in one list and secondary education has no career field or ongoing option", () => {
  const props = { level: "secondary", fields: ["Sistemas"], acceptsStudents: true, onChange() {} };
  const secondary = renderToStaticMarkup(createElement(EducationRequirementsEditor, props));
  assert.ok(!secondary.includes("<optgroup"));
  assert.ok(!secondary.includes('value="secondary_in_progress"'));
  assert.ok(!secondary.includes("Carreras o áreas aceptadas"));
  assert.match(secondary, /value="secondary" selected/);
  const technical = renderToStaticMarkup(createElement(EducationRequirementsEditor, { ...props, level: "technical" }));
  assert.match(technical, /value="technical" selected/);
  assert.ok(!technical.includes("_in_progress"));
  assert.match(technical, /Aceptar personas que aún están estudiando/);
  assert.match(technical, /type="checkbox" checked/);
  assert.match(technical, /Carreras o áreas aceptadas/);
  assert.match(technical, /Quitar Sistemas/);
});

test("long screening prompts and scored options use wrapping textareas and retain their complete text", () => {
  const prompt = "Describe un trabajo o proyecto donde utilizaste JavaScript para construir formularios accesibles y explica cómo verificaste el resultado con el equipo.";
  const option = "Verificar la fuente, documentar la diferencia y acordar con el equipo la corrección antes de continuar.";
  const html = renderToStaticMarkup(createElement(ScreeningQuestionsEditor, { value: [{ id: "example", prompt, type: "choice", required: true, options: [option, "Continuar sin revisar"], option_scores: { [option]: 3 } }], onChange() {} }));
  assert.equal((html.match(/<textarea /g) || []).length, 3);
  assert.ok(html.includes(prompt));
  assert.ok(html.includes(option));
  assert.match(html, /value="3" selected/);
  assert.match(html, /aria-label="Eliminar pregunta 1"/);
});

test("added text items are individual removable chips rather than a comma-separated input", () => {
  const html = renderToStaticMarkup(createElement(TextItemsEditor, { label: "Habilidades que la empresa enseñará", value: ["SQL", "Excel"], onChange() {} }));
  assert.match(html, /Quitar SQL/);
  assert.match(html, /Quitar Excel/);
  assert.ok(!html.includes('value="SQL,Excel"'));
  assert.match(html, /Añadir o Enter/);
});


test("long screening text has a 1000-character allowance and accessible option removal", () => {
  const prompt = "Explica cómo resolverías esta situación. ".repeat(20), option = "Verificar la información antes de continuar. ".repeat(15);
  const html = renderToStaticMarkup(createElement(ScreeningQuestionsEditor, { value: [{ id: "long", prompt, type: "choice", required: true, options: [option, "Otra alternativa"], option_scores: {} }], onChange() {} }));
  assert.equal((html.match(/maxLength="1000"/g) || []).length, 3);
  assert.ok(html.includes(prompt));
  assert.ok(html.includes(option));
  assert.match(html, /role="switch"/);
  assert.match(html, /aria-pressed="true"/);
  assert.match(html, /screening-remove-option/);
  assert.match(html, /<span>Eliminar<\/span>/);
});

test("process stages preserve the company's configured order in a compact list", () => {
  const html = renderToStaticMarkup(createElement(ProcessStages, { stages: [{ id: "received", title: "Recibidas" }, { id: "interview", title: "Entrevista" }] }));
  assert.equal((html.match(/<li/g) || []).length, 2);
  assert.ok(html.indexOf("Recibidas") < html.indexOf("Entrevista"));
  assert.ok(!html.includes("Etapa del tablero"));
});

test("academic policy is separate from level and students, and hidden for secondary", () => {
  const html = renderToStaticMarkup(createElement(EducationRequirementsEditor, { level: "university", fields: ["Contaduría Pública"], fieldPolicy: "exact", acceptsStudents: false, onChange() {} }));
  assert.match(html, /Solo las áreas seleccionadas/);
  assert.match(html, /También formaciones afines/);
  assert.match(html, /checked="" value="exact"/);
  assert.match(html, /Aceptar personas que aún están estudiando/);
  const secondary = renderToStaticMarkup(createElement(EducationRequirementsEditor, { level: "secondary", fields: [], onChange() {} }));
  assert.ok(!secondary.includes("education-policy") && !secondary.includes('type="radio"'));
});

test("academic uncertainty remains visible even without a numeric component", () => {
  const html = renderToStaticMarkup(createElement(AcademicMatchDetails, { value: { status: "review", reason: "Denominación no reconocida", policy: "related" } }));
  assert.match(html, /Falta información académica/);
  assert.ok(!html.includes("0%"));
  const partial = renderToStaticMarkup(createElement(AcademicMatchDetails, { value: { status: "partial", reason: "Áreas distintas relacionadas", policy: "related", requested_fields: ["Ingeniería de Sistemas"], required_level: "university", selected: { status: "related", candidate_degree: "Ingeniería Informática", requested_field: "Ingeniería de Sistemas", actual_level: "university", level_status: "meets" } } }));
  assert.match(partial, /Afinidad parcial/);
  assert.match(partial, /Ingeniería Informática/);
  assert.match(partial, /Ingeniería de Sistemas/);
  assert.match(partial, /Cumple el nivel/);
});

test("extracted employment months remain visible and education suggestions allow free text", () => {
  const html = renderToStaticMarkup(createElement(ExperienceFields, { items: [{ role: "Analista", company: "Avinal", start_year: "2025", end_year: "2025", start_date: "2025-07", end_date: "2025-11" }], editing: false }));
  assert.match(html, /jul/);
  assert.match(html, /nov/);
  const editor = renderToStaticMarkup(createElement(TextItemsEditor, { label: "Carreras", value: [], onChange() {}, suggestions: ["Contaduría Pública", "Gestión de Proyectos"] }));
  assert.match(editor, /<datalist/);
  assert.match(editor, /value="Gestión de Proyectos"/);
  assert.ok(!editor.includes("readonly"));
});

test("learning cards explain context without displaying a hiring probability", () => {
  const html = renderToStaticMarkup(createElement(LearningResourceCard, { resource: { id: "projects", title: "Gestión de proyectos", skills: ["gestión de proyectos"], category: "administration", hours: 4, provider: "Proveedor", instructions: "Curso de planificación y seguimiento.", relevance: { kind: "context", score: 75, reasons: ["Relacionado con la planificación y el seguimiento de proyectos de tu experiencia."] } } }));
  assert.match(html, /Por qué aparece para ti/);
  assert.match(html, /seguimiento de proyectos/);
  assert.ok(!html.includes("75%"));
});


test("field feedback connects its local message to the invalid input", async () => {
  const { ProfileFormFeedback, FormField } = await component("ProfileFormFeedback");
  const html = renderToStaticMarkup(createElement(ProfileFormFeedback, { errors: { "links.2.url": "Corrige este enlace" }, clearError() {} }, createElement(FormField, { path: "links.2.url", label: "Enlace" }, createElement("input", { value: "mal", onChange() {} }))));
  assert.match(html, /data-field-path="links.2.url"/);
  assert.match(html, /aria-invalid="true"/);
  assert.match(html, /aria-describedby="[^"]+-error"/);
  assert.match(html, /role="alert"/);
  assert.match(html, /Corrige este enlace/);
});

test("saved driving categories show motorcycle, car, heavy and articulated icons", () => {
  const html = renderToStaticMarkup(createElement(ProfileCredentials, { kind: "drivingLicenses", drivingLicenses: ["A2", "B1", "C2", "B3"].map((category) => ({ category })) }));
  for (const vehicle of ["motorcycle", "car", "heavy", "articulated"]) assert.match(html, new RegExp(`data-vehicle="${vehicle}"`));
});


test("academic comparison starts collapsed and retains all three explanations", () => {
  const html = renderToStaticMarkup(createElement(AcademicMatchDetails, { value: { status: "partial", required_level: "university", requested_fields: ["Ingeniería de Sistemas"], selected: { status: "exact", actual_level: "university", in_progress: true, candidate_degree: "Ingeniería de Sistemas" } } }));
  assert.match(html, /<details/);
  assert.match(html, /<summary/);
  assert.ok(!html.includes('open=""'));
  for (const text of ["Área de formación", "Nivel académico", "Finalización del estudio"]) assert.ok(html.includes(text));
});

test("dashboard formation shows saved courses and opens the chosen plan directly", async () => {
  const DashboardLearning = await component("DashboardLearning", "DashboardLearning");
  const render = (props) => renderToStaticMarkup(createElement(MemoryRouter, null, createElement(DashboardLearning, props)));
  const active = render({ plans: [{ id: 1, status: "in_progress", resource: { id: "sql-one", title: "SQL aplicado", provider: "Ejemplo" } }] });
  assert.match(active, /SQL aplicado/);
  assert.match(active, /resource=sql-one#mi-plan/);
  assert.ok(!active.includes("Aprende con un objetivo"));
  const saved = render({ certifications: [{ name: "Excel básico", issuer: "Instituto" }] });
  assert.match(saved, /Excel básico/);
  assert.match(saved, /profile-certifications/);
});
