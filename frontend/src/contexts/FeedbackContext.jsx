import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { CheckCircle2, AlertCircle, X } from "lucide-react";
import { ConfirmModal } from "../components/ConfirmModal.jsx";

const FeedbackContext = createContext(null);
export const useFeedback = () => useContext(FeedbackContext);

export function FeedbackProvider({ children }) {
  const [notice, setNotice] = useState(null), [dialog, setDialog] = useState(null);
  const pending = useRef(null);
  const notify = useCallback((message, error = false) => setNotice({ message, error, at: Date.now() }), []);
  const confirm = useCallback((options) => new Promise((resolve) => {
    pending.current?.(false); pending.current = resolve; setDialog(options);
  }), []);
  const resolve = (answer) => { pending.current?.(answer); pending.current = null; setDialog(null); };
  useEffect(() => {
    const handle = (event) => notify(event.detail.message, event.detail.error);
    window.addEventListener("talentsync:feedback", handle);
    return () => { window.removeEventListener("talentsync:feedback", handle); pending.current?.(false); };
  }, [notify]);
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(null), notice.error ? 10000 : 6000); return () => clearTimeout(timer); }, [notice]);
  return <FeedbackContext.Provider value={{ notify, confirm }}>{children}
    {notice && <div className="feedback-toast" role={notice.error ? "alert" : "status"} key={notice.at}>
      {notice.error ? <AlertCircle className="shrink-0 text-[var(--error)]" /> : <CheckCircle2 className="shrink-0 text-[var(--success)]" />}
      <p className="min-w-0 flex-1 text-sm">{notice.message}</p><button aria-label="Cerrar aviso" onClick={() => setNotice(null)}><X size={18} /></button>
    </div>}
    <ConfirmModal open={Boolean(dialog)} {...dialog} onClose={() => resolve(false)} onConfirm={() => resolve(true)} />
  </FeedbackContext.Provider>;
}
