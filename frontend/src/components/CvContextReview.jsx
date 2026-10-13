const labels = { learning: "Aprendizaje indicado explícitamente", negated: "Falta de experiencia indicada", project: "Mencionada en proyectos", training: "Mencionada en formación", unknown: "Contexto por confirmar" };

export function CvContextReview({ rows = [], skills = [] }) {
  const declared = new Set(skills.map((skill) => skill.toLocaleLowerCase()));
  const review = rows.filter((row) => labels[row.state] && !declared.has(row.skill.toLocaleLowerCase()));
  if (!review.length) return null;
  return <details className="cv-context-review"><summary>Menciones del CV para confirmar ({review.length})</summary>
    <p>El contexto del documento no demuestra dominio. «En formación» no significa que estés aprendiendo actualmente.</p>
    {review.map((row, index) => <div key={`${row.skill}-${index}`}><strong>{row.skill} · {labels[row.state]}</strong><p>{row.reason || "Revisa la mención antes de incorporarla a tu perfil."}</p><blockquote>{row.excerpt}</blockquote>{row.cue && <small>Expresión detectada: «{row.cue}»</small>}</div>)}
  </details>;
}
