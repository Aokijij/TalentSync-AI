import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

const errors = { query_limit: "Escribe una consulta de hasta 4.000 caracteres.", result_limit: "Reduce el resultado a cien filas y dieciséis KiB.", query_rejected: "Consulta rechazada: revisa la sintaxis, usa solo lectura de las tablas indicadas y evita funciones o cálculos fuera de los límites.", unsupported_value: "Devuelve texto o números finitos; no se admiten valores binarios." };

export function SQLPractice({ onCompleted }) {
  const [challenges, setChallenges] = useState([]);
  const [attempt, setAttempt] = useState(null);
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [now, setNow] = useState(Date.now());
  useEffect(() => { api.get("/learning/practical").then(({ data }) => setChallenges(data)).catch((failure) => setError(getApiErrorMessage(failure))); }, []);
  useEffect(() => { if (attempt?.status !== "active") return; const timer = setInterval(() => setNow(Date.now()), 1000); return () => clearInterval(timer); }, [attempt]);
  async function act(action) {
    setBusy(true); setError("");
    try { await action(); } catch (failure) { setError(getApiErrorMessage(failure)); }
    finally { setBusy(false); }
  }
  const seconds = attempt?.expires_at ? Math.max(0, Math.floor((new Date(attempt.expires_at + "Z").getTime() - now) / 1000)) : 0;
  return <section id="retos-sql" className="surface-card space-y-4 p-5"><h2 className="font-bold">Retos prácticos de consultas SQL</h2>
    <p className="text-sm text-[var(--muted)]">Escribe y prueba una consulta real sobre datos ficticios. Tienes quince minutos y una entrega final por reto cada veinticuatro horas. Debes superar las tres comprobaciones. No se ejecutan programas ni se accede a la base de TalentSync.</p>
    {error && <p role="alert" className="text-sm text-[var(--error)]">{error}</p>}
    <div className="flex flex-wrap gap-3">{challenges.map((challenge) => <button className="button-secondary" key={challenge.id} disabled={busy || attempt?.status === "active" && seconds > 0 && attempt.assessment_id !== challenge.id} onClick={() => act(async () => { const { data } = await api.post(`/learning/practical/${challenge.id}/start`); if (attempt?.id !== data.id) setQuery(""); setAttempt(data); setResult(null); setNow(Date.now()); })}>{challenge.title}</button>)}</div>
    {attempt?.status === "active" && <><p className="font-semibold">{attempt.title} · {Math.floor(seconds / 60)}:{String(seconds % 60).padStart(2, "0")}</p><p className="text-sm">{attempt.prompt}</p><p className="text-xs text-[var(--muted)]">{attempt.notice}</p>
      <div className="grid gap-4 lg:grid-cols-2">{Object.entries(attempt.tables).map(([table, columns]) => <div key={table} className="overflow-x-auto"><h3 className="mb-2 font-mono text-sm font-semibold">{table}</h3><table className="w-full text-left text-xs"><thead><tr>{columns.map((column) => <th className="p-2" key={column}>{column}</th>)}</tr></thead><tbody>{attempt.sample[table].map((row, index) => <tr className="border-t border-[var(--line)]" key={index}>{row.map((value, cell) => <td className="p-2" key={cell}>{value === null ? "NULL" : value}</td>)}</tr>)}</tbody></table></div>)}</div>
      <label className="block text-sm">Tu consulta SQLite (el borrador se conserva mientras esta página siga abierta)<textarea className="field-control mt-2 min-h-48 font-mono" value={query} onChange={(event) => setQuery(event.target.value)} maxLength={4000} spellCheck={false} placeholder="SELECT ..." /></label>
      <div className="flex flex-wrap gap-3"><button className="button-secondary" disabled={busy || !query.trim() || seconds === 0} onClick={() => act(async () => setResult((await api.post(`/learning/practical/attempts/${attempt.id}/preview`, { query })).data))}>Probar con los datos visibles</button><button className="button-primary" disabled={busy || !query.trim() || seconds === 0} onClick={() => act(async () => { const { data } = await api.post(`/learning/practical/attempts/${attempt.id}/submit`, { query }); setAttempt(data); setResult(null); setQuery(""); await onCompleted(); })}>Entregar y finalizar intento</button></div>
      {seconds === 0 && <p>El intento venció. Puedes iniciar el siguiente cuando termine el periodo de espera.</p>}
      {result && (result.ok ? <div className="overflow-x-auto"><p className="mb-2 text-xs">Resultado de muestra; no es la evaluación final.</p><table className="w-full text-left text-xs"><thead><tr>{result.columns.map((column, index) => <th className="p-2" key={index}>{column}</th>)}</tr></thead><tbody>{result.rows.map((row, index) => <tr className="border-t border-[var(--line)]" key={index}>{row.map((value, cell) => <td className="break-all p-2" key={cell}>{value === null ? "NULL" : value}</td>)}</tr>)}</tbody></table>{!result.rows.length && <p className="text-sm">Sin filas.</p>}</div> : <p role="status" className="text-sm">{errors[result.error] || "No se pudo ejecutar esa consulta."}</p>)}
    </>}
    {attempt?.status === "completed" && <div role="status" className="space-y-2"><p className="font-semibold">{attempt.passed ? "Consultas SQL básicas acreditadas" : "Continúa practicando"} · {attempt.score}%</p>{attempt.feedback.map((item) => <p key={item.question_id} className="text-sm">{item.correct ? "✓" : "Revisar:"} {item.message}</p>)}</div>}
  </section>;
}
