import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";
import { createElement } from "react";
import { MemoryRouter } from "react-router-dom";
import { renderToStaticMarkup } from "react-dom/server";
import { comparisonFacts, comparisonIds, comparisonRequirements, comparisonSalary, toggleComparedJob } from "../src/utils/jobComparison.js";
import { activeInterview, interviewDateParts, interviewInputUtc, interviewInputValue, processDate, upcomingInterviews } from "../src/utils/interviewAgenda.js";

const require = createRequire(import.meta.url);
async function components(file) {
  const compiled = await build({ entryPoints: [fileURLToPath(new URL(`../src/components/${file}.jsx`, import.meta.url))], bundle: true, write: false, platform: "node", format: "cjs", jsx: "automatic", packages: "external", loader: { ".css": "empty" }, plugins: [{ name: "no-network", setup(builder) {
    builder.onResolve({ filter: /api\/client\.js$/ }, () => ({ path: "api", namespace: "test" }));
    builder.onLoad({ filter: /.*/, namespace: "test" }, () => ({ contents: "export const api = {}; export const getApiErrorMessage = () => '';", loader: "js" }));
  } }] });
  const module = { exports: {} };
  new Function("require", "module", "exports", compiled.outputFiles[0].text)(require, module, module.exports);
  return module.exports;
}
const { JobComparisonTable, JobComparison } = await components("JobComparison");
const { InterviewAgenda, ProcessInterview } = await components("InterviewAgenda");
const { VacancyCard } = await components("VacancyCard");
const { ApplicationAnswersModal } = await components("ApplicationAnswersModal");
const { RecruiterProcessDialog } = await components("RecruiterProcessDialog");
const render = (element) => renderToStaticMarkup(createElement(MemoryRouter, {}, element));
const now = new Date("2026-10-22T12:00:00Z");
const jobs = [{ id: 1, title: "Analista de inventarios", company_name: "Distribución", modality: "hybrid", salary: 3000000, skills: ["excel"], quality_details: { salary_max: 4000000, weekly_hours: 40, contract_type: "indefinite", experience_months: 0 } }, { id: 2, title: "Operaciones de datos", company_name: "Reportes", skills: ["sql"] }];
const appointment = { id: 5, application_id: 5, job_title: "Analista de inventarios", company_name: "Distribución", status: "technical_interview", interview_at: "2026-10-26T14:00:00" };

test("comparison has no empty banner and vacancy actions do not repeat a checkbox row", () => {
  assert.equal(render(createElement(JobComparison, { selection: { ids: [] }, jobs })), "");
  const html = render(createElement(VacancyCard, { job: { ...jobs[0], created_at: "2026-10-20T10:00:00Z", skills: ["excel", "sql", "git", "python"] }, comparison: { ids: [1], toggle() {} }, match: 75, showMatch: true }));
  assert.match(html, /vacancy-modality">Híbrido/);
  assert.match(html, /Quitar de comparación: Analista de inventarios/);
  assert.match(html, /aria-pressed="true"/);
  assert.match(html, /aria-label="Compatibilidad 75 por ciento"/);
  assert.match(html, /role="progressbar"[^>]*aria-valuenow="75"/);
  assert.match(html, />\+1</);
  assert.doesNotMatch(html, /type="checkbox"|Compara tus opciones/);
});

test("vacancy cards preserve unknown location and compatibility instead of inventing flexibility or a zero score", () => {
  const job = { ...jobs[0], modality: "onsite", location: null, department: null };
  for (const match of [null, undefined, "", NaN, Infinity]) {
    const html = render(createElement(VacancyCard, { job, match, showMatch: true }));
    assert.match(html, /Ubicación por confirmar/);
    assert.doesNotMatch(html, /Ubicación flexible|role="progressbar"/);
  }
  const zero = render(createElement(VacancyCard, { job, match: 0, showMatch: true }));
  assert.match(zero, /aria-label="Compatibilidad 0 por ciento"/);
});

test("applied vacancy cards expose the existing process and highlight its status", () => {
  const html = render(createElement(VacancyCard, { job: jobs[0], application: { id: 45, status: "technical_interview" } }));
  assert.match(html, /is-applied/);
  assert.match(html, /Postulación enviada/);
  assert.match(html, /Entrevista/);
  assert.match(html, /href="\/procesos\/45"/);
  assert.match(html, /Ver mi proceso/);
});

test("answer review shows one question and preserves pending board adjustments without process fields", () => {
  const html = render(createElement(ApplicationAnswersModal, { application: { id: 5, candidate_name: "Ejemplo", base_match_percentage: 59, screening_answer_adjustments: { first: 2 }, screening_answers: [{ question_id: "first", question: "Primera pregunta específica", answer: "Mi evidencia", type: "open" }, { question_id: "second", question: "Segunda pregunta específica", answer: "Otra evidencia", type: "open" }] }, onPrepare() {}, onClose() {} }));
  assert.match(html, /Primera pregunta específica/);
  assert.doesNotMatch(html, /Segunda pregunta específica|Notas internas|Fecha y hora/);
  assert.match(html, /value="2" selected/);
  assert.match(html, /Preparar valoración/);
  assert.match(html, /61%/);
  assert.match(html, /Pregunta 1 de 2/);
});

test("process management keeps notes and scheduling separate from answer scoring", () => {
  const html = render(createElement(RecruiterProcessDialog, { application: { id: 5, candidate_name: "Ejemplo", recruiter_notes: "Revisar disponibilidad", screening_answers: [{ question_id: "first", question: "Pregunta fuera del proceso", answer: "Respuesta privada" }] }, onClose() {}, onDelete() {}, onSave() {} }));
  assert.match(html, /Notas internas/);
  assert.match(html, /Revisar disponibilidad/);
  assert.match(html, /Fecha y hora de entrevista/);
  assert.match(html, /Preparar cambios/);
  assert.doesNotMatch(html, /Pregunta fuera del proceso|Respuesta privada|Valoración manual/);
});

test("comparison selection survives corrupt storage, deduplicates and enforces three choices", () => {
  assert.deepEqual(comparisonIds("broken"), []);
  assert.deepEqual(comparisonIds('{"ids":[1]}'), []);
  assert.deepEqual(comparisonIds('[1,1,"2",null,-3,2,3,4]'), [1, 2, 3]);
  assert.deepEqual(toggleComparedJob([1, 2, 3], 4), [1, 2, 3]);
  assert.deepEqual(toggleComparedJob([1, 2, 3], 2), [1, 3]);
  assert.deepEqual(toggleComparedJob([1, 2], 3), [1, 2, 3]);
  assert.deepEqual(toggleComparedJob([1], NaN), [1]);
});

test("comparison does not infer salaries, zero years, language fluency or required degrees from missing data", () => {
  const unknown = comparisonFacts({});
  assert.equal(unknown.salary, "Salario no informado");
  assert.equal(unknown.experience, "Experiencia por definir");
  assert.equal(unknown.education, "Formación sin especificar");
  assert.equal(unknown.languages, "Idiomas sin especificar");
  assert.match(comparisonFacts(jobs[0]).salary, /3\.000\.000 – 4\.000\.000 COP \/ mes/);
  assert.equal(comparisonFacts(jobs[0]).experience, "Sin experiencia previa");
  assert.match(comparisonSalary({ salary: 60000, source_kind: "external" }), /moneda por confirmar.*período por confirmar/);
  assert.match(comparisonFacts({ modality: "remote", quality_details: { remote_scope: { mode: "regions", countries: ["CO"], continents: [] } } }).location, /Colombia/);
});

test("requirements keep partial and unknown results separate from covered skills", () => {
  assert.equal(comparisonRequirements(null), null);
  const rows = comparisonRequirements({ match_details: { requirements: [{ skill: "excel", covered: true }, { skill: "sql", covered: false, status: "partial" }, { skill: "python" }] } });
  assert.deepEqual(rows.covered.map((row) => row.skill), ["excel"]);
  assert.deepEqual(rows.pending.map((row) => row.skill), ["sql", "python"]);
  const html = render(createElement(JobComparisonTable, { jobs, matches: { 1: { match_percentage: 0, match_details: { requirements: [{ skill: "excel", covered: false }] } } } }));
  assert.match(html, /0%/);
  assert.match(html, /Sin cálculo disponible/);
  assert.match(html, /Sin detalle disponible/);
  assert.match(html, /scope="col"/);
  assert.match(html, /scope="row"/);
  assert.match(html, /Tabla de comparación de vacantes/);
  assert.doesNotMatch(html, /undefined|NaN|Ganadora/);
});

test("comparison keeps an unavailable selection removable and requires two available jobs", () => {
  const html = render(createElement(JobComparison, { selection: { ids: [1, 999], toggle() {}, clear() {} }, jobs, loading: false }));
  assert.match(html, /Oferta no disponible/);
  assert.match(html, /Quitar oferta no disponible de la comparación/);
  assert.match(html, /disabled=""[^>]*>.*?Comparar/s);
});

test("agenda sorts future open processes and excludes missing, invalid, past or finalized dates", () => {
  const rows = [appointment, { ...appointment, id: 8, interview_at: "2026-10-25T14:00:00Z" }, ...["rejected", "accepted", "hired"].map((status) => ({ ...appointment, status })), { ...appointment, released_at: "2026-10-22" }, { ...appointment, interview_at: "invalid" }, { ...appointment, interview_at: "2026-10-20T14:00:00Z" }, { ...appointment, interview_at: null }];
  assert.deepEqual(upcomingInterviews(rows, now).map((row) => row.id), [8, 5]);
  assert.equal(activeInterview({ ...appointment, interview_at: now.toISOString() }, now), false);
  assert.equal(processDate("invalid"), null);
});

test("editing a saved interview preserves the instant across offsets and incomplete inputs", () => {
  assert.equal(interviewInputValue("2026-10-26T14:00:00"), "2026-10-26T09:00");
  assert.equal(interviewInputValue("2026-10-26T09:00:00-05:00"), "2026-10-26T09:00");
  assert.equal(interviewInputUtc("2026-10-26T09:00"), "2026-10-26T14:00:00.000Z");
  assert.equal(interviewInputUtc(interviewInputValue(appointment.interview_at)), processDate(appointment.interview_at).toISOString());
  assert.equal(interviewInputValue("2026-10-26T04:30:00Z"), "2026-10-25T23:30");
  for (const invalid of ["", "2026-10-26T", "2026-02-30T09:00", "2026-10-26T25:00"]) assert.equal(interviewInputUtc(invalid), null);
  assert.equal(interviewDateParts("2026-10-26T04:30:00").day, "25");
});

test("agenda distinguishes loading and failure from an empty calendar and explains manual import", () => {
  const html = render(createElement(InterviewAgenda, { applications: [appointment], now }));
  assert.match(html, /1 cita próxima/);
  assert.match(html, /Añadir al calendario/);
  assert.match(html, /recordatorio de 30 minutos/);
  assert.match(html, /No se sincroniza/);
  assert.match(html, /Duración|duración/);
  const error = render(createElement(InterviewAgenda, { applications: [], now, error: "No pudimos consultar tus procesos" }));
  assert.match(error, /role="alert"/);
  assert.doesNotMatch(error, /Las próximas citas aparecerán/);
  const loading = render(createElement(InterviewAgenda, { applications: [], loading: true, now }));
  assert.match(loading, /Cargando entrevistas/);
  assert.doesNotMatch(loading, /Las próximas citas aparecerán/);
  const closed = render(createElement(ProcessInterview, { process: { ...appointment, status: "hired" }, now }));
  assert.match(closed, /El proceso finalizó/);
  assert.doesNotMatch(closed, /Añadir al calendario/);
});
