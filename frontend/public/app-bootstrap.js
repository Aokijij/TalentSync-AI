// Only controls the first paint. Authentication is always checked by the API.
(() => {
  const publicPaths = new Set(["/", "/candidatos", "/empresas", "/privacidad", "/terminos"]);
  if (!publicPaths.has(location.pathname.replace(/\/+$/, "") || "/")) {
    document.documentElement.dataset.appRoute = "private";
    document.title = "TalentSync";
  }
})();
