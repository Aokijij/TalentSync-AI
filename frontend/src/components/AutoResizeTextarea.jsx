import { useEffect, useLayoutEffect, useRef } from "react";
import { resizeTextarea } from "../utils/textareaSizing.js";

export function AutoResizeTextarea({ value, rows = 2, className = "", ...props }) {
  const control = useRef(null);
  useLayoutEffect(() => { resizeTextarea(control.current); }, [value]);
  useEffect(() => {
    let active = true, width = -1;
    const resize = () => { if (active) resizeTextarea(control.current); };
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(([entry]) => {
      if (entry && entry.contentRect.width !== width) { width = entry.contentRect.width; resize(); }
    });
    if (control.current?.parentElement) observer?.observe(control.current.parentElement);
    window.addEventListener("resize", resize);
    document.fonts?.ready.then(resize);
    return () => { active = false; observer?.disconnect(); window.removeEventListener("resize", resize); };
  }, []);
  return <textarea ref={control} rows={rows} className={`field-control expanding-textarea ${className}`} value={value} {...props} onInput={(event) => resizeTextarea(event.currentTarget)} />;
}
