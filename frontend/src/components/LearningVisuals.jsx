import { BookOpen, Boxes, Factory, HardHat, Hotel, Sprout, BriefcaseBusiness, Calculator, Code2, GraduationCap, Headphones, HeartHandshake, Palette, UsersRound } from "lucide-react";

const icons = { industry: Factory, construction: HardHat, hospitality: Hotel, agriculture: Sprout, general: UsersRound, technology: Code2, service: Headphones, sales: BriefcaseBusiness, administration: BookOpen, finance: Calculator, logistics: Boxes, education: GraduationCap, design: Palette, care: HeartHandshake };
export function AreaIcon({ area, size = 22 }) { const Icon = icons[area] || BookOpen; return <Icon size={size} aria-hidden="true" />; }

export function LearningOverview({ plans, passport }) {
  const active = plans.filter((row) => row.status !== "completed").length;
  const published = passport?.practice_evidence?.length || 0;
  const validated = passport?.assessments.filter((row) => row.valid).length || 0;
  return <div className="development-overview">{[[active, "Recursos en marcha", "Avanza a tu ritmo"], [published, "Trabajos publicados", "Evidencias en tu perfil"], [validated, "Evaluaciones vigentes", "Resultados de retos vigentes"]].map(([count, label, detail]) => <div key={label}><strong>{count}</strong><span>{label}<small>{detail}</small></span></div>)}</div>;
}
