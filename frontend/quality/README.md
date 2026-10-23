# Comprobación de interfaz y regresión visual

La página de revisión usa componentes reales y datos ficticios. No forma parte de la compilación publicada. Los recorridos bloquean peticiones externas y las respuestas API del perfil se simulan; no modifican cuentas de trabajo.

## Recorridos funcionales

`npm run quality:ui` comprueba navegación, modales, filtros, retos, CV, confirmaciones, avisos y conservación de ediciones. Puede usar el Chromium personal configurado en `.local/playwright-browser.json`. Estos recorridos también se ejecutan en Linux en CI.

## Imágenes de referencia

`npm run quality:visual` compara filtros, tarjetas, estados de integraciones, avisos y confirmaciones con 36 PNG versionados: candidato, empresa y administración, temas claro/oscuro, 360 y 1280 píxeles. Usa exclusivamente el Chromium fijado en package-lock/Playwright y referencias de Windows. La preferencia del navegador personal no interviene. Instalarlo con `npx playwright install chromium`.

El trabajo `visual-regression` de CI usa Windows y ese mismo navegador. Linux conserva las pruebas funcionales; no se comparan píxeles entre sistemas operativos con fuentes diferentes. La tolerancia es 0,1 % de píxeles, con umbral de color 0,15. No se comparan datos de cuentas ni fechas variables.

Si un diseño cambia intencionadamente:

1. Ejecutar la comparación y revisar las diferencias en `playwright-report/index.html` y `test-results/`.
2. Comprobar visualmente escritorio, móvil, roles y temas afectados.
3. Solo entonces ejecutar `npm run quality:visual:update` en Windows con el navegador fijado y revisar los PNG del diff de Git.
4. Ejecutar de nuevo `npm run quality:visual` sin actualizar imágenes.

CI nunca actualiza las referencias. Conserva el informe y las diferencias como artefactos. Las imágenes cubren los componentes compartidos; no equivalen a una referencia de cada pantalla, estado o navegador de toda la plataforma.
