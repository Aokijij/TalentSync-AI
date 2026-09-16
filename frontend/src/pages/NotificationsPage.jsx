import { useEffect, useState } from "react";
import {
  ArrowRight,
  Bell,
  CalendarClock,
  CheckCheck,
  FileCheck2,
  Sparkles,
  UserPlus,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";

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
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const { data } = await api.get("/notifications", {
        params: { unread_only: false },
      });
      setItems(data);
      window.dispatchEvent(
        new CustomEvent("talentsync:notifications-changed", {
          detail: { count: data.filter((item) => !item.is_read).length },
        }),
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible cargar las notificaciones",
        ),
      );
    }
  }
  useEffect(() => {
    load();
  }, []);

  async function openNotification(item) {
    try {
      await api.put(`/notifications/${item.id}/read`);
      const updated = items.map((current) =>
        current.id === item.id ? { ...current, is_read: true } : current,
      );
      setItems(updated);
      window.dispatchEvent(
        new CustomEvent("talentsync:notifications-changed", {
          detail: { count: updated.filter((current) => !current.is_read).length },
        }),
      );
      const fallback =
        item.type === "application_received"
          ? "/empresa/postulaciones"
          : item.type.startsWith("application")
            ? "/postulaciones"
            : null;
      if (item.action_url || fallback) navigate(item.action_url || fallback);
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible abrir la notificación",
        ),
      );
    }
  }

  async function markAllRead() {
    try {
      await api.put("/notifications/read-all");
      setItems((current) =>
        current.map((item) => ({ ...item, is_read: true })),
      );
      window.dispatchEvent(
        new CustomEvent("talentsync:notifications-changed", {
          detail: { count: 0 },
        }),
      );
    } catch (requestError) {
      setError(
        getApiErrorMessage(
          requestError,
          "No fue posible actualizar las notificaciones",
        ),
      );
    }
  }

  return (
    <div className="space-y-6">
      <PageHeader
        kicker="Actividad"
        title="Notificaciones"
        description="Consulta novedades, invitaciones y cambios de tus procesos con el contexto necesario."
        actions={
          items.some((item) => !item.is_read) ? (
            <button
              type="button"
              onClick={markAllRead}
              className="button-secondary"
            >
              <CheckCheck size={16} />
              Marcar todas como leídas
            </button>
          ) : null
        }
      />
      {error ? (
        <p
          role="alert"
          className="rounded-[var(--radius-lg)] border border-[var(--error)] bg-[var(--error)]/10 px-4 py-3 text-sm text-[var(--error)]"
        >
          {error}
        </p>
      ) : null}
      <section className="surface-card overflow-hidden !p-0">
        <header className="flex items-center gap-3 border-b border-[var(--line)] px-5 py-5">
          <div className="grid h-10 w-10 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]">
            <Bell size={20} />
          </div>
          <div>
            <h2 className="font-bold text-[var(--ink-strong)]">
              Actividad pendiente
            </h2>
            <p className="text-sm text-[var(--muted)]">
              {items.length
                ? `${items.filter((item) => !item.is_read).length} sin leer · ${items.length} en total`
                : "Estás al día"}
            </p>
          </div>
        </header>
        <div className="divide-y divide-[var(--line)]">
          {items.map((item) => {
            const meta = typeMeta[item.type] ?? {
              label: "Novedad",
              icon: FileCheck2,
            };
            const Icon = meta.icon;
            return (
              <button
                type="button"
                key={item.id}
                onClick={() => openNotification(item)}
                className={`group flex w-full gap-4 px-5 py-5 text-left transition-colors hover:bg-[var(--accent)]/10 ${item.is_read ? "bg-[var(--surface)]" : "bg-[var(--accent)]/[0.06]"}`}
              >
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]">
                  <Icon size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <span className="inline-flex rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--accent)]">
                    {meta.label}
                  </span>
                  {!item.is_read ? <span className="ml-2 inline-flex rounded-full bg-[var(--success)]/10 px-2 py-0.5 text-[10px] font-bold uppercase text-[var(--success)]">Nueva</span> : null}
                  <p className="mt-2 font-bold text-[var(--ink-strong)]">
                    {item.title}
                  </p>
                  <p className="mt-1 text-sm text-[var(--muted)]">
                    {item.body}
                  </p>
                  <p className="mt-2 text-xs text-[var(--muted)]">
                    {new Date(item.created_at).toLocaleString("es-CO")}
                  </p>
                </div>
                <ArrowRight
                  size={18}
                  className="mt-3 shrink-0 text-[var(--muted)] transition-transform group-hover:translate-x-1 group-hover:text-[var(--accent)]"
                />
              </button>
            );
          })}
          {!items.length ? (
            <div className="px-5 py-16 text-center">
              <div className="mx-auto grid h-14 w-14 place-items-center rounded-full bg-[var(--success)]/10 text-[var(--success)]">
                <Sparkles size={24} />
              </div>
              <p className="mt-4 font-bold text-[var(--ink-strong)]">
                No tienes notificaciones pendientes
              </p>
              <p className="mt-1 text-sm text-[var(--muted)]">
                Las próximas invitaciones y actualizaciones aparecerán aquí.
              </p>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
