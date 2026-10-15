function pause(milliseconds, signal) {
  return new Promise((resolve, reject) => {
    const stop = () => { clearTimeout(timer); reject(Object.assign(new Error("Cancelado"), { code: "ERR_CANCELED" })); };
    const timer = setTimeout(() => { signal?.removeEventListener("abort", stop); resolve(); }, milliseconds);
    if (signal?.aborted) stop();
    else signal?.addEventListener("abort", stop, { once: true });
  });
}

// Exactly one bounded scoring request at a time; view changes cancel its poll.
export async function loadCandidatePages({ request, onPage, signal, wait = pause }) {
  let unchanged = 0, previous;
  while (!signal?.aborted) {
    const response = await request();
    if (signal?.aborted) return;
    onPage(response.data);
    if (!response.data.pending) return;
    unchanged = previous === response.data.pending ? unchanged + 1 : 0;
    previous = response.data.pending;
    await wait(Math.min(2000, 500 + unchanged * 500), signal);
  }
}
