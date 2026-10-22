import { useState } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { PageHeader } from "../src/components/PageHeader.jsx";
import { CandidateHero } from "../src/components/CandidateHero.jsx";
import { LanguageSummary } from "../src/components/LanguageSummary.jsx";
import { LearningFilters } from "../src/components/LearningFilters.jsx";
import { LearningResourceCard } from "../src/components/LearningResourceCard.jsx";
import { PreparationWorkspace } from "../src/components/PreparationWorkspace.jsx";
import { JobComparison } from "../src/components/JobComparison.jsx";
import { InterviewAgenda } from "../src/components/InterviewAgenda.jsx";
import { toggleComparedJob } from "../src/utils/jobComparison.js";
import "../src/styles/index.css";
import "./quality.css";

const params = new URLSearchParams(window.location.search);
document.documentElement.dataset.theme = params.get("theme") || "light";
const role = ["candidate", "company", "admin"].includes(params.get("role")) ? params.get("role") : "candidate";
const experiences = [{ role: "Analista de inventario y reportes", company: "Equipo de distribución", description: "Organicé los registros y preparé reportes en Excel para el equipo.", start_date: "2021-01", end_date: "2023-01" }];
const questions = [{ id: "introduction", title: "¿Qué parte de tu trayectoria se relaciona con este cargo?", hint: "Describe una experiencia real y tu participación.", experiences }];
const data = { job: { title: "Analista de operaciones · inventarios y coordinación de entregas", company_name: "Equipo de distribución" }, profile: { summary: experiences[0].description, experiences, skills: ["excel", "logística", "gestión de inventarios"] }, versions: [], interview: { questions, ask_company: ["¿Qué resultados esperan en los primeros tres meses?"], answers: {}, version: 0 } };
const resource = { id: "review-excel", title: "Prepara reportes de inventario con Excel y tablas dinámicas", provider: "Formación de ejemplo para revisión", category: "business", skills: ["excel", "gestión de inventarios"], targeted_skills: ["excel"], hours: 12, cost: "free", active: true };
const comparisonJobs = [
  { id: 101, title: "Analista de inventarios y coordinación de entregas", company_name: "Distribución de ejemplo", salary: 3000000, modality: "hybrid", skills: ["excel", "gestión de inventarios"], quality_details: { weekly_hours: 40, contract_type: "indefinite" } },
  { id: 102, title: "Analista de operaciones y elaboración de reportes", company_name: "Equipo de operaciones", salary: 3500000, modality: "remote", skills: ["excel", "sql"] },
  { id: 103, title: "Coordinación de logística", company_name: "Operaciones de ejemplo", modality: "onsite", skills: ["logística"] },
];
const agendaRows = [{ id: 101, job_title: comparisonJobs[0].title, company_name: comparisonJobs[0].company_name, status: "technical_interview", interview_at: "2026-10-26T14:00:00" }];

function QualityPage() {
  const [selected, setSelected] = useState([101, 102]);
  const [tab, setTab] = useState("cv"), [filters, setFilters] = useState({}), [answers, setAnswers] = useState({}), [dirty, setDirty] = useState(false), [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ summary: data.profile.summary, experiences: [0], skills: data.profile.skills, style: "modern", includePhoto: false });
  return <MemoryRouter><main className={`quality-shell role-${role}`}><p className="quality-label">Datos ficticios para comprobar componentes. Esta página no se incluye en la aplicación publicada.</p>
    <PageHeader kicker="TalentSync" title="Prepara tu próxima oportunidad" description="Comprueba filtros, tarjetas y preparación con textos largos, estados vacíos y diferentes tamaños de pantalla." actions={<button type="button" className="button-secondary">Revisar mi perfil</button>} />
    <section data-quality="profile"><CandidateHero candidate={{ name: "María Alejandra Restrepo Gómez Delgado", profession: "Analista de operaciones y coordinación de inventarios", email: "candidata@example.com", location: "Medellín", department: "Antioquia", skills: [] }}><div><h2>Compatibilidad para esta vacante</h2><p>Consulta los requisitos de la oferta.</p></div></CandidateHero><LanguageSummary value={[{ name: "Inglés", level: "B1" }, { name: "Español", level: "NATIVE" }]} /></section>
    <section data-quality="filters"><LearningFilters value={filters} onChange={setFilters} resources={[resource]} resultCount={1} /></section>
    <section className="quality-course-grid" data-quality="course"><LearningResourceCard resource={resource} compact onPlan={() => {}} /><LearningResourceCard resource={{ ...resource, id: "review-long", title: "Herramientas para analizar, organizar y comunicar información de operaciones a diferentes equipos", cost: "unknown" }} compact onPlan={() => {}} /></section>
    <section data-quality="comparison"><div className="quality-comparison-options">{comparisonJobs.map((job) => <label key={job.id}><input type="checkbox" checked={selected.includes(job.id)} disabled={selected.length === 3 && !selected.includes(job.id)} onChange={() => setSelected((current) => toggleComparedJob(current, job.id))} />{job.title}</label>)}</div><JobComparison jobs={comparisonJobs} matches={{ 101: { match_percentage: 75 } }} selection={{ ids: selected, toggle: (id) => setSelected((current) => toggleComparedJob(current, id)), clear: () => setSelected([]) }} /></section>
    <section data-quality="agenda"><InterviewAgenda applications={agendaRows} now={new Date("2026-10-22T00:00:00Z")} /></section>
    <section className="quality-preparation" data-quality="preparation">{saved && <p role="status">Respuestas guardadas</p>}<PreparationWorkspace data={data} tab={tab} onTab={setTab} form={form} onForm={setForm} answers={answers} onAnswer={(id, key, value) => { setAnswers((current) => ({ ...current, [id]: { ...current[id], [key]: value } })); setDirty(true); setSaved(false); }} questionIndex={0} onQuestion={() => {}} dirty={dirty} onSaveInterview={() => { setSaved(true); setDirty(false); }} onDownloadNotes={() => {}} onCreateVersion={() => {}} onPreview={() => {}} onDownload={() => {}} /></section>
  </main></MemoryRouter>;
}

createRoot(document.getElementById("root")).render(<QualityPage />);
