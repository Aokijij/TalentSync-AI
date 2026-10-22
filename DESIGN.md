# TalentSync: reglas de interfaz

La interfaz debe ayudar a encontrar una oportunidad, revisar un candidato o completar una tarea. La identidad actual se mantiene: azul para candidatos, violeta para empresas y ámbar para administración, con temas claro y oscuro.

## Componentes y medidas

- `frontend/src/styles/design-system.css` define espaciado, radios, tamaño de texto y altura de controles. Usar esos valores antes de añadir medidas aisladas.
- `PageHeader` presenta título, descripción breve y acciones, sin un contenedor de bienvenida que ocupe la primera pantalla.
- `Panel`, `PanelActions`, `WorkspaceTabs` e `InlineNotice` están en `frontend/src/components/ui/Panel.jsx`.
- Las acciones de una tarjeta ocupan todo el ancho de su pie. No deben heredar una anchura limitada al texto de sus botones.
- Controles principales de al menos 44 px de altura. Texto de contenido de 14 px; metadatos de al menos 12 px. Títulos de página de 24–28 px.
- En móvil, las columnas se apilan antes de que el contenido quede comprimido. Las pestañas pueden desplazarse dentro de su fila; la página no debe desplazarse horizontalmente.
- Mantener una única familia de iconos: Lucide. Los iconos acompañan el significado; los controles conservan una etiqueta comprensible.

## Contenido y estados

- Cada pantalla responde primero a una pregunta del usuario. Situar junto a ella la acción más frecuente.
- Los contadores se calculan a partir de los datos mostrados. Un dato desconocido no es un cero.
- Las secciones opcionales extensas comienzan plegadas o se abren mediante una acción explícita.
- Los estados vacíos explican el siguiente paso. Las empresas no reciben formularios para completar los datos del candidato.
- Mostrar un error dentro del bloque afectado y permitir reintentar. Conservar los textos no guardados cuando falla una operación.
- Distinguir perfil actual, documento guardado y documento enviado. Una práctica privada no se presenta como una acreditación o puntuación laboral.
- El color señala selección, una acción o un estado; no debe ser la única forma de reconocerlos.

## Movimiento y accesibilidad

- Usar transiciones breves para foco, selección y cambios de estado. Respetar `prefers-reduced-motion`.
- Pestañas con navegación por flechas, Home y End; campos con etiquetas; diálogos con título, cierre y recuperación del foco.
- El contenido esencial no depende de animaciones, 3D, transparencia, hover ni desplazamiento animado.
- Los temas y tamaños necesitan revisión visual además de pruebas de lógica. Una compilación correcta no confirma un diseño correcto.

## Referencias utilizadas

- [Taste-Skill: pantallas de aplicaciones](https://github.com/Leonxlnx/taste-skill/blob/main/skills/taste-skill/references/app-screens.md): jerarquía, densidad, estados honestos, controles y estructura. Las pautas se adaptan a nuestra marca; sus scripts no forman parte de la aplicación.
- [Mobbin](https://mobbin.com/) y [Refero Styles](https://styles.refero.design/): referencias de organización y consistencia; no se copiaron pantallas ni recursos propietarios.
- [Figma: estructura y componentes](https://developers.figma.com/docs/figma-mcp-server/structure-figma-file/): variables y componentes compartidos. Una futura biblioteca de Figma debe reflejar estos componentes reales.

## Revisión reproducible

`frontend/quality/` monta componentes reales con datos ficticios, sin credenciales ni acceso a la API. No es una entrada del build publicado.

Desde `frontend/`:

```text
npm test
npm run lint
npm run build
npm run quality:ui:build
npm run quality:ui:list
```

La suite `npm run quality:ui` requiere Chromium de Playwright y un entorno autorizado para ejecutar un navegador. Define 24 combinaciones: 360, 768, 1280 y 1440 px, tres roles, dos temas. Comprueba desbordamiento, pies de tarjetas y el recorrido de teclado/respuestas; adjunta capturas al informe HTML. El CI guarda ese informe durante siete días.

Las capturas sirven para revisión. Todavía no hay imágenes de referencia aprobadas para comparación píxel a píxel. Listar los casos y compilar la página de revisión no equivale a ejecutarlos.
