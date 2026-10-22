import { useState } from "react";
import { createRoot } from "react-dom/client";
import { MemoryRouter } from "react-router-dom";
import { PageHeader } from "../src/components/PageHeader.jsx";
import { CandidateHero } from "../src/components/CandidateHero.jsx";
import { LanguageSummary } from "../src/components/LanguageSummary.jsx";
import { LearningFilters } from "../src/components/LearningFilters.jsx";
import { LearningResourceCard } from "../src/components/LearningResourceCard.jsx";
import { PreparationWorkspace } from "../src/components/PreparationWorkspace.jsx";
import "../src/styles/index.css";
import "./quality.css";

const params = new URLSearchParams(window.location.search);
document.documentElement.dataset.theme = params.get("theme") || "light";
const role = ["candidate", "company", "admin"].includes(params.get("role")) ? params.get("role") : "candidate";
const experiences = [{ role: "Analista de inventario y reportes", company: "Equipo de distribución", description: "Organicé los registros y preparé reportes en Excel para el equipo.", start_date: "2021-01", end_date: "2023-01" }];
const questions = [{ id: "introduction", title: "¿Qué parte de tu trayectoria se relaciona con este cargo?", hint: "Describe una experiencia real y tu participación.", experiences }];
const data = { job: { title: "Analista de operaciones · inventarios y coordinación de entregas", company_name: "Equipo de distribución" }, profile: { summary: experiences[0].description, experiences, skills: ["excel", "logística", "gestión de inventarios"] }, versions: [], interview: { questions, ask_company: ["¿Qué resultados esperan en los primeros tres meses?"], answers: {}, version: 0 } };
const resource = { id: "review-excel", title: "Prepara reportes de inventario con Excel y tablas dinámicas", provider: "Formación de ejemplo para revisión", category: "business", skills: ["excel", "gestión de inventarios"], targeted_skills: ["excel"], hours: 12, cost: "free", active: true };

function QualityPage() {
  const [tab, setTab] = useState("cv"), [filters, setFilters] = useState({}), [answers, setAnswers] = useState({}), [dirty, setDirty] = useState(false), [saved, setSaved] = useState(false);
  const [form, setForm] = useState({ summary: data.profile.summary, experiences: [0], skills: data.profile.skills, style: "modern", includePhoto: false });
  return <MemoryRouter><main className={`quality-shell role-${role}`}><p className="quality-label">Datos ficticios para comprobar componentes. Esta página no se incluye en la aplicación publicada.</p>
    <PageHeader kicker="TalentSync" title="Prepara tu próxima oportunidad" description="Comprueba filtros, tarjetas y preparación con textos largos, estados vacíos y diferentes tamaños de pantalla." actions={<button type="button" className="button-secondary">Revisar mi perfil</button>} />
    <section data-quality="profile"><CandidateHero candidate={{ name: "María Alejandra Restrepo Gómez Delgado", profession: "Analista de operaciones y coordinación de inventarios", email: "candidata@example.com", location: "Medellín", department: "Antioquia", skills: [] }}><div><h2>Compatibilidad para esta vacante</h2><p>Consulta los requisitos de la oferta.</p></div></CandidateHero><LanguageSummary value={[{ name: "Inglés", level: "B1" }, { name: "Español", level: "NATIVE" }]} /></section>
    <section data-quality="filters"><LearningFilters value={filters} onChange={setFilters} resources={[resource]} resultCount={1} /></section>
    <section className="quality-course-grid" data-quality="course"><LearningResourceCard resource={resource} compact onPlan={() => {}} /><LearningResourceCard resource={{ ...resource, id: "review-long", title: "Herramientas para analizar, organizar y comunicar información de operaciones a diferentes equipos", cost: "unknown" }} compact onPlan={() => {}} /></section>
    <section className="quality-preparation" data-quality="preparation">{saved && <p role="status">Respuestas guardadas</p>}<PreparationWorkspace data={data} tab={tab} onTab={setTab} form={form} onForm={setForm} answers={answers} onAnswer={(id, key, value) => { setAnswers((current) => ({ ...current, [id]: { ...current[id], [key]: value } })); setDirty(true); setSaved(false); }} questionIndex={0} onQuestion={() => {}} dirty={dirty} onSaveInterview={() => { setSaved(true); setDirty(false); }} onDownloadNotes={() => {}} onCreateVersion={() => {}} onPreview={() => {}} onDownload={() => {}} /></section>
  </main></MemoryRouter>;
}

createRoot(document.getElementById("root")).render(<QualityPage />);
