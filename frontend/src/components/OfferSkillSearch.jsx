import { useEffect, useRef, useState } from "react";
import { Search, Plus, Check } from "lucide-react";
import { api, getApiErrorMessage } from "../api/client.js";
import { skillKey } from "../utils/skillLevels.js";
import { detectedRequirements } from "../utils/offerPresentation.js";

export function OfferSkillSearch({ text, requirements, onChange }) {
  const [detected, setDetected] = useState([]), [chosen, setChosen] = useState([]), [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const request = useRef(null);
  useEffect(() => () => request.current?.abort(), []);
  useEffect(() => { request.current?.abort(); setDetected([]); setChosen([]); setMessage(""); setBusy(false); }, [text]);
  async function search() {
    request.current?.abort(); const controller = new AbortController(); request.current = controller;
    setBusy(true); setMessage("");
    try {
      const { data } = await api.post("/hiring/skills/search", { text }, { signal: controller.signal });
      if (controller.signal.aborted) return;
      const found = detectedRequirements(data, requirements);
      setDetected(found); setChosen(found.slice(0, Math.max(0, 50 - requirements.length)));
      setMessage(found.length ? "Revisa las sugerencias. Usamos la prioridad y el nivel indicados en el texto; si no se especifican, asignamos Deseable · Básico · peso 1." : "No encontramos habilidades nuevas. Puedes añadirlas manualmente.");
    } catch (error) { if (!controller.signal.aborted) setMessage(getApiErrorMessage(error)); }
    finally { if (!controller.signal.aborted) setBusy(false); }
  }
  return <div className="offer-skill-search"><button type="button" className="offer-detect-action" disabled={busy || text.trim().length < 3} onClick={search}><Search size={16} />{busy ? "Buscando…" : "Detectar habilidades del texto"}</button>{message && <p role="status">{message}</p>}{!!detected.length && <><div className="offer-detected-skills">{detected.map((item) => <button type="button" key={item.skill} aria-pressed={chosen.includes(item)} onClick={() => setChosen((current) => current.includes(item) ? current.filter((skill) => skill !== item) : current.length < 50 - requirements.length ? [...current, item] : current)}>{chosen.includes(item) && <Check size={13} />}{item.skill} · {item.essential ? "Esencial" : "Deseable"} · {({ basic: "Básico", intermediate: "Intermedio", advanced: "Avanzado", expert: "Experto" })[item.level]}</button>)}</div><button className="button-primary button-sm" type="button" disabled={!chosen.length} onClick={() => { const existing = new Set(requirements.map((row) => skillKey(row.skill))); const additions = chosen.filter((item) => !existing.has(skillKey(item.skill))).slice(0, Math.max(0, 50 - requirements.length)); onChange([...requirements, ...additions]); setDetected([]); setChosen([]); setMessage(`${additions.length} habilidades añadidas. Revisa los niveles y prioridades.`); }}><Plus size={14} />Añadir seleccionadas ({chosen.length})</button></>}</div>;
}
