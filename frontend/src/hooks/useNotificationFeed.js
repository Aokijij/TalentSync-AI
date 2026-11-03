import { useEffect, useRef, useState } from "react";
import { api } from "../api/client.js";
import { createNotificationFeed, emptyNotificationFeed } from "../utils/notificationFeed.js";

export function useNotificationFeed(filter) {
  const [state, setState] = useState(() => ({ ...emptyNotificationFeed(), filter }));
  const feed = useRef(null);
  useEffect(() => {
    const current = createNotificationFeed((params, signal) => api.get("/notifications", { params, signal, __quiet: true }).then(({ data }) => data), (next) => setState({ ...next, filter }));
    feed.current = current;
    void current.reset(filter);
    return () => current.dispose();
  }, [filter]);
  return { ...(state.filter === filter ? state : emptyNotificationFeed()), reload: () => feed.current?.reset(filter), loadMore: () => feed.current?.more() };
}
