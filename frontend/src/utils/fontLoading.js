// A remote stylesheet must not hold up the application's first paint.
export function loadAppFont(document) {
  if (document.getElementById("talentsync-font")) return;
  const link = document.createElement("link");
  link.id = "talentsync-font";
  link.rel = "preload";
  link.as = "style";
  link.href = "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap";
  link.addEventListener("load", () => { link.rel = "stylesheet"; }, { once: true });
  document.head.append(link);
}
