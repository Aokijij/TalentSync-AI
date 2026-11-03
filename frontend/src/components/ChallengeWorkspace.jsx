import { useEffect, useRef } from "react";
import { ArrowLeft, ArrowRight, Check, CheckCircle2, CircleHelp, Clock3, Flag, Send } from "lucide-react";
import { ActivityInput, activityComplete, describeAnswer } from "./ActivityInput.jsx";
import { questionInstruction } from "../utils/practiceSession.js";
import "../styles/challenge-workspace.css";
import "../styles/learning-paths.css";
import { challengeLevels } from "../utils/challengeCatalog.js";

export function ChallengeWorkspace({ attempt, answers, step, onStep, onAnswer, seconds, busy = false, error = "", warning = "", onExit, onSubmit }) {
  const heading = useRef(null);
  const questions = attempt.questions || [];
  const reviewing = step >= questions.length;
  const question = questions[step];
  const answered = questions.filter((row) => activityComplete(row, answers[row.id])).length;
  const expired = seconds === 0;
  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0, behavior: "auto" });
  }, [step, attempt.id]);
  return <section className="challenge-session" aria-label="Espacio de práctica">
    <header className="challenge-session-top"><button type="button" className="button-secondary button-sm" disabled={busy} onClick={onExit}><ArrowLeft size={16} />Salir y conservar respuestas</button><span className={`challenge-timer${seconds <= 120 ? " is-urgent" : ""}`} role="timer" aria-label="Tiempo restante"><Clock3 size={17} /><strong>{Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</strong><span>restantes</span></span></header>
    <div className="challenge-session-title"><p className="section-kicker">RETO DE {attempt.skill} · {challengeLevels[attempt.level] || "Fundamentos"}</p><h1>{attempt.title || "Practica una habilidad"}</h1><p>Avanza a tu ritmo dentro del tiempo disponible. Puedes cambiar tus respuestas antes de entregar.</p></div>
    {error && <p className="challenge-session-notice is-error" role="alert">{error} Tus respuestas siguen disponibles.</p>}
    {warning && <p className="challenge-session-notice" role="alert">{warning}</p>}
    {expired && <p className="challenge-session-notice" role="status">El tiempo de este intento terminó. Puedes revisar tus respuestas y volver al catálogo para consultar cuándo repetir.</p>}
    <div className="challenge-session-layout"><aside className="challenge-stepper"><div><strong>Tu progreso</strong><span>{answered} de {questions.length} respondidas</span></div><progress aria-label="Preguntas respondidas" max={questions.length || 1} value={answered} /><nav aria-label="Preguntas de la práctica">{questions.map((row, index) => {
      const complete = activityComplete(row, answers[row.id]);
      return <button key={row.id} type="button" className={complete ? "is-answered" : ""} aria-current={step === index ? "step" : undefined} aria-label={`Pregunta ${index + 1}: ${complete ? "respondida" : "pendiente"}`} disabled={busy} onClick={() => onStep(index)}><span>{complete ? <Check size={14} /> : index + 1}</span><span>Pregunta {index + 1}</span>{step === index && <span className="sr-only">Actual</span>}</button>;
    })}<button type="button" className="challenge-review-step" aria-current={reviewing ? "step" : undefined} disabled={busy} onClick={() => onStep(questions.length)}><Flag size={17} />Revisar y entregar</button></nav><p>{warning ? "El navegador no pudo conservar el borrador." : "Borrador conservado en esta pestaña."} Al salir, el tiempo sigue corriendo.</p></aside>
    <section className="challenge-question-card">
      <header><span>{reviewing ? "ANTES DE TERMINAR" : `PREGUNTA ${step + 1} DE ${questions.length}`}</span>{!reviewing && <small>{questionInstruction(question?.type)}</small>}</header>
      <div className="challenge-question-content">{reviewing ? <><h2 ref={heading} tabIndex={-1}>Revisa tus respuestas</h2><p className="challenge-question-intro">{answered === questions.length ? "Todo está respondido. Revisa lo que necesites antes de entregar." : questions.length - answered === 1 ? "Te falta 1 pregunta. Puedes abrirla desde esta lista." : `Te faltan ${questions.length - answered} preguntas. Puedes abrirlas desde esta lista.`}</p><ol className="challenge-review-list">{questions.map((row, index) => {
        const complete = activityComplete(row, answers[row.id]);
        return <li key={row.id}><span className={complete ? "is-complete" : ""}>{complete ? <CheckCircle2 size={18} /> : <CircleHelp size={18} />}</span><div><h3>{index + 1}. {row.prompt}</h3>{row.context && <p className="challenge-case-context">{row.context}</p>}<p>{describeAnswer(row, answers[row.id])}</p></div><button type="button" className="button-secondary button-sm" disabled={busy} onClick={() => onStep(index)}>{complete ? "Editar" : "Responder"}<span className="sr-only"> pregunta {index + 1}</span></button></li>;
      })}</ol></> : question ? <><h2 ref={heading} tabIndex={-1}>{question.prompt}</h2>{question.context && <p className="challenge-case-context">{question.context}</p>}<ActivityInput key={question.id} item={question} value={answers[question.id]} presentation="practice" disabled={busy || expired} onChange={(value) => onAnswer(question.id, value)} /></> : <h2 ref={heading} tabIndex={-1}>No hay preguntas disponibles para este intento.</h2>}</div>
      <footer className="challenge-session-actions"><button type="button" className="button-secondary" disabled={busy || step === 0} onClick={() => onStep(Math.max(0, step - 1))}><ArrowLeft size={16} />Anterior</button>{reviewing ? <button type="button" className="button-primary" disabled={busy || expired || !questions.length || answered !== questions.length} onClick={onSubmit}><Send size={16} />{busy ? "Entregando…" : "Entregar respuestas"}</button> : <button type="button" className="button-primary" disabled={busy || !question || !activityComplete(question, answers[question.id])} onClick={() => onStep(step + 1)}>{step === questions.length - 1 ? "Revisar respuestas" : "Continuar"}<ArrowRight size={16} /></button>}</footer>
    </section></div>
  </section>;
}

export function ChallengeResult({ attempt, error, onExit, onResults, children }) {
  const heading = useRef(null);
  useEffect(() => { heading.current?.focus({ preventScroll: true }); window.scrollTo({ top: 0, behavior: "auto" }); }, [attempt.id]);
  const feedback = attempt.feedback || [], correct = feedback.filter((row) => row.correct).length;
  return <section className="challenge-session challenge-result" aria-label="Resultado de la práctica"><header className="challenge-session-top"><button type="button" className="button-secondary button-sm" onClick={onExit}><ArrowLeft size={16} />Volver a los retos</button><span>Práctica finalizada</span></header>
    <section className="challenge-result-summary"><span className="challenge-result-icon"><CheckCircle2 size={28} /></span><div><p className="section-kicker">{attempt.title || attempt.skill}</p><h1 ref={heading} tabIndex={-1}>{attempt.passed ? attempt.level && attempt.level !== "fundamentals" ? `Reto ${challengeLevels[attempt.level]?.toLowerCase()} aprobado` : "Fundamentos aprobados" : "Ya sabes qué reforzar"}</h1><p>{feedback.length ? `${correct} de ${feedback.length} respuestas correctas. Revisa las explicaciones para preparar tu próximo intento.` : "Resultado guardado. Este intento no incluye correcciones detalladas."}</p></div><strong>{attempt.score}<small>%</small></strong></section>
    {error && <p className="challenge-session-notice is-error" role="alert">{error}</p>}
    {!!attempt.topic_results?.length && <section className="challenge-topic-results" aria-label="Resultado por contenido">{attempt.topic_results.map((row) => <article key={row.topic}><h3>{row.topic}</h3><p>{row.correct} de {row.total} respuestas correctas</p><progress max={row.total} value={row.correct} aria-label={row.topic} /></article>)}</section>}<section className="challenge-result-feedback"><h2>Corrección de tus respuestas</h2>{feedback.map((row, index) => <details key={row.question_id} open={!row.correct}><summary>{row.correct ? <CheckCircle2 size={18} /> : <CircleHelp size={18} />}<span>{row.prompt || `Pregunta ${index + 1}`}</span><strong>{row.correct ? "Correcta" : "Por reforzar"}</strong></summary>{row.context && <p className="challenge-case-context">{row.context}</p>}<p>{row.message}</p></details>)}</section>
    {children}<footer className="challenge-result-actions"><button type="button" className="button-secondary" onClick={onExit}>Explorar otros retos</button><button type="button" className="button-primary" onClick={onResults}>Ver mis resultados<ArrowRight size={16} /></button></footer><p className="challenge-result-scope">Este resultado corresponde al nivel y a las tareas de este reto; no sustituye una certificación profesional ni acredita experiencia laboral.</p>
  </section>;
}
