import { Navigate, useParams, useSearchParams } from "react-router-dom";

// Keep bookmarked links working without fetching a second candidate list.
export function CompanyCandidatesPage() {
  const { jobId } = useParams();
  const [params] = useSearchParams();
  const next = new URLSearchParams(params);
  next.set("job", jobId);
  next.set("audience", params.get("audience") === "applied" ? "applied" : "new");
  return <Navigate replace to={`/empresa/talento?${next}`} />;
}
