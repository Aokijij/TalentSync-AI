import { BookOpen, Boxes, BriefcaseBusiness, Calculator, Code2, GraduationCap, Headphones, HeartHandshake, Palette, UsersRound } from "lucide-react";

const icons = { general: UsersRound, technology: Code2, service: Headphones, sales: BriefcaseBusiness, administration: BookOpen, finance: Calculator, logistics: Boxes, education: GraduationCap, design: Palette, care: HeartHandshake };
export function AreaIcon({ area, size = 22 }) { const Icon = icons[area] || BookOpen; return <Icon size={size} aria-hidden="true" />; }

export function LearningOverview({ plans, passport }) {
  const active = plans.filter((row) => row.status !== "completed").length;
  const published = passport?.practice_evidence?.length || 0;
  const validated = passport?.assessments.filter((row) => row.valid).length || 0;
  return <div className="development-overview">{[[active, "Prácticas en marcha", "Avanza a tu ritmo"], [published, "Trabajos publicados", "Evidencias en tu perfil"], [validated, "Evaluaciones vigentes", "Fundamentos acreditados"]].map(([count, label, detail]) => <div key={label}><strong>{count}</strong><span>{label}<small>{detail}</small></span></div>)}</div>;
}
