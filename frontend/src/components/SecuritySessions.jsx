import { useState } from "react";
import { Laptop, LogOut, Monitor, Smartphone } from "lucide-react";
import { Pagination } from "./Pagination.jsx";

function deviceLabel(agent = "") {
  const browser = /Edg\//.test(agent) ? "Microsoft Edge" : /Firefox\//.test(agent) ? "Firefox" : /Chrome\//.test(agent) ? "Chrome" : /Safari\//.test(agent) ? "Safari" : "Navegador";
  const system = /Android/.test(agent) ? "Android" : /iPhone|iPad/.test(agent) ? "iOS" : /Windows/.test(agent) ? "Windows" : /Macintosh|Mac OS/.test(agent) ? "macOS" : /Linux/.test(agent) ? "Linux" : "Otro dispositivo";
  return `${browser} · ${system}`;
}

export function SecuritySessions({ sessions, busy, onRevoke }) {
  const [closed, setClosed] = useState(false), [page, setPage] = useState(1);
  const rows = sessions.filter((row) => closed ? row.revoked : !row.revoked);
  const pages = Math.max(1, Math.ceil(rows.length / 6)), safePage = Math.min(page, pages);
  return <section id="security-sessions" className="security-panel"><header><span className="security-panel-icon"><Monitor size={24} /></span><div><h2>Dispositivos y sesiones</h2><p>Revisa dónde está abierta tu cuenta y cierra los accesos que ya no utilices.</p></div></header><div className="security-session-tabs"><button type="button" aria-pressed={!closed} onClick={() => { setClosed(false); setPage(1); }}>Activas <span>{sessions.filter((row) => !row.revoked).length}</span></button><button type="button" aria-pressed={closed} onClick={() => { setClosed(true); setPage(1); }}>Cerradas</button></div><div className="security-session-list">{rows.slice((safePage - 1) * 6, safePage * 6).map((session) => {
    const Icon = /Android|iPhone|iPad/.test(session.device || "") ? Smartphone : Laptop;
    const date = session.last_seen_at ? new Date(session.last_seen_at.endsWith("Z") ? session.last_seen_at : `${session.last_seen_at}Z`).toLocaleString("es-CO") : "Sin fecha";
    return <article key={session.id}><span className="session-device-icon"><Icon size={22} /></span><div className="min-w-0"><h3>{deviceLabel(session.device)}{session.current && <span>Este dispositivo</span>}</h3><p>Última actividad: {date}</p><details><summary>Información del dispositivo</summary><p className="break-all">{session.device || "Sin información adicional"}</p></details></div>{!session.revoked ? <button type="button" disabled={busy} className="button-secondary button-sm" onClick={() => onRevoke(session)}><LogOut size={14} />Cerrar sesión</button> : <span className="status-chip">Cerrada</span>}</article>;
  })}{!rows.length && <p className="learning-empty">No hay sesiones {closed ? "cerradas" : "activas"} para mostrar.</p>}</div><Pagination page={safePage} pages={pages} total={rows.length} pageSize={6} onChange={setPage} label="Páginas de dispositivos" /></section>;
}
