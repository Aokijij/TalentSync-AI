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
};

export function NotificationsPage() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");

  async function load() {
    try {
      const { data } = await api.get("/notifications", {
        params: { unread_only: true },
      });
      setItems(data);
      window.dispatchEvent(
        new CustomEvent("talentsync:notifications-changed", {
          detail: { count: data.length },
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
      const remaining = items.filter((current) => current.id !== item.id);
      setItems(remaining);
      window.dispatchEvent(
        new CustomEvent("talentsync:notifications-changed", {
          detail: { count: remaining.length },
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
      setItems([]);
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
        description="Solo mostramos novedades pendientes. Al abrir una, desaparecerá de esta bandeja."
        actions={
          items.length ? (
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
                ? `${items.length} novedad${items.length === 1 ? "" : "es"} sin leer`
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
                className="group flex w-full gap-4 bg-[var(--accent)]/[0.04] px-5 py-5 text-left transition-colors hover:bg-[var(--accent)]/10"
              >
                <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[var(--accent)]/10 text-[var(--accent)]">
                  <Icon size={18} />
                </div>
                <div className="min-w-0 flex-1">
                  <span className="inline-flex rounded-full bg-[var(--accent)]/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-[var(--accent)]">
                    {meta.label}
                  </span>
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
                Los próximos cambios de etapa aparecerán aquí.
              </p>
            </div>
          ) : null}
        </div>
      </section>
    </div>
  );
}
