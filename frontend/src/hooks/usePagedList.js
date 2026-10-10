import { useEffect, useState } from "react";
import { api, getApiErrorMessage } from "../api/client.js";

export function useDebouncedValue(value, delay = 300) {
  const [result, setResult] = useState(value);
  useEffect(() => {
    const timer = window.setTimeout(() => setResult(value.trim()), delay);
    return () => window.clearTimeout(timer);
  }, [value, delay]);
  return result;
}

export function usePagedList(endpoint, params, refresh = 0) {
  const [data, setData] = useState(null), [loading, setLoading] = useState(true), [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  const encoded = JSON.stringify(params);
  useEffect(() => {
    let active = true;
    setLoading(true); setError("");
    api.get(endpoint, { params: JSON.parse(encoded) }).then(({ data: result }) => {
      if (active) setData(result);
    }).catch((failure) => {
      if (active) setError(getApiErrorMessage(failure));
    }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [endpoint, encoded, refresh, retry]);
  return { data, loading, error, reload: () => setRetry((value) => value + 1) };
}
