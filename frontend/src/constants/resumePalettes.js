const palette = (id, label, accent, dark, tint, line, secondary = accent) => ({
  id,
  label,
  swatch: accent,
  variables: {
    "--resume-accent": accent,
    "--resume-dark": dark,
    "--resume-tint": tint,
    "--resume-line": line,
    "--resume-secondary": secondary,
  },
});

const forest = palette("forest", "Verde bosque", "#166534", "#12382b", "#f0fdf4", "#bbf7d0");
const wine = palette("wine", "Vino", "#881337", "#4c1025", "#fff1f2", "#fecdd3");
const slate = palette("slate", "Grafito", "#334155", "#1e293b", "#f8fafc", "#cbd5e1");
const navy = palette("navy", "Azul marino", "#1e3a8a", "#172554", "#eff6ff", "#bfdbfe");

const palettes = {
  classic: [palette("default", "Azul noche", "#0c4a6e", "#020617", "#eef6fc", "#bfdbfe", "#0369a1"), forest, wine, slate],
  modern: [
    palette("default", "Violeta", "#4338ca", "#312e81", "#eef2ff", "#c7d2fe"),
    palette("blue", "Azul", "#1d4ed8", "#172554", "#eff6ff", "#bfdbfe"),
    palette("teal", "Turquesa", "#0f766e", "#134e4a", "#f0fdfa", "#99f6e4"),
    palette("rose", "Frambuesa", "#be185d", "#500724", "#fdf2f8", "#fbcfe8"),
  ],
  minimal: [palette("default", "Grafito", "#0f172a", "#0f172a", "#f8fafc", "#cbd5e1"), navy, forest, wine],
};

export function getResumePalettes(style) {
  return palettes[style] || palettes.classic;
}

export function getResumePalette(style, color) {
  const options = getResumePalettes(style);
  return options.find((item) => item.id === color) || options[0];
}
