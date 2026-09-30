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

function groupedBlocks(value) {
  return textBlocks(value).reduce((groups, block) => {
    const previous = groups.at(-1);
    if (block.type === "bullet" && previous?.type === "list") {
      previous.items.push(block.text);
    } else if (block.type === "bullet") {
      groups.push({ type: "list", items: [block.text] });
    } else {
      groups.push(block);
    }
    return groups;
  }, []);
}

export function StructuredJobText({ text }) {
  const blocks = groupedBlocks(text);
  if (!blocks.length) {
    return <p className="text-sm text-[var(--muted)]">Información no disponible.</p>;
  }
  return (
    <div className="space-y-3 text-sm leading-6 text-[var(--muted)]">
      {blocks.map((block, index) =>
        block.type === "heading" ? (
          <h3 key={`${block.text}-${index}`} className="border-t border-[var(--line)] pt-3 text-sm font-bold text-[var(--ink-strong)] first:border-0 first:pt-0">
            {block.text.replace(/:$/, "")}
          </h3>
        ) : block.type === "list" ? (
          <ul key={`list-${index}`} className="space-y-1.5 border-l-2 border-[var(--accent)]/30 pl-4">
            {block.items.map((item, itemIndex) => (
              <li key={`${item}-${itemIndex}`} className="relative pl-3 before:absolute before:left-0 before:top-[0.65rem] before:h-1 before:w-1 before:rounded-full before:bg-[var(--accent)]">
                {item}
              </li>
            ))}
          </ul>
        ) : (
          <p key={`${block.text}-${index}`}>{block.text}</p>
        ),
      )}
    </div>
  );
}
