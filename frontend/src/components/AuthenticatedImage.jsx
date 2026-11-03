import { useEffect, useState } from "react";

import { api } from "../api/client.js";

export function AuthenticatedImage({ src, fallback = null, ...props }) {
  const [objectUrl, setObjectUrl] = useState("");

  useEffect(() => {
    if (!src) {
      setObjectUrl("");
      return undefined;
    }
    const controller = new AbortController();
    let createdUrl = "";
    const requestPath = src.startsWith("/api/v1/")
      ? src.slice("/api/v1".length)
      : src;
    api.get(requestPath, { responseType: "blob", signal: controller.signal })
      .then(({ data }) => {
        createdUrl = URL.createObjectURL(data);
        setObjectUrl(createdUrl);
      })
      .catch(() => setObjectUrl(""));
    return () => {
      controller.abort();
      if (createdUrl) URL.revokeObjectURL(createdUrl);
    };
  }, [src]);

  return objectUrl ? <img src={objectUrl} {...props} /> : fallback;
}
