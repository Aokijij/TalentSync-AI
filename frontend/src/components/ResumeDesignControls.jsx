import { useState } from "react";
import { Check, Camera, UserRound } from "lucide-react";
import { AuthenticatedImage } from "./AuthenticatedImage.jsx";
import { getResumePalettes } from "../constants/resumePalettes.js";

const designs = [["classic", "Clásico", "Una columna · Estilo ejecutivo"], ["modern", "Moderno", "Foto circular · Columna de color"], ["minimal", "Minimalista", "Una columna · Nombre en serif"]];
export function ResumeDesignControls({ profile, photoVersion, style, color, onStyle, onColor, onPhoto }) {
  const [uploading, setUploading] = useState(false), [photoMessage, setPhotoMessage] = useState("");
  async function changePhoto(event) {
    if (!event.target.files?.[0]) return;
    setUploading(true); setPhotoMessage("");
    try { const saved = await onPhoto(event); setPhotoMessage(saved ? "Foto guardada en tu perfil." : "No pudimos guardar la foto. Revisa el formato y vuelve a intentarlo."); }
    finally { setUploading(false); event.target.value = ""; }
  }
  return <div className="resume-design-controls">
    <div className="resume-photo-control"><div className="resume-photo-sample">{profile.photo_url ? <AuthenticatedImage src={`${profile.photo_url}?v=${photoVersion}`} alt="Tu foto para la hoja de vida" fallback={<UserRound size={30} />} /> : <UserRound size={30} />}</div><div><strong>Tu foto</strong><small>Encuadre centrado · Se guarda en tu perfil</small><label className="button-secondary button-sm"><Camera size={15} />{uploading ? "Guardando…" : profile.photo_url ? "Cambiar foto" : "Añadir foto"}<input type="file" className="sr-only" disabled={uploading} accept="image/jpeg,image/png,image/webp" onChange={changePhoto} /></label>{photoMessage && <small role="status">{photoMessage}</small>}</div></div>
    <fieldset className="resume-design-picker"><legend>Diseño del documento</legend>{designs.map(([key, label, description]) => <button type="button" aria-pressed={style === key} key={key} onClick={() => onStyle(key)}><span className={`resume-design-thumbnail thumbnail-${key}`} aria-hidden="true"><i /><b /><em /><em /><em /></span><span><strong>{label}</strong><small>{description}</small></span><Check className={style === key ? "selected-check" : "unselected-check"} size={18} /></button>)}</fieldset>
    <fieldset className="resume-color-picker"><legend>Color de acento</legend><div>{getResumePalettes(style).map((palette) => <button key={palette.id} type="button" aria-label={`Color ${palette.label}`} title={palette.label} aria-pressed={color === palette.id} onClick={() => onColor(palette.id)}><span style={{ background: palette.swatch }}>{color === palette.id && <Check size={16} />}</span><small>{palette.label}</small></button>)}</div></fieldset>
  </div>;
}
