import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api, getApiErrorMessage } from "../api/client.js";
import { CareerCoachWorkspace } from "./CareerCoachWorkspace.jsx";

export function CareerCoachTools({ context, job, onDraftSaved, onDone }) {
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null), [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    api.get("/profiles/me").then(({ data }) => { if (active) setProfile(data); })
      .catch((failure) => { if (active) setError(getApiErrorMessage(failure)); });
    return () => { active = false; };
  }, []);
  if (error) return <p role="alert" className="surface-card p-4 text-[var(--error)]">{error}</p>;
  if (!profile) return <p role="status" className="p-4 text-sm text-[var(--muted)]">Cargando tu información…</p>;
  return <>
    {context === "learning" && <p className="text-sm text-[var(--muted)]">Usamos tus habilidades registradas para orientarte. <Link className="text-[var(--accent)] underline" to="/perfil#profile-skills">Actualizar mis habilidades</Link></p>}
    <CareerCoachWorkspace profile={profile} editing={false} context={context} vacancyJob={job} onDraftSaved={onDraftSaved} onDone={onDone} onEdit={(target) => navigate(`/perfil#${target}`)} />
  </>;
}
