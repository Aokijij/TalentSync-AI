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
import { FeedbackProvider } from "../src/contexts/FeedbackContext.jsx";
import { VacancyCard } from "../src/components/VacancyCard.jsx";
import { ApplicationAnswersModal } from "../src/components/ApplicationAnswersModal.jsx";
import { RecruiterProcessDialog } from "../src/components/RecruiterProcessDialog.jsx";
import { ChallengeCatalog } from "../src/components/ChallengeCatalog.jsx";
import { ChallengeWorkspace, ChallengeResult } from "../src/components/ChallengeWorkspace.jsx";
import { ProcessWorkspace } from "../src/components/ProcessWorkspace.jsx";
import { toggleComparedJob } from "../src/utils/jobComparison.js";
import "../src/styles/index.css";
import "./quality.css";

const params = new URLSearchParams(window.location.search);
document.documentElement.dataset.theme = params.get("theme") || "light";
const role = ["candidate", "company", "admin"].includes(params.get("role")) ? params.get("role") : "candidate";
const experiences = [{ role: "Analista de inventario y reportes", company: "Equipo de distribución", description: "Organicé los registros y preparé reportes en Excel para el equipo.", start_date: "2021-01", end_date: "2023-01" }];
const questions = [{ id: "introduction", category: "Trayectoria y cargo", title: "¿Qué parte de tu trayectoria se relaciona con este cargo?", hint: "Describe una experiencia real y tu participación.", context: "Reconciliar el inventario y coordinar entregas con el equipo.", follow_ups: ["¿Qué registros revisaste?", "¿Cómo comprobaste las diferencias?"], experiences }];
const data = { job: { title: "Analista de operaciones · inventarios y coordinación de entregas", company_name: "Equipo de distribución" }, profile: { summary: experiences[0].description, experiences, skills: ["excel", "logística", "gestión de inventarios"] }, versions: [], interview: { questions, ask_company: ["¿Qué resultados esperan en los primeros tres meses?"], answers: {}, version: 0 } };
const resource = { id: "review-excel", title: "Prepara reportes de inventario con Excel y tablas dinámicas", provider: "Formación de ejemplo para revisión", category: "business", skills: ["excel", "gestión de inventarios"], targeted_skills: ["excel"], hours: 12, cost: "free", active: true };
const comparisonJobs = [
  { id: 101, title: "Analista de inventarios y coordinación de entregas", company_name: "Distribución de ejemplo", salary: 3000000, modality: "hybrid", skills: ["excel", "gestión de inventarios"], quality_details: { weekly_hours: 40, contract_type: "indefinite" } },
  { id: 102, title: "Analista de operaciones y elaboración de reportes", company_name: "Equipo de operaciones", salary: 3500000, modality: "remote", skills: ["excel", "sql"] },
  { id: 103, title: "Coordinación de logística", company_name: "Operaciones de ejemplo", modality: "onsite", skills: ["logística"] },
];
const agendaRows = [{ id: 101, job_title: comparisonJobs[0].title, company_name: comparisonJobs[0].company_name, status: "technical_interview", interview_at: "2026-10-26T14:00:00" }];
const practiceExample = { id: "example-attempt", assessment_id: "example-python", status: "active", title: "Fundamentos de Python", skill: "python", questions: [{ id: "example-default", prompt: "¿Qué firma evita compartir una lista mutable entre llamadas?", choices: ["def f(items=[])", "def f(items=None) y crear la lista dentro", "def f(items=list())"] }, { id: "example-errors", prompt: "¿Cómo tratarías un dato inesperado?", choices: ["Validarlo y comunicar el error", "Ignorarlo y continuar"] }] };

const exampleApplications = { 101: { id: 901, status: "technical_interview", created_at: "2026-10-20T12:00:00" } };

function QualityPage() {
  const [interestStates, setInterestStates] = useState(new Map());
  const interests = { enabled: true, byId: interestStates, save: (id, value) => setInterestStates((current) => new Map(current).set(id, value)), remove: (id) => setInterestStates((current) => { const next = new Map(current); next.delete(id); return next; }) };
  const [practiceMode, setPracticeMode] = useState(null), [practiceAnswers, setPracticeAnswers] = useState({}), [practiceStep, setPracticeStep] = useState(0);
  const [recruiterDialog, setRecruiterDialog] = useState(null), [reviewed, setReviewed] = useState(false);
  const [selected, setSelected] = useState([101, 102]);
  const [tab, setTab] = useState("cv"), [filters, setFilters] = useState({}), [answers, setAnswers] = useState({}), [dirty, setDirty] = useState(false), [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ summary: data.profile.summary, experiences: [0], skills: data.profile.skills, style: "modern", includePhoto: false });
  if (practiceMode === "active") return <MemoryRouter><div className={`quality-shell role-${role}`}><ChallengeWorkspace attempt={practiceExample} seconds={441} answers={practiceAnswers} step={practiceStep} onStep={setPracticeStep} onAnswer={(id, value) => setPracticeAnswers((current) => ({ ...current, [id]: value }))} onExit={() => setPracticeMode(null)} onSubmit={() => setPracticeMode("result")} /></div></MemoryRouter>;
  if (practiceMode === "result") return <MemoryRouter><div className={`quality-shell role-${role}`}><ChallengeResult attempt={{ ...practiceExample, status: "completed", score: 100, passed: true, feedback: practiceExample.questions.map((row) => ({ question_id: row.id, prompt: row.prompt, correct: true, message: "Respuesta revisada en el ejemplo de interfaz." })) }} onExit={() => setPracticeMode(null)} onResults={() => setPracticeMode(null)} /></div></MemoryRouter>;
  return <MemoryRouter><FeedbackProvider><main className={`quality-shell role-${role}`}><p className="quality-label">Datos ficticios para comprobar componentes. Esta página no se incluye en la aplicación publicada.</p>
    <PageHeader kicker="TalentSync" title="Prepara tu próxima oportunidad" description="Comprueba filtros, tarjetas y preparación con textos largos, estados vacíos y diferentes tamaños de pantalla." actions={<button type="button" className="button-secondary">Revisar mi perfil</button>} />
    <section data-quality="challenge"><ChallengeCatalog assessments={[{ id: "example-python", title: "Fundamentos de Python", category: "technology", skill: "python", minutes: 10, context: "Dos decisiones de ejemplo para comprobar el recorrido de práctica." }]} areas={[{ id: "technology", label: "Tecnología y datos" }]} onStart={() => { setPracticeStep(0); setPracticeMode("active"); }} onReview={() => {}} onExplore={() => {}} /></section>
    <section data-quality="profile"><CandidateHero candidate={{ name: "María Alejandra Restrepo Gómez Delgado", profession: "Analista de operaciones y coordinación de inventarios", email: "candidata@example.com", location: "Medellín", department: "Antioquia", skills: [] }}><div><h2>Compatibilidad para esta vacante</h2><p>Consulta los requisitos de la oferta.</p></div></CandidateHero><LanguageSummary value={[{ name: "Inglés", level: "B1" }, { name: "Español", level: "NATIVE" }]} /></section>
    <section data-quality="filters"><LearningFilters value={filters} onChange={setFilters} resources={[resource]} resultCount={1} /></section>
    <section className="quality-course-grid" data-quality="course"><LearningResourceCard resource={resource} compact onPlan={() => {}} /><LearningResourceCard resource={{ ...resource, id: "review-long", title: "Herramientas para analizar, organizar y comunicar información de operaciones a diferentes equipos", cost: "unknown" }} compact onPlan={() => {}} /></section>
    <section data-quality="comparison"><div className="quality-vacancy-grid">{comparisonJobs.map((job) => <VacancyCard key={job.id} interests={interests} application={exampleApplications[job.id]} job={{ ...job, created_at: "2026-10-20T12:00:00Z", description: "Reconciliar el inventario y coordinar entregas con el equipo." }} comparison={{ ids: selected, toggle: (id) => setSelected((current) => toggleComparedJob(current, id)) }} match={75} showMatch />)}</div><JobComparison applications={exampleApplications} jobs={comparisonJobs} matches={{ 101: { match_percentage: 75 } }} selection={{ ids: selected, toggle: (id) => setSelected((current) => toggleComparedJob(current, id)), clear: () => setSelected([]) }} /></section>
    <section data-quality="agenda"><InterviewAgenda applications={agendaRows} now={new Date("2026-10-22T00:00:00Z")} /></section>
    <section data-quality="tracking"><ProcessWorkspace role={role} process={{ application_id: 101, job_id: 101, company_name: "Empresa de ejemplo", candidate_name: "Persona de ejemplo", status: "technical_interview", stage_title: "Entrevista técnica", response_days: 3, response_due_at: "2026-10-26T15:00:00", created_at: "2026-10-20T12:00:00", job_description: "Trabajarás con el equipo de operaciones. Responsabilidades: • Revisar los registros de inventario. • Documentar las diferencias y presentar los resultados al equipo.", job_requirements: "Experiencia relacionada con Excel y SQL.", events: [] }} evaluation={<label>Evaluación de ejemplo<textarea className="field-control" /></label>} communication={role === "company" ? <label>Mensaje de ejemplo<textarea className="field-control" /></label> : null} /></section>
    <section className="quality-recruiter-actions"><button type="button" className="button-secondary" onClick={() => setRecruiterDialog("process")}>Gestionar proceso de ejemplo</button><button type="button" className="button-secondary" onClick={() => setRecruiterDialog("answers")}>Revisar respuestas de ejemplo</button>{reviewed && <p role="status">Valoración preparada</p>}</section>
    {recruiterDialog === "process" && <RecruiterProcessDialog application={{ id: 101, candidate_name: "Candidata de ejemplo" }} onClose={() => setRecruiterDialog(null)} onDelete={() => setRecruiterDialog(null)} onSave={() => setRecruiterDialog(null)} />}
    {recruiterDialog === "answers" && <ApplicationAnswersModal application={{ id: 101, candidate_name: "Candidata de ejemplo", base_match_percentage: 70, screening_answers: [{ question_id: "example-first", question: "¿Cómo verificaste los registros de inventario?", answer: "Comparé movimientos y documenté las diferencias.", type: "open" }, { question_id: "example-second", question: "¿Cómo compartiste el resultado con el equipo?", answer: "Presenté un reporte y acordamos las correcciones.", type: "open" }] }} onClose={() => setRecruiterDialog(null)} onPrepare={() => { setReviewed(true); setRecruiterDialog(null); }} />}
    <section className="quality-preparation" data-quality="preparation">{saved && <p role="status">Respuestas guardadas</p>}<PreparationWorkspace data={data} tab={tab} onTab={setTab} form={form} onForm={setForm} answers={answers} onAnswer={(id, key, value) => { setAnswers((current) => ({ ...current, [id]: { ...current[id], [key]: value } })); setDirty(true); setSaved(false); }} questionIndex={0} onQuestion={() => {}} dirty={dirty} onSaveInterview={() => { setSaved(true); setDirty(false); }} onDownloadNotes={() => {}} onCreateVersion={() => {}} onPreview={() => {}} onDownload={() => {}} /></section>
  </main></FeedbackProvider></MemoryRouter>;
}

createRoot(document.getElementById("root")).render(<QualityPage />);
