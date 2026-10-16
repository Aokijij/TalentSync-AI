import { useEffect, useRef } from "react";

export function AutoResizeTextarea({ value, rows = 2, className = "", ...props }) {
  const control = useRef(null);
  useEffect(() => {
    const resize = () => { if (control.current) { control.current.style.height = "auto"; control.current.style.height = `${control.current.scrollHeight + 2}px`; } };
    resize(); window.addEventListener("resize", resize);
    return () => window.removeEventListener("resize", resize);
  }, [value]);
  return <textarea ref={control} rows={rows} className={`field-control expanding-textarea ${className}`} value={value} {...props} />;
}
