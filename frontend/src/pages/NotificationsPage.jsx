import { useState } from "react";
import { ArrowRight, Bell, CalendarClock, CheckCheck, FileCheck2, Sparkles, Trash2, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { formatRelativeTime } from "../utils/dates.js";
import { useNotificationFeed } from "../hooks/useNotificationFeed.js";
import { processDate } from "../utils/interviewAgenda.js";

const typeMeta = {
  application_interview: { label: "Entrevista", icon: CalendarClock },
  application_status: { label: "Cambio de etapa", icon: FileCheck2 },
  application_received: { label: "Nueva candidatura", icon: UserPlus },
  application_updated: { label: "Actualización de proceso", icon: FileCheck2 },
  application_selected: { label: "Selección", icon: CheckCheck },
  application_not_selected: { label: "Proceso finalizado", icon: FileCheck2 },
  candidate_invitation: { label: "Invitación", icon: UserPlus },
  company_job_match: { label: "Nueva oportunidad", icon: Sparkles },
};

export function NotificationsPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [filter, setFilter] = useState("all");
  const { items, hasMore, loading, error: loadError, reload, loadMore } = useNotificationFeed(filter);

  async function openNotification(item) {
    if (busy || loading) return;
    setBusy(true); setError("");
    try {
      if (!item.is_read) await api.put(`/notifications/${item.id}/read`);
      window.dispatchEvent(new CustomEvent("talentsync:notifications-changed"));
      const fallback = item.type === "application_received" ? "/empresa/postulaciones" : item.type.startsWith("application") ? "/postulaciones" : null;
      if (item.action_url || fallback) navigate(item.action_url || fallback);
      else await reload();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible abrir la notificación"));
    } finally { setBusy(false); }
  }

  async function markAllRead() {
    if (busy || loading) return;
    setBusy(true); setError("");
    try {
      await api.put("/notifications/read-all");
      await reload();
      window.dispatchEvent(new CustomEvent("talentsync:notifications-changed", { detail: { count: 0 } }));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible actualizar las notificaciones"));
    } finally { setBusy(false); }
  }

  async function removeNotification(item) {
    if (busy || loading) return;
    setBusy(true); setError("");
    try {
      await api.delete(`/notifications/${item.id}`);
      await reload();
      if (!item.is_read) window.dispatchEvent(new CustomEvent("talentsync:notifications-changed"));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible quitar la notificación"));
    } finally { setBusy(false); }
  }

  async function clearRead() {
    if (busy || loading) return;
    setBusy(true); setError("");
    try {
      await api.delete("/notifications/read");
      await reload();
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible limpiar las notificaciones leídas"));
    } finally { setBusy(false); }
  }

  const tabs = user?.role === "company"
    ? [["all", "Todas"], ["unread", "Sin leer"], ["applications", "Candidaturas"], ["system", "Sistema"]]
    : [["all", "Todas"], ["unread", "Sin leer"], ["applications", "Mis procesos"], ["opportunities", "Oportunidades"]];

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Actividad"
        title="Notificaciones"
        description={user?.role === "company" ? "Organiza nuevas candidaturas, cambios de proceso y avisos del sistema." : "Separa oportunidades, invitaciones y cambios de tus postulaciones."}
        actions={<div className="flex flex-wrap gap-2">{items.some((item) => item.is_read) ? <button type="button" onClick={clearRead} disabled={busy || loading} className="button-secondary"><Trash2 size={16} /> Quitar leídas</button> : null}{items.some((item) => !item.is_read) ? <button type="button" onClick={markAllRead} disabled={busy || loading} className="button-secondary"><CheckCheck size={16} /> Marcar todas como leídas</button> : null}</div>}
      />
      {(error || loadError) && <p role="alert" className="ui-inline-notice is-error">{error || getApiErrorMessage(loadError, "No pudimos cargar las notificaciones.")} <button type="button" disabled={loading || busy} className="underline" onClick={reload}>Reintentar</button></p>}
      {loading && <p role="status" className="text-sm text-[var(--muted)]">Cargando notificaciones…</p>}

      <nav className="surface-card flex gap-2 overflow-x-auto p-2" aria-label="Filtros de notificaciones">
        {tabs.map(([value, label]) => <button key={value} type="button" disabled={busy} aria-pressed={filter === value} className={filter === value ? "button-primary button-sm whitespace-nowrap" : "button-ghost button-sm whitespace-nowrap"} onClick={() => { setFilter(value); setError(""); }}>{label}</button>)}
      </nav>

      <section className="surface-card overflow-hidden !p-0">
        <header className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-5">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Bell size={20} /></div>
          <div><h2 className="font-bold text-[var(--ink-strong)]">Actividad</h2><p className="text-sm text-[var(--muted)]">{loading && !items.length ? "Consultando tu actividad…" : loadError && !items.length ? "Actividad no disponible" : items.length ? `${items.filter((item) => !item.is_read).length} sin leer · ${items.length} mostradas` : "Estás al día"}</p></div>
        </header>

        <div className="divide-y divide-[var(--line)]">
          {items.map((item) => {
            const meta = typeMeta[item.type] ?? { label: "Novedad", icon: FileCheck2 };
            const Icon = meta.icon;
            return (
              <article key={item.id} className={`group flex gap-3 px-5 py-5 transition-colors hover:bg-[var(--accent)]/10 ${item.is_read ? "bg-[var(--surface)]" : "bg-[var(--accent)]/[0.06]"}`}>
                <button type="button" onClick={() => openNotification(item)} disabled={busy || loading} className="flex min-w-0 flex-1 gap-4 text-left">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Icon size={18} /></div>
                  <div className="min-w-0 flex-1">
                    <span className="inline-flex rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--accent)]">{meta.label}</span>
                    {!item.is_read ? <span className="ml-2 inline-flex rounded-full bg-[var(--success)]/10 px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--success)]">Nueva</span> : null}
                    <p className="mt-2 font-bold text-[var(--ink-strong)]">{item.title}</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">{item.body}</p>
                    <p className="mt-2 text-xs text-[var(--muted)]">{formatRelativeTime(item.created_at)} · {processDate(item.created_at)?.toLocaleString("es-CO", { timeZone: "America/Bogota" })}</p>
                  </div>
                  <ArrowRight size={18} className="mt-3 shrink-0 text-[var(--muted)] transition-transform group-hover:translate-x-1 group-hover:text-[var(--accent)]" />
                </button>
                <button type="button" className="button-ghost button-sm self-center !px-2 text-[var(--muted)] hover:text-[var(--error)]" disabled={busy || loading} onClick={() => removeNotification(item)} aria-label="Quitar notificación" title="Quitar"><Trash2 size={16} /></button>
              </article>
            );
          })}
          {!items.length && !loading && !loadError ? <div className="px-5 py-16 text-center"><div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[var(--success)]/10 text-[var(--success)]"><Sparkles size={24} /></div><p className="mt-4 font-bold text-[var(--ink-strong)]">No hay notificaciones en esta categoría</p><p className="mt-1 text-sm text-[var(--muted)]">Puedes cambiar de sección para consultar el historial restante.</p></div> : null}
        </div>
        {hasMore ? <div className="border-t border-[var(--line)] p-4 text-center"><button type="button" className="button-secondary" disabled={busy || loading} onClick={loadMore}>Cargar más</button></div> : null}
      </section>
    </div>
  );
}
