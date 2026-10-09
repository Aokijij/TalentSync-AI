// POST is also used for calculations and presence. Those calls do not save user edits.
export function shouldNotifyMutation(config = {}) {
  const method = String(config.method || "get").toLowerCase();
  const path = String(config.url || "").split("?")[0];
  return ["post", "put", "patch", "delete"].includes(method) && !config.__quiet &&
    !/^\/?auth\//.test(path) && !/^\/jobs\/\d+\/match$/.test(path) &&
    !/^\/interviews\/rooms\/.*\/(presence|signal|connect)$/.test(path);
}
