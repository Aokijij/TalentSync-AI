export function OfferPublicationStatus({ quality, status }) {
  if (!quality) return null;
  const minimum = quality.minimum_publish_score || 60;
  const critical = quality.issues?.filter((row) => row.severity === "critical") || [];
  return <div className={`offer-publication-status ${quality.can_publish ? "ready" : "pending"}`} role="status"><strong>{status === "active" ? "Oferta publicada" : quality.can_publish ? "Lista para publicar" : quality.score >= minimum ? "Puntaje suficiente · faltan datos por resolver" : `Faltan ${minimum - quality.score} puntos para el mínimo`}</strong><p>{status === "active" ? "Los cambios se aplicarán al guardar. Revisa los datos pendientes para mantener la oferta completa." : quality.can_publish ? `Cumple el mínimo de ${minimum}/100 y los datos obligatorios. Puedes publicar; las mejoras restantes son opcionales.` : `Publicar requiere ${minimum}/100 y los datos obligatorios completos. Tener más puntos no sustituye esos datos.`}</p>{!!quality.blockers?.length && <p><b>Falta:</b> {quality.blockers.map((row) => row.label).join("; ")}.</p>}{!!critical.length && <p><b>Revisa:</b> {critical.map((row) => row.message).join(" ")}</p>}</div>;
}
