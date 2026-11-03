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
  const [result, setResult] = useState(null);
  const [retry, setRetry] = useState(0);
  const encoded = JSON.stringify(params);
  const key = JSON.stringify([endpoint, encoded, refresh, retry]);
  useEffect(() => {
    const controller = new AbortController();
    api.get(endpoint, { params: JSON.parse(encoded), signal: controller.signal }).then(({ data }) => {
      if (!controller.signal.aborted) setResult({ key, data, error: "" });
    }).catch((failure) => {
      if (!controller.signal.aborted) setResult({ key, data: null, error: getApiErrorMessage(failure) });
    });
    return () => controller.abort();
  }, [endpoint, encoded, key]);
  const current = result?.key === key ? result : null;
  return { data: current?.data ?? null, loading: !current, error: current?.error || "", reload: () => setRetry((value) => value + 1) };
}
