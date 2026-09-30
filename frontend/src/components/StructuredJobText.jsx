const headings = /^(requisitos|responsabilidades|funciones|perfil requerido|qué necesitas|que necesitas|condiciones|competencias|beneficios|conocimientos)(?:\s*:)?$/i;

function textBlocks(value) {
  const normalized = String(value || "")
    .replace(/\?\?+/g, "\n")
    .replace(/\s+[•*]\s+/g, "\n• ")
    .replace(/\s+-\s*(requerimientos|requisitos|responsabilidades|funciones|competencias)\s*-\s*/gi, "\n$1\n")
    .replace(/\s+(?=(?:Requisitos|Responsabilidades|Funciones|Perfil requerido|Condiciones|Competencias):)/g, "\n")
    .split(/\n+/)
    .map((item) => item.trim())
    .filter(Boolean);

  const blocks = [];
  for (const item of normalized) {
    const clean = item.replace(/^[-•*]\s*/, "").trim();
    if (!clean) continue;
    blocks.push({
      type: headings.test(clean) ? "heading" : item.match(/^[-•*]/) ? "bullet" : "paragraph",
      text: clean,
    });
  }
  return blocks;
}

export function StructuredJobText({ text }) {
  const blocks = textBlocks(text);
  if (!blocks.length) {
    return <p className="text-sm text-[var(--muted)]">Información no disponible.</p>;
  }
  return (
    <div className="space-y-3 text-sm leading-7 text-[var(--muted)]">
      {blocks.map((block, index) =>
        block.type === "heading" ? (
          <h3 key={`${block.text}-${index}`} className="pt-2 text-base font-bold text-[var(--ink-strong)]">
            {block.text.replace(/:$/, "")}
          </h3>
        ) : block.type === "bullet" ? (
          <div key={`${block.text}-${index}`} className="flex gap-3 rounded-xl bg-[var(--surface-subtle)] px-3 py-2.5">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--accent)]" />
            <p>{block.text}</p>
          </div>
        ) : (
          <p key={`${block.text}-${index}`}>{block.text}</p>
        ),
      )}
    </div>
  );
}
