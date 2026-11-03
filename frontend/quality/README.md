# Pruebas de interfaz y regresión visual

El entorno de calidad monta componentes reales con datos ficticios. Sus rutas y fixtures no forman parte de la aplicación publicada. Los recorridos funcionales simulan las API y bloquean conexiones externas según cada caso.

## Comandos

Desde `frontend/`:

| Comando | Uso |
| --- | --- |
| `npm run quality:ui` | Recorridos funcionales con Playwright. |
| `npm run quality:ui:list` | Inventario de casos sin ejecutarlos. |
| `npm run quality:ui:build` | Compilación de la página de revisión. |
| `npm run quality:visual` | Comparación con las imágenes versionadas de Windows. |
| `npm run quality:visual:update` | Actualización intencional de referencias tras revisar el diseño. |
| `npm run build:public` | Compilación del sitio informativo independiente. |
| `npx playwright test --config playwright.public.config.js` | Pruebas de la compilación pública preparada. |

Chromium se instala con `npx playwright install chromium`. Para los recorridos funcionales puede configurarse `PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH` o el archivo privado `.local/playwright-browser.json`. La regresión visual usa siempre el Chromium fijado por Playwright.

## Cobertura

Los casos revisan componentes compartidos, navegación por rol, temas, móvil y escritorio, formularios, filtros, selección, CV, aprendizaje, diálogos, estados de error y conservación de ediciones. Las pruebas de accesibilidad comprueban aspectos concretos como foco, teclado y contraste de controles; no constituyen una certificación integral.

Los escenarios se mantienen en `quality/specs/`, los casos del sitio público en `quality/public-specs/` y los datos sintéticos en los módulos del entorno de calidad. Los criterios compartidos de interfaz están en [docs/DESIGN.md](../../docs/DESIGN.md).

## Referencias visuales

`quality/baselines/win32/` contiene imágenes de componentes compartidos para los tres roles y ambos temas. Las fuentes y la representación del sistema afectan a los píxeles: CI compara esas referencias en Windows y ejecuta los recorridos funcionales en Linux.

Ante un cambio intencional:

1. Ejecutar la comparación y revisar las diferencias en `playwright-report/` y `test-results/`.
2. Inspeccionar los tamaños, roles y temas afectados.
3. Actualizar las referencias en Windows y revisar los PNG modificados en Git.
4. Repetir la comparación sin actualizar imágenes.

CI nunca actualiza las referencias. Los informes, capturas de fallos y trazas son artefactos generados y quedan fuera de Git. La comparación cubre los componentes incluidos, no todas las pantallas ni todos los navegadores.

## Separación de entornos

La configuración principal sirve la página de calidad en el puerto 4175. La configuración del sitio público usa el puerto 4186 y necesita su compilación preparada. Algunas pruebas públicas verifican también el HTML prerenderizado por `scripts/render-public-site.mjs`; seguir su flujo de preparación antes de ejecutarlas.

Las pruebas de aceptación con API y base de datos reales deben usar copias aisladas. No reutilizar cuentas ni credenciales productivas en fixtures, capturas o referencias.
