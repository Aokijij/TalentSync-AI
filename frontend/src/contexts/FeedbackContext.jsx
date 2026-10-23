import { useLocation } from "react-router-dom";
import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";
import { ConfirmModal } from "../components/ConfirmModal.jsx";
import "../styles/feedback.css";

const roleScope = () => ["role-candidate", "role-company", "role-admin"].find((role) => document.activeElement?.closest(`.${role}`) || document.querySelector(`main.${role}, main .${role}`)) || (["candidate", "company", "admin"].includes(document.documentElement.dataset.role) ? `role-${document.documentElement.dataset.role}` : "role-candidate");
const FeedbackContext = createContext(null);
export const useFeedback = () => useContext(FeedbackContext);

function FeedbackToast({ notice, onDismiss }) {
  const [paused, setPaused] = useState(false);
  const remaining = useRef(notice.duration ?? (notice.tone === "error" ? 0 : 6500));
  useEffect(() => {
    if (paused || remaining.current <= 0) return;
    const start = Date.now(), timer = setTimeout(() => onDismiss(notice.id), remaining.current);
    return () => { clearTimeout(timer); remaining.current = Math.max(1, remaining.current - (Date.now() - start)); };
  }, [paused, notice.id, onDismiss]);
  const Icon = { success: CheckCircle2, error: AlertCircle, warning: AlertTriangle, info: Info }[notice.tone];
  return <div className={`feedback-toast ${notice.scope}`} data-tone={notice.tone} role={notice.tone === "error" ? "alert" : "status"}
    onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)} onFocusCapture={() => setPaused(true)} onBlurCapture={(event) => { if (!event.currentTarget.contains(event.relatedTarget)) setPaused(false); }}>
    <Icon size={21} /><div className="feedback-toast-copy"><strong>{notice.title || { success: "Listo", error: "No se pudo completar", warning: "Revisa antes de continuar", info: "Información" }[notice.tone]}</strong><p>{notice.message}</p></div>
    <button type="button" aria-label="Cerrar aviso" onClick={() => onDismiss(notice.id)}><X size={16} /></button>
  </div>;
}

export function FeedbackProvider({ children }) {
  const location = useLocation();
  const [notices, setNotices] = useState([]), [dialog, setDialog] = useState(null);
  const sequence = useRef(0), pending = useRef([]);
  const dismiss = useCallback((id) => setNotices((current) => current.filter((notice) => notice.id !== id)), []);
  const notify = useCallback((message, options = {}) => {
    if (typeof message !== "string" || !message.trim()) return;
    const values = typeof options === "boolean" ? { tone: options ? "error" : "success" } : options && typeof options === "object" ? options : {};
    const tone = ["success", "error", "warning", "info"].includes(values.tone) ? values.tone : "success";
    const id = ++sequence.current;
    setNotices((current) => [...current.filter((notice) => notice.message !== message || notice.tone !== tone), { ...values, tone, message, id, scope: roleScope() }].slice(-3));
  }, []);
  const confirm = useCallback((options) => new Promise((resolve) => {
    const scoped = { ...options, className: roleScope() };
    pending.current.push({ options: scoped, resolve });
    if (pending.current.length === 1) setDialog(scoped);
  }), []);
  const resolve = useCallback((answer) => {
    pending.current.shift()?.resolve(answer);
    setDialog(pending.current[0]?.options || null);
  }, []);
  useEffect(() => {
    setNotices([]);
    pending.current.splice(0).forEach((entry) => entry.resolve(false));
    setDialog(null);
  }, [location.pathname]);
  useEffect(() => {
    const handle = (event) => notify(event.detail?.message, event.detail?.error ? { tone: "error" } : event.detail?.options);
    window.addEventListener("talentsync:feedback", handle);
    return () => { window.removeEventListener("talentsync:feedback", handle); pending.current.splice(0).forEach((entry) => entry.resolve(false)); };
  }, [notify]);
  return <FeedbackContext.Provider value={{ notify, confirm }}>{children}
    <div className="feedback-stack" aria-label="Avisos de la aplicación">{notices.map((notice) => <FeedbackToast notice={notice} key={notice.id} onDismiss={dismiss} />)}</div>
    <ConfirmModal key={dialog?.title || "closed"} open={Boolean(dialog)} {...dialog} onClose={() => resolve(false)} onConfirm={() => resolve(true)} />
  </FeedbackContext.Provider>;
}
