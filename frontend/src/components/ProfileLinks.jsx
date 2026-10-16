import { useId } from "react";
import { ExternalLink, Github, Globe, Linkedin, Link2, Plus, Trash2 } from "lucide-react";
import { linkPlatforms, normalizeProfessionalUrl, profileLinksPayload } from "../utils/profileLinks.js";
import "../styles/profile-links.css";

export function ProfileLinks({ value = [], editing = false, onChange, onEdit }) {
  const helpId = useId();
  function update(index, changes) { onChange(value.map((row, current) => current === index ? { ...row, ...changes } : row)); }
  if (!editing) {
    const visible = value.flatMap((row) => { try { return profileLinksPayload([row]); } catch { return []; } });
    return <div className="profile-links">
      {visible.length ? <div className="profile-links-list">{visible.map((row) => {
        const platform = linkPlatforms.find((item) => item.value === row.platform);
        const Icon = row.platform === "github" ? Github : row.platform === "linkedin" ? Linkedin : Globe;
        return <a key={row.url} href={row.url} target="_blank" rel="noopener noreferrer" className="profile-link"><span className="profile-link-icon"><Icon size={19} aria-hidden="true" /></span><span><strong>{row.label || platform.label}</strong><small>{row.url.replace(/^https?:\/\/(www\.)?/, "").replace(/\/$/, "")}</small></span><ExternalLink size={15} aria-hidden="true" /><span className="sr-only"> (abre en otra pestaña)</span></a>;
      })}</div> : <p className="profile-links-help">Comparte tu LinkedIn, GitHub, portafolio u otros espacios donde muestras tu trabajo.</p>}
      {!visible.length && onEdit && <button type="button" className="button-secondary button-sm" onClick={onEdit}><Plus size={16} />Añadir enlace</button>}
    </div>;
  }
  return <div className="profile-links">
    <p id={helpId} className="profile-links-help">Añade hasta 10 enlaces. Se guardan al pulsar «Guardar cambios» y se incluyen con tus datos de contacto al exportar la hoja de vida.</p>
    <div className="profile-links-fields">{value.map((row, index) => {
      const platform = linkPlatforms.find((item) => item.value === row.platform) || linkPlatforms[0];
      return <fieldset key={index} className="profile-link-editor"><legend><Link2 size={14} />Enlace {index + 1}</legend><button type="button" className="profile-link-remove" aria-label={`Eliminar enlace ${index + 1}`} onClick={() => onChange(value.filter((_, current) => current !== index))}><Trash2 size={16} /></button>
        <label>Plataforma<select className="field-control" value={row.platform} onChange={(event) => update(index, { platform: event.target.value, label: "" })}>{linkPlatforms.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
        <label>Enlace<input className="field-control" type="url" required maxLength={500} value={row.url} placeholder={platform.placeholder} aria-describedby={helpId} onChange={(event) => update(index, { url: event.target.value })} onBlur={(event) => update(index, { url: normalizeProfessionalUrl(event.target.value) })} /></label>
        {["other", "portfolio"].includes(row.platform) && <label>Nombre del enlace <span className="profile-links-help">(opcional)</span><input className="field-control" maxLength={60} value={row.label || ""} placeholder="Ej.: Mi sitio web" onChange={(event) => update(index, { label: event.target.value })} /></label>}
      </fieldset>;
    })}</div>
    <button type="button" className="button-secondary button-sm" disabled={value.length >= 10} onClick={() => onChange([...value, { platform: value.length ? "portfolio" : "linkedin", url: "", label: "" }])}><Plus size={16} />Añadir enlace</button>
  </div>;
}
