import { ArrowUpRight, BriefcaseBusiness, Check, Compass, ShieldCheck, UsersRound } from "lucide-react";
import { BrandLogo } from "./brand/BrandLogo.jsx";
import { ThemeToggle } from "./ThemeToggle.jsx";

export function AuthFrame({ company = false, children, registering = false }) {
  return <main className={`access-page ${company ? "role-company" : "role-candidate"}`}>
    <ThemeToggle compact className="fixed right-4 top-4 z-20" />
    <section className="access-stage">
      <aside className="access-story">
        <BrandLogo size="lg" subtitle={company ? "EMPRESAS" : "TU SIGUIENTE PASO"} tone="inverse" />
        <div className="access-story-heading"><p className="access-eyebrow">{company ? "Tu centro de contratación" : "Tu carrera, con dirección"}</p>
          <h1>{company ? "El próximo talento de tu equipo empieza aquí." : "Dale forma a tu próximo paso."}</h1>
          <p>{company ? "Un espacio propio para preparar ofertas claras, comparar talento y acompañar cada proceso." : "Descubre oportunidades, practica con un propósito y muestra lo que puedes aportar."}</p>
        </div>
        <div className="access-preview" aria-hidden="true">
          <div className="flex items-center justify-between"><span>{company ? "Vista de tu equipo" : "Tu recorrido"}</span><ArrowUpRight size={18} /></div>
          {(company ? [[BriefcaseBusiness, "Ofertas claras", "Requisitos y condiciones revisados"], [UsersRound, "Talento organizado", "Cada candidatura, en su etapa"], [ShieldCheck, "Equipo conectado", "Accesos y responsabilidades definidos"]] : [[Compass, "Encuentra tu oportunidad", "Recomendaciones con motivos claros"], [BriefcaseBusiness, "Prepárate para el cargo", "Prácticas y formación de tu área"], [Check, "Haz visible tu avance", "Resultados y evidencias en tu perfil"]]).map(([Icon, title, detail], index) => <div className="access-preview-row" key={title}><span className="access-preview-icon"><Icon size={20} /></span><div><strong>{title}</strong><small>{detail}</small></div><span className="access-preview-number">0{index + 1}</span></div>)}
        </div>
        <p className="access-story-footer">{company ? "Espacio empresarial · Acceso por rol · Verificación de organización" : "Tu perfil · Tus preferencias · Tu desarrollo"}{registering ? " · Registro guiado" : ""}</p>
      </aside>
      <div className="access-form-panel">{children}</div>
    </section>
  </main>;
}
