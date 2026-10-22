import { Check, ChevronLeft, ChevronRight, Download, FileText, MessageSquare, Save, ShieldCheck } from "lucide-react";
import { InlineNotice, Panel, PanelActions, WorkspaceTabs } from "./ui/Panel.jsx";
import { starFields, reviewAnswer } from "../utils/preparation.js";
import "../styles/application-preparation.css";

const date = (value) => new Date(value.endsWith("Z") ? value : `${value}Z`).toLocaleString("es-CO", { dateStyle: "medium", timeStyle: "short" });

export function PreparationWorkspace({ data, tab, onTab, form, onForm, busy, saving, answers, onAnswer, questionIndex, onQuestion, dirty, onSaveInterview, onDownloadNotes, onCreateVersion, onPreview, onDownload, onSelect, selectedId, application = false, preview, onClosePreview }) {
  const questions = data.interview.questions;
  const question = questions[Math.min(questionIndex, questions.length - 1)];
  const answered = questions.filter((row) => reviewAnswer(answers[row.id]).complete).length;
  const currentReview = reviewAnswer(answers[question?.id]);
  const changeSelection = (key, value, checked) => onForm({ ...form, [key]: checked ? [...form[key], value] : form[key].filter((item) => item !== value) });
  return <div className="preparation-workspace">
    <div className="preparation-context"><div><span>{application ? "Tu proceso" : "Tu próxima oportunidad"}</span><h3>{data.job.title}</h3><p>{data.job.company_name}</p></div><span className="preparation-private"><ShieldCheck size={16} />Preparación privada</span></div>
    <WorkspaceTabs id="preparation" label="Preparación para la vacante" value={tab} onChange={onTab} items={[["cv", application ? "CV enviado" : "CV por vacante", FileText], ["interview", "Practicar entrevista", MessageSquare]]} />
    <div id={`preparation-panel-${tab}`} role="tabpanel" aria-labelledby={`preparation-tab-${tab}`} tabIndex={0}>
      {tab === "cv" && <div className={`preparation-cv-layout${application ? " is-submitted" : ""}`}>
        {!application && <Panel title="Destaca lo que se relaciona con el cargo" description="Elige contenido de tu perfil para esta versión. Tu perfil principal se conserva.">
          <form id="prepare-cv" onSubmit={(event) => { event.preventDefault(); onCreateVersion(); }}><fieldset disabled={busy}>
            <label className="preparation-field">Resumen para esta vacante<textarea rows={5} maxLength={3000} value={form.summary} onChange={(event) => onForm({ ...form, summary: event.target.value })} /><small>Revisa el texto e incluye únicamente hechos que puedas respaldar.</small></label>
            {!!data.profile.experiences.length && <fieldset className="preparation-selection"><legend>Experiencias que quieres incluir</legend>{data.profile.experiences.map((row, index) => <label key={index}><input type="checkbox" checked={form.experiences.includes(index)} onChange={(event) => changeSelection("experiences", index, event.target.checked)} /><span><strong>{row.role || "Experiencia"}</strong><small>{row.company}</small></span></label>)}</fieldset>}
            {!!data.profile.skills.length && <fieldset className="preparation-selection"><legend>Habilidades de tu perfil</legend><p>Las relacionadas con la vacante aparecen primero.</p><div className="preparation-skills">{data.profile.skills.map((skill) => <label key={skill}><input type="checkbox" checked={form.skills.includes(skill)} onChange={(event) => changeSelection("skills", skill, event.target.checked)} />{skill}</label>)}</div></fieldset>}
            <div className="preparation-design"><label className="preparation-field">Diseño<select value={form.style} onChange={(event) => onForm({ ...form, style: event.target.value })}><option value="modern">Moderno</option><option value="classic">Clásico</option><option value="minimal">Minimalista</option></select></label><label className="preparation-photo"><input type="checkbox" checked={form.includePhoto} onChange={(event) => onForm({ ...form, includePhoto: event.target.checked })} />Incluir mi foto si está disponible</label></div>
          </fieldset></form>
          <PanelActions><span>Formación, cursos y datos visibles se toman de tu perfil.</span><button type="submit" form="prepare-cv" className="button-primary" disabled={busy}><Save size={16} />{saving ? "Guardando…" : "Guardar versión del CV"}</button></PanelActions>
        </Panel>}
        <Panel title={application ? "Documento de esta postulación" : "Tus versiones guardadas"} description={application ? "La copia enviada permanece igual aunque después edites tu perfil." : "Abre el PDF y revisa su contenido antes de utilizarlo."}>
          {data.versions.filter((row) => !application || row.id === data.submitted_resume_id).length ? <div className="preparation-version-list">{data.versions.filter((row) => !application || row.id === data.submitted_resume_id).map((row) => <article key={row.id}><header><strong>{date(row.created_at)}</strong>{selectedId === row.id && <span><Check size={14} />Seleccionada</span>}</header><p>{row.experiences.length} experiencias · {row.skills.length} habilidades · {{ modern: "Moderno", classic: "Clásico", minimal: "Minimalista" }[row.style] || "CV"}</p><div><button type="button" className="button-secondary button-sm" disabled={busy} onClick={() => onPreview(row)}>Ver PDF</button><button type="button" className="button-secondary button-sm" disabled={busy} onClick={() => onDownload(row)}><Download size={15} />Descargar</button>{onSelect && <button type="button" className={selectedId === row.id ? "button-secondary button-sm" : "button-primary button-sm"} disabled={busy} onClick={() => onSelect(row)}>{selectedId === row.id ? "Usar perfil habitual" : "Usar al postularme"}</button>}</div></article>)}</div> : <div className="preparation-empty"><FileText size={25} /><strong>{application ? "Esta postulación se envió con tu perfil" : "Todavía no hay versiones guardadas"}</strong><p>{application ? "Puedes preparar la entrevista con la información disponible del proceso." : "Selecciona lo que quieres destacar y guarda una versión para revisar su PDF."}</p></div>}
          {!application && <p className="preparation-caption">Guardar un CV no envía una postulación. La versión seleccionada se indicará junto al botón de postularte.</p>}
        </Panel>
        {preview && <section className="preparation-pdf"><header><h4>PDF guardado · vista previa</h4><button className="button-secondary button-sm" type="button" onClick={onClosePreview}>Cerrar vista previa</button></header><iframe title="Vista previa del CV guardado para esta vacante" src={`${preview.url}#toolbar=0&navpanes=0`} /></section>}
      </div>}
      {tab === "interview" && <>
        <div className="preparation-practice-intro"><div><h3>Prepara ejemplos de tu propia experiencia</h3><p>Preguntas basadas en los requisitos de la oferta. Tus respuestas solo las puedes ver tú.</p></div><span>{answered} de {questions.length} respuestas estructuradas</span></div>
        {data.interview.outdated && <InlineNotice>La oferta o tu perfil cambiaron desde la última práctica. Conservamos tus respuestas; revísalas antes de guardar.</InlineNotice>}
        <div className="preparation-interview-layout"><Panel title={`Pregunta ${questionIndex + 1} de ${questions.length}`}>
          <div className="preparation-question"><h3>{question.title}</h3><p>{question.hint}</p>{question.skill && <span className="preparation-skill">Requisito: {question.skill}{!question.in_profile && " · no está declarado en tu perfil"}</span>}</div>
          <div className="preparation-star-grid">{starFields.map(([key, label, placeholder]) => <label key={key} className="preparation-field">{label}<textarea rows={3} maxLength={1500} value={answers[question.id]?.[key] || ""} disabled={busy} onChange={(event) => onAnswer(question.id, key, event.target.value)} placeholder={placeholder} /></label>)}</div>
          <p className="preparation-caption" role="status">{currentReview.complete ? "Tu respuesta incluye los cuatro apartados. Revisa que describa con precisión tu participación." : `Por completar: ${currentReview.missing.join(", ").toLowerCase()}.`} Esta revisión comprueba la estructura del texto.</p>
          <PanelActions><div className="preparation-question-navigation"><button className="button-secondary" type="button" disabled={questionIndex === 0 || busy} onClick={() => onQuestion(questionIndex - 1)}><ChevronLeft size={16} />Anterior</button><button className="button-secondary" type="button" disabled={questionIndex === questions.length - 1 || busy} onClick={() => onQuestion(questionIndex + 1)}>Siguiente<ChevronRight size={16} /></button></div><button type="button" className="button-primary" disabled={busy || !dirty} onClick={onSaveInterview}><Save size={16} />{saving ? "Guardando…" : "Guardar mis respuestas"}</button></PanelActions>
        </Panel><aside className="preparation-evidence"><Panel title="Recuerda tus experiencias">
          {question.experiences.length ? question.experiences.map((row, index) => <article key={index}><h4>{row.role}</h4><span>{row.company}</span><p>{row.description}</p></article>) : <p>Elige un trabajo, práctica o proyecto real. Si no tienes experiencia con el requisito, explica lo que sabes y lo que necesitas aprender.</p>}
          <p className="preparation-caption">Son extractos guardados de tu trayectoria; no se han generado logros ni respuestas por ti.</p>
        </Panel><Panel title="También puedes preguntar">{data.interview.ask_company.map((text) => <p className="preparation-company-question" key={text}>{text}</p>)}</Panel></aside></div>
        <div className="preparation-notes-footer"><span>{dirty ? "Tienes respuestas sin guardar" : data.interview.saved_at ? `Guardado ${date(data.interview.saved_at)}` : "Guarda cuando quieras continuar más tarde"}</span><button type="button" className="button-secondary" onClick={onDownloadNotes}><Download size={16} />Descargar mis notas</button></div>
      </>}
    </div>
  </div>;
}
