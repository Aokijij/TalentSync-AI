export function continueBullet(value, start, end = start) {
  const before = value.slice(0, start), lineStart = before.lastIndexOf("\n") + 1;
  const line = before.slice(lineStart), bullet = line.match(/^(\s*)([•*-])\s/);
  if (!bullet) return null;
  if (!line.slice(bullet[0].length).trim() && start === end) {
    return { value: value.slice(0, lineStart) + value.slice(end), caret: lineStart };
  }
  const insert = `\n${bullet[1]}${bullet[2]} `;
  return { value: before + insert + value.slice(end), caret: start + insert.length };
}

export function bulletKeyDown(event, onChange, maxLength = 3000) {
  if (event.key !== "Enter" || event.shiftKey || event.altKey || event.ctrlKey || event.metaKey || event.nativeEvent?.isComposing) return;
  const control = event.currentTarget, next = continueBullet(control.value, control.selectionStart, control.selectionEnd);
  if (!next) return;
  event.preventDefault();
  if (next.value.length > maxLength) return;
  onChange(next.value);
  requestAnimationFrame(() => control.setSelectionRange(next.caret, next.caret));
}
