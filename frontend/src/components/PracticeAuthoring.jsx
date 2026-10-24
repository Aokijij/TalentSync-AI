import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";
import "../styles/learning-revision.css";

export function PracticeAuthoring({ value, onChange }) {
  const [templates, setTemplates] = useState([]), [error, setError] = useState(""), [revision, setRevision] = useState(0);
  const [preview, setPreview] = useState(null);
  useEffect(() => {
    setPreview(null);
    if (value.mode !== "template" || !value.template_id) return;
    let active = true;
    api.get(`/admin/learning/practice-templates/${value.template_id}`, { params: { level: value.level } }).then(({ data }) => { if (active) setPreview(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [value.mode, value.template_id, value.level, revision]);
  useEffect(() => {
    if (value.mode !== "template") return;
    let active = true; setError("");
    api.get("/admin/learning/practice-templates").then(({ data }) => { if (active) setTemplates(data); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [value.mode, revision]);
  const change = (key, next) => onChange({ ...value, [key]: next });
  const text = (key, label, { min = 10, max = 800, help, placeholder } = {}) => <label>{label}<textarea className="field-control" required minLength={min} maxLength={max} value={value[key]} onChange={(event) => change(key, event.target.value)} placeholder={placeholder || "Describe el contenido que debe trabajar el candidato"} />{help && <small>{help}</small>}</label>;
  return <section className="practice-authoring sm:col-span-2" aria-label="Asociación de práctica"><header><h3>Práctica de TalentSync asociada al curso</h3><p>Revisa el temario antes de asociar una actividad. La práctica y el certificado del proveedor son independientes.</p></header>
    <label>Relación con la práctica<select className="field-control" value={value.mode} onChange={(event) => change("mode", event.target.value)}><option value="none">Sin práctica asociada</option><option value="template">Asociar una práctica del catálogo</option><option value="custom">Redactar una práctica para este temario</option></select></label>
    {value.mode !== "none" && <div className="practice-authoring-grid"><div className="wide">{text("rationale", "Cómo se relaciona con el temario", { min: 20, max: 600, placeholder: "Explica qué contenidos del curso refuerza y qué queda fuera" })}</div>
      {value.mode === "template" ? <><label>Práctica que has revisado<select className="field-control" required value={value.template_id} onChange={(event) => change("template_id", event.target.value)}><option value="">Elige el tema correspondiente</option>{templates.map((row) => <option key={row.id} value={row.id}>{row.title}</option>)}</select></label><label>Nivel de la práctica<select className="field-control" value={value.level} onChange={(event) => change("level", event.target.value)}><option value="beginner">Inicial</option><option value="intermediate">Intermedio</option><option value="advanced">Avanzado</option></select></label><p className="wide">La plantilla incluye organización de un caso, cálculo y relación de conceptos. Selecciónala solo si esas actividades corresponden al aprendizaje que quieres reforzar.</p>{error && <div className="wide" role="alert">{error}<button type="button" className="button-secondary button-sm ml-3" onClick={() => setRevision((current) => current + 1)}>Reintentar plantillas</button></div>}</> : <>
        <label className="wide">Título de la práctica<input className="field-control" required minLength={5} maxLength={160} value={value.title} onChange={(event) => change("title", event.target.value)} placeholder="Indica la actividad que se va a resolver" /></label><div className="wide">{text("scenario", "Caso y datos para resolverlo", { min: 20, max: 1500, placeholder: "Presenta un caso ficticio con los datos y criterios necesarios" })}</div>
        <div className="wide practice-authoring-step"><h4>Actividad 1 · Ordenar un procedimiento</h4>{text("steps", "Pasos en el orden correcto", { min: 8, max: 2400, placeholder: "Escribe entre 3 y 8 pasos, uno por línea", help: "Se mostrarán desordenados al candidato. Cada paso debe tener entre 2 y 300 caracteres." })}</div>
        <div className="wide practice-authoring-step"><h4>Actividad 2 · Resolver un cálculo</h4>{text("calculation_prompt", "Pregunta del cálculo", { placeholder: "Incluye todos los datos, la unidad y qué se debe calcular" })}</div><label>Respuesta numérica correcta<input className="field-control" required type="number" step="any" min={-1e9} max={1e9} value={value.calculation_answer} onChange={(event) => change("calculation_answer", event.target.value)} placeholder="Indica el resultado numérico esperado" /></label>{text("calculation_feedback", "Explicación de la solución", { placeholder: "Explica las operaciones y el resultado correcto" })}
        <div className="wide practice-authoring-step"><h4>Actividad 3 · Relacionar conceptos</h4><p>Escribe entre 3 y 8 pares. Cada línea de conceptos corresponde a la misma línea de definiciones.</p></div>{text("terms", "Conceptos, uno por línea", { min: 8, max: 2400, placeholder: "Escribe los conceptos que se van a relacionar" })}{text("meanings", "Definiciones correspondientes", { min: 8, max: 2400, placeholder: "Escribe una definición por concepto, en el mismo orden" })}
      </>}
    </div>}
    {preview && value.mode === "template" && <details className="practice-authoring-step"><summary>Revisar actividades y soluciones de la plantilla</summary>{preview.activities.map((item) => <article className="mt-4 text-sm" key={item.id}><h4 className="font-bold">{item.prompt}</h4><p>{item.type === "number" ? `Respuesta: ${item.answer}` : item.type === "order" ? item.answer.map((index) => item.choices[index]).join(" → ") : item.terms.map((term, index) => `${term}: ${item.choices[item.answer[index]]}`).join(" · ")}</p><small>{item.feedback}</small></article>)}</details>}
    <p className="mt-4">Las soluciones son privadas de administración. Los planes nuevos usarán esta asociación; los intentos existentes conservan sus actividades.</p>
  </section>;
}
