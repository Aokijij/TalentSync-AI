import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ArrowLeft, ArrowRight, BookOpen, CalendarDays, ClipboardCheck, FileText, HelpCircle, ListChecks, Radar, Search, ShieldCheck, UserRound, UsersRound } from "lucide-react";
import { guideForRole } from "../constants/platformGuide.js";
import "../styles/platform-guide.css";

const icons = { profile: UserRound, search: Search, file: FileText, calendar: CalendarDays, book: BookOpen, results: ClipboardCheck, radar: Radar, shield: ShieldCheck, people: UsersRound, process: ListChecks };
export function PlatformGuide({ role = "candidate", memberRole = "owner", onNavigate, compact = false }) {
  const chapters = guideForRole(role, memberRole);
  const [topic, setTopic] = useState(chapters[0]?.id);
  const index = Math.max(0, chapters.findIndex((row) => row.id === topic)), current = chapters[index];
  useEffect(() => { if (!chapters.some((row) => row.id === topic)) setTopic(chapters[0]?.id); }, [role, memberRole, topic]);
  if (!current) return null;
  const Icon = icons[current.icon] || HelpCircle;
  return <section className={`platform-guide ${compact ? "is-compact" : ""}`} aria-label="Guía de uso de TalentSync"><header className="platform-guide-heading"><div><p className="section-kicker">CONOCE TU ESPACIO</p><h2>Cómo usar TalentSync</h2><p>Recorre las funciones por tema. Puedes abrir cada sección, volver a esta guía y continuar cuando quieras.</p></div>{compact && (onNavigate ? <button type="button" className="button-secondary button-sm" onClick={() => onNavigate("/guia")}>Abrir guía completa<ArrowRight size={15} /></button> : <Link className="button-secondary button-sm" to="/guia">Abrir guía completa<ArrowRight size={15} /></Link>)}</header>
    <div className="platform-guide-layout"><nav aria-label="Temas de la guía">{chapters.map((chapter, position) => { const ChapterIcon = icons[chapter.icon] || HelpCircle; return <button key={chapter.id} type="button" aria-current={chapter.id === current.id ? "step" : undefined} onClick={() => setTopic(chapter.id)}><ChapterIcon size={18} /><span>{chapter.title}</span><small>{position + 1}</small></button>; })}</nav>
      <article className="platform-guide-content" aria-live="polite"><header><span className="learning-area-icon"><Icon size={24} /></span><div><p>Tema {index + 1} de {chapters.length} · {current.where}</p><h3>{current.title}</h3></div></header><p className="platform-guide-summary">{current.summary}</p><ol>{current.steps.map((step, position) => <li key={step}><span>{position + 1}</span><p>{step}</p></li>)}</ol><aside><strong>Ten presente</strong><p>{current.note}</p></aside><footer>{onNavigate ? <button className="button-primary" type="button" onClick={() => onNavigate(current.to)}>{current.action}<ArrowRight size={16} /></button> : <Link className="button-primary" to={current.to}>{current.action}<ArrowRight size={16} /></Link>}<div><button className="button-secondary button-sm" type="button" disabled={index === 0} onClick={() => setTopic(chapters[index - 1].id)}><ArrowLeft size={15} />Anterior</button><button className="button-secondary button-sm" type="button" disabled={index === chapters.length - 1} onClick={() => setTopic(chapters[index + 1].id)}>Siguiente tema<ArrowRight size={15} /></button></div></footer></article>
    </div>
  </section>;
}
