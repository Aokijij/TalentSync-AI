import { useEffect, useState } from "react";
import { ArrowRight, Bell, CalendarClock, CheckCheck, FileCheck2, Sparkles, Trash2, UserPlus } from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { useAuth } from "../hooks/useAuth.js";
import { formatRelativeTime } from "../utils/dates.js";

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
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [filter, setFilter] = useState("all");
  const [hasMore, setHasMore] = useState(false);
  const pageSize = 20;

  async function load(reset = true) {
    try {
      const { data } = await api.get("/notifications", {
        params: {
          unread_only: filter === "unread",
          category: ["applications", "opportunities", "system"].includes(filter) ? filter : undefined,
          limit: pageSize,
          offset: reset ? 0 : items.length,
        },
      });
      const next = reset ? data : [...items, ...data];
      setItems(next);
      setHasMore(data.length === pageSize);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible cargar las notificaciones"));
    }
  }

  useEffect(() => {
    load(true);
  }, [filter]);

  async function openNotification(item) {
    try {
      if (!item.is_read) await api.put(`/notifications/${item.id}/read`);
      const updated = items.map((current) => current.id === item.id ? { ...current, is_read: true } : current);
      setItems(updated);
      window.dispatchEvent(new CustomEvent("talentsync:notifications-changed"));
      const fallback = item.type === "application_received" ? "/empresa/postulaciones" : item.type.startsWith("application") ? "/postulaciones" : null;
      if (item.action_url || fallback) navigate(item.action_url || fallback);
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible abrir la notificación"));
    }
  }

  async function markAllRead() {
    try {
      await api.put("/notifications/read-all");
      setItems((current) => current.map((item) => ({ ...item, is_read: true })));
      window.dispatchEvent(new CustomEvent("talentsync:notifications-changed", { detail: { count: 0 } }));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible actualizar las notificaciones"));
    }
  }

  async function removeNotification(item) {
    try {
      await api.delete(`/notifications/${item.id}`);
      const next = items.filter((entry) => entry.id !== item.id);
      setItems(next);
      if (!item.is_read) window.dispatchEvent(new CustomEvent("talentsync:notifications-changed"));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible quitar la notificación"));
    }
  }

  async function clearRead() {
    try {
      await api.delete("/notifications/read");
      setItems((current) => current.filter((item) => !item.is_read));
    } catch (requestError) {
      setError(getApiErrorMessage(requestError, "No fue posible limpiar las notificaciones leídas"));
    }
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
        actions={<div className="flex flex-wrap gap-2">{items.some((item) => item.is_read) ? <button type="button" onClick={clearRead} className="button-secondary"><Trash2 size={16} /> Quitar leídas</button> : null}{items.some((item) => !item.is_read) ? <button type="button" onClick={markAllRead} className="button-secondary"><CheckCheck size={16} /> Marcar todas como leídas</button> : null}</div>}
      />
      {error ? <p role="alert" className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]">{error}</p> : null}

      <nav className="surface-card flex gap-2 overflow-x-auto p-2" aria-label="Filtros de notificaciones">
        {tabs.map(([value, label]) => <button key={value} type="button" className={filter === value ? "button-primary button-sm whitespace-nowrap" : "button-ghost button-sm whitespace-nowrap"} onClick={() => setFilter(value)}>{label}</button>)}
      </nav>

      <section className="surface-card overflow-hidden !p-0">
        <header className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-5">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Bell size={20} /></div>
          <div><h2 className="font-bold text-[var(--ink-strong)]">Actividad</h2><p className="text-sm text-[var(--muted)]">{items.length ? `${items.filter((item) => !item.is_read).length} sin leer · ${items.length} mostradas` : "Estás al día"}</p></div>
        </header>

        <div className="divide-y divide-[var(--line)]">
          {items.map((item) => {
            const meta = typeMeta[item.type] ?? { label: "Novedad", icon: FileCheck2 };
            const Icon = meta.icon;
            return (
              <article key={item.id} className={`group flex gap-3 px-5 py-5 transition-colors hover:bg-[var(--accent)]/10 ${item.is_read ? "bg-[var(--surface)]" : "bg-[var(--accent)]/[0.06]"}`}>
                <button type="button" onClick={() => openNotification(item)} className="flex min-w-0 flex-1 gap-4 text-left">
                  <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]"><Icon size={18} /></div>
                  <div className="min-w-0 flex-1">
                    <span className="inline-flex rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--accent)]">{meta.label}</span>
                    {!item.is_read ? <span className="ml-2 inline-flex rounded-full bg-[var(--success)]/10 px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--success)]">Nueva</span> : null}
                    <p className="mt-2 font-bold text-[var(--ink-strong)]">{item.title}</p>
                    <p className="mt-1 text-sm text-[var(--muted)]">{item.body}</p>
                    <p className="mt-2 text-xs text-[var(--muted)]">{formatRelativeTime(item.created_at)} · {new Date(item.created_at).toLocaleString("es-CO")}</p>
                  </div>
                  <ArrowRight size={18} className="mt-3 shrink-0 text-[var(--muted)] transition-transform group-hover:translate-x-1 group-hover:text-[var(--accent)]" />
                </button>
                <button type="button" className="button-ghost button-sm self-center !px-2 text-[var(--muted)] hover:text-[var(--error)]" onClick={() => removeNotification(item)} aria-label="Quitar notificación" title="Quitar"><Trash2 size={16} /></button>
              </article>
            );
          })}
          {!items.length ? <div className="px-5 py-16 text-center"><div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[var(--success)]/10 text-[var(--success)]"><Sparkles size={24} /></div><p className="mt-4 font-bold text-[var(--ink-strong)]">No hay notificaciones en esta categoría</p><p className="mt-1 text-sm text-[var(--muted)]">Puedes cambiar de sección para consultar el historial restante.</p></div> : null}
        </div>
        {hasMore ? <div className="border-t border-[var(--line)] p-4 text-center"><button type="button" className="button-secondary" onClick={() => load(false)}>Cargar más</button></div> : null}
      </section>
    </div>
  );
}
