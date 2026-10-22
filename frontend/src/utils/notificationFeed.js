export const emptyNotificationFeed = () => ({ items: [], loading: true, error: null, hasMore: false });

export function createNotificationFeed(request, onChange, pageSize = 20) {
  let state = emptyNotificationFeed(), offset = 0, generation = 0, controller = null, category = "all", disposed = false;
  const publish = (patch) => { state = { ...state, ...patch }; if (!disposed) onChange(state); };
  async function load(reset, filter = category) {
    if (disposed || !reset && (state.loading || !state.hasMore)) return;
    if (reset) {
      generation += 1; controller?.abort(); offset = 0; category = filter;
      publish({ items: [], hasMore: false });
    }
    const current = generation;
    const requestController = new AbortController();
    controller = requestController;
    publish({ loading: true, error: null });
    try {
      const rows = await request({ unread_only: category === "unread", category: ["applications", "opportunities", "system"].includes(category) ? category : undefined, limit: pageSize, offset }, requestController.signal);
      if (disposed || current !== generation || requestController.signal.aborted) return;
      // Offset follows consumed server rows even when new notifications overlap a page.
      offset += rows.length;
      const items = [...new Map([...state.items, ...rows].map((row) => [row.id, row])).values()];
      publish({ items, hasMore: rows.length === pageSize });
    } catch (error) {
      if (!disposed && current === generation && !requestController.signal.aborted) publish({ error });
    } finally {
      if (!disposed && current === generation && !requestController.signal.aborted) publish({ loading: false });
    }
  }
  return { reset: (filter = category) => load(true, filter), more: () => load(false), dispose() { disposed = true; generation += 1; controller?.abort(); } };
}
