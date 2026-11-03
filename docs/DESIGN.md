# Criterios de interfaz

La interfaz acompaña tres tareas: encontrar oportunidades, seleccionar talento y administrar la plataforma. La identidad usa azul para candidatos, violeta para empresas y ámbar para administración, con temas claro y oscuro.

## Componentes compartidos

- `frontend/src/styles/design-system.css` define espaciado, radios, tipografía y geometría de controles.
- `PageHeader` presenta el título, una descripción breve y las acciones principales.
- `Panel`, `PanelActions`, `WorkspaceTabs` e `InlineNotice` comparten la estructura de contenido.
- Los iconos pertenecen a Lucide y acompañan etiquetas comprensibles.
- Los colores de acción provienen de las variables del tema y el rol; el texto mantiene contraste en ambos temas.

## Lectura y acciones

- Una pantalla presenta primero la tarea y el siguiente paso más frecuente.
- Los contadores corresponden a los datos mostrados; un valor desconocido conserva ese estado.
- Las secciones opcionales extensas se abren mediante una acción explícita.
- Los errores aparecen en el bloque afectado, permiten reintentar y conservan las ediciones.
- Perfil actual, CV guardado y documento enviado son elementos distintos y se identifican como tales.
- Los resultados de prácticas conservan su alcance; no se presentan como acreditaciones profesionales.

## Adaptación y accesibilidad

- Los controles principales tienen al menos 44 px de altura y foco visible.
- Las columnas se apilan en pantallas estrechas y las pestañas pueden desplazarse dentro de su fila.
- Los formularios tienen etiquetas y errores asociados; los diálogos gestionan título y recuperación del foco.
- Las pestañas permiten flechas, Home y End. El contenido incluye un acceso para saltar la navegación.
- El color se acompaña de texto o iconos; las animaciones respetan `prefers-reduced-motion`.

## Verificación

La revisión combina pruebas de lógica, recorridos de teclado y comprobación visual de los tres roles, ambos temas y varios tamaños de pantalla. Los casos usan componentes reales y datos ficticios en `frontend/quality/`.

Las referencias visuales están versionadas y sus cambios deben revisarse. Consultar el [flujo de revisión de interfaz](../frontend/quality/README.md). Las pruebas existentes cubren recorridos concretos; no equivalen a una certificación de accesibilidad de toda la plataforma.
