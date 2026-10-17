import { useEffect, useState } from "react";
import { TextItemsEditor } from "./TextItemsEditor.jsx";

export function AcademicStudyFields(props) {
  const [suggestions, setSuggestions] = useState([]);
  useEffect(() => {
    const controller = new AbortController();
    import("../api/client.js").then(({ api }) => api.get("/hiring/education/catalog", { signal: controller.signal })).then(({ data }) => {
      if (!controller.signal.aborted) setSuggestions([...new Set(data.items.flatMap((row) => [row.label, ...row.aliases]))]);
    }).catch(() => { /* Free text remains available when catalog loading fails. */ });
    return () => controller.abort();
  }, []);
  return <TextItemsEditor {...props} suggestions={suggestions} help="Elige una sugerencia o añade otra denominación. Los nombres no reconocidos quedan por revisar al comparar el perfil." />;
}
