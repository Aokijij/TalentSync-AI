import { useEffect, useState } from "react";
import { useAuth } from "../hooks/useAuth.js";
import { api, getApiErrorMessage } from "../api/client.js";
import { PageHeader } from "../components/PageHeader.jsx";
import { PlatformGuide } from "../components/PlatformGuide.jsx";

export function PlatformGuidePage() {
  const { user } = useAuth();
  const [memberRole, setMemberRole] = useState(null), [error, setError] = useState(""), [revision, setRevision] = useState(0);
  useEffect(() => {
    if (user.role !== "company") return;
    let active = true; setError("");
    api.get("/organization/access").then(({ data }) => { if (active) setMemberRole(data.role); }).catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, [user.role, revision]);
  return <div className="space-y-6"><PageHeader kicker="AYUDA PARA TU RECORRIDO" title="Tu guía de TalentSync" description="Aprende dónde está cada función, cómo utilizarla y qué significan sus resultados." />{error && <div className="welcome-alert" role="alert"><p>{error}</p><button className="button-secondary" onClick={() => setRevision((value) => value + 1)}>Reintentar</button></div>}{user.role === "company" && !memberRole ? !error && <p role="status">Consultando tus permisos de equipo…</p> : <PlatformGuide role={user.role} memberRole={memberRole || "owner"} />}</div>;
}
