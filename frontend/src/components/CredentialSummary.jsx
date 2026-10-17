export function CredentialRequirementsSummary({ value }) {
  if (!value?.driving_categories?.length && !value?.professional_cards?.length) return null;
  return <section className="credential-summary"><h3>Licencias y tarjetas solicitadas</h3>{!!value.driving_categories?.length && <p><strong>Licencia de conducción vigente:</strong> {value.driving_categories.join(" o ")}.</p>}{!!value.professional_cards?.length && <p><strong>Tarjeta profesional vigente:</strong> {value.professional_cards.join(" o ")}.</p>}<small>Se revisarán los documentos declarados durante el proceso.</small></section>;
}

export function CredentialMatchDetails({ value }) {
  if (!value?.groups?.length) return null;
  const labels = { declared: "Vigencia declarada · por verificar", review: "Por revisar", missing: "Sin registro", not_met: "No cumple la vigencia solicitada" };
  return <section className="credential-summary"><h3>Revisión de licencias y tarjetas</h3>{value.groups.map((row) => <div key={row.key}><strong>{row.label}: {row.accepted.join(" o ")}</strong><p>{labels[row.status]}</p><small>{row.reason}</small></div>)}<p className="credential-note">{value.notice}</p></section>;
}
