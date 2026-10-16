import { Check, Minus } from "lucide-react";
import { matchingSkills } from "../utils/talentSearch.js";

export function TalentComparison({ candidates, requiredSkills }) {
  const skills = requiredSkills.slice(0, 5);
  if (!candidates.length || !skills.length) return null;
  return <details className="surface-card talent-comparison"><summary>Comparar los mejores perfiles <span>{Math.min(5, candidates.length)} personas · {skills.length} habilidades</span></summary><div className="overflow-x-auto"><table><caption className="sr-only">Coincidencias declaradas de los cinco primeros candidatos para los filtros actuales</caption><thead><tr><th scope="col">Candidato</th>{skills.map((skill) => <th scope="col" key={skill}>{skill}</th>)}<th scope="col">Compatibilidad</th></tr></thead><tbody>{candidates.slice(0, 5).map((candidate) => <tr key={candidate.user_id}><th scope="row"><strong>{candidate.name}</strong><small>{candidate.profession}</small></th>{skills.map((skill) => { const matched = matchingSkills(candidate.skills, [skill]).length > 0; return <td key={skill}><span className={matched ? "matched" : "missing"} aria-label={matched ? "Declarada" : "Sin coincidencia directa"}>{matched ? <Check size={15} /> : <Minus size={15} />}</span></td>; })}<td><strong>{Math.round(candidate.match_percentage)}%</strong></td></tr>)}</tbody></table></div></details>;
}
