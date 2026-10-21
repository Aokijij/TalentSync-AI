export function CredentialRequirementsSummary({ value }) {
  if (!value?.driving_categories?.length && !value?.professional_cards?.length) return null;
  return <div>{!!value.driving_categories?.length && <section className="credential-summary"><h3>Licencia de conducción</h3><p>Categorías aceptadas: {value.driving_categories.join(" o ")}.</p></section>}{!!value.professional_cards?.length && <section className="credential-summary"><h3>Tarjeta profesional</h3><p>Profesiones aceptadas: {value.professional_cards.join(" o ")}.</p></section>}</div>;
}

export function CredentialMatchDetails({ value }) {
  if (!value?.groups?.length) return null;
  const labels = { recorded: "Documento registrado · por verificar", missing: "Sin registro", not_met: "Sin registro de lo solicitado" };
  return <section className="credential-summary"><h3>Revisión de licencias y tarjetas</h3>{value.groups.map((row) => <div key={row.key}><strong>{row.label}: {row.accepted.join(" o ")}</strong><p>{labels[row.status]}</p><small>{row.reason}</small></div>)}<p className="credential-note">{value.notice}</p></section>;
}
