export function resizeTextarea(element) {
  if (!element || !element.getClientRects().length) return;
  element.style.height = "auto";
  const borders = element.offsetHeight - element.clientHeight;
  element.style.height = `${Math.ceil(element.scrollHeight + borders)}px`;
}
