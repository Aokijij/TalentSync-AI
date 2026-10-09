import { useId, useState } from "react";
const fold = (text) => text.normalize("NFD").replace(/\p{Diacritic}/gu, "").toLowerCase();

export function Autocomplete({ label, options, value, onChange, ...props }) {
  const id = useId(), [open, setOpen] = useState(false), [active, setActive] = useState(-1);
  const matches = value.trim() ? options.filter((item) => fold(item).includes(fold(value))).slice(0, 7) : options.slice(0, 5);
  const select = (item) => { onChange(item); setOpen(false); setActive(-1); };
  return <div className="relative"><label htmlFor={id} className="block text-sm font-semibold">{label}</label>
    <input {...props} id={id} className="field-control mt-2" value={value} role="combobox" autoComplete="off" aria-autocomplete="list" aria-expanded={open && matches.length > 0} aria-controls={`${id}-list`} aria-activedescendant={active >= 0 ? `${id}-${active}` : undefined}
      onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }} onFocus={() => setOpen(true)} onBlur={() => setOpen(false)}
      onKeyDown={(event) => { if (event.key === "Escape") setOpen(false); if (matches.length && (event.key === "ArrowDown" || event.key === "ArrowUp")) { event.preventDefault(); setOpen(true); setActive((old) => (old + (event.key === "ArrowDown" ? 1 : -1) + matches.length) % matches.length); } if (event.key === "Enter" && open && active >= 0 && matches[active]) { event.preventDefault(); select(matches[active]); } }} />
    {open && matches.length > 0 && <ul id={`${id}-list`} role="listbox" className="autocomplete-list">{matches.map((item, index) => <li key={item} id={`${id}-${index}`} role="option" aria-selected={active === index} onMouseDown={(event) => { event.preventDefault(); select(item); }} className={active === index ? "selected" : ""}>{item}</li>)}</ul>}
  </div>;
}
