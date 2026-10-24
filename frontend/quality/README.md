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

## Datos de cuenta y operación

`/quality/?auth=register` y `?auth=login` montan las pantallas reales con proveedores
sintéticos habilitados; `?auth=accounts` muestra vinculación. `providers=off`
comprueba la configuración ausente. `social-access.spec.js` revisa móvil/escritorio,
ambos temas, errores de proveedor, redirección con almacenamiento bloqueado y
separación del registro empresarial. Las API se interceptan: no abre Google,
GitHub o LinkedIn ni crea cuentas externas.

`/quality/?controls=1&role=candidate&theme=dark` monta los componentes reales de
portabilidad, Google Calendar y diagnóstico operativo con las mismas tres hojas
de estilo globales de la aplicación. La suite intercepta las API con datos
sintéticos; comprueba descarga, cancelación de borrado, confirmación, sincronizar,
desconectar y estados de entrega, en móvil/escritorio y ambos temas. No conecta
Google ni envía correos. Las capturas de revisión se guardan en `.local/operations/`.


## Cierre visual y accesibilidad de los controles

`design-closure.spec.js` monta el layout real en candidato, empresa y administración. Comprueba los colores de texto y fondo de botones y placeholders, los bordes de los campos estándar, la ampliación del texto al 200 %, la navegación de pestañas con teclado, el salto al contenido y el foco del menú móvil. También verifica error y reintento de una confirmación asíncrona sin doble envío, y la asociación de errores a los campos de acceso. Estos casos usan datos sintéticos y no acreditan conformidad completa de accesibilidad de todas las pantallas.

Los criterios para mantener componentes y textos consistentes están en [DISENO_INTERFAZ](../../DISENO_INTERFAZ.md). Las capturas locales de la revisión se guardan en `.local/design-closure-review/`.

## Landing y bienvenida por rol

`entry.spec.js` monta `AppRoutes` con los componentes y permisos de navegación reales, autenticación sintética y todas las peticiones externas bloqueadas. Revisa landing, bienvenida de candidato y de empresa a 360/1280 px, ambos temas y texto al 200 %. Incluye conservación de datos tras un fallo, lectura reciente antes de reemplazar el perfil, continuar sin guardar, acceso al control de CV y separación de revisión, aprobación, exención y suspensión. Las capturas se guardan en `.local/entry-review/`; no se incluyen en el sitio publicado. Las pruebas backend de API, organizaciones, calidad y perfil utilizan bases descartables.

## Guía completa y aprendizaje independiente

`guide-learning.spec.js` usa las rutas y componentes reales con API sintética. Comprueba la guía por rol y permisos del entrevistador, los apartados públicos de funcionalidades, un único aviso al añadir recursos, error y reintento, el seguimiento manual de un curso sin práctica asociada y las categorías, búsqueda y paginación de resultados. Revisa 360/1280 px, ambos temas y texto al 200 %. El recorrido administrativo permite revisar una práctica del catálogo y redactar otra, comprobando el contenido enviado y un solo aviso de guardado. Las capturas están en `.local/learning-guide-review/`.

Las pruebas backend `test_course_plan_separation.py` comprueban propiedad, versión, separación de curso/práctica/certificado, privacidad de soluciones y conservación de intentos ante cambios del catálogo. Las familias existentes de cursos, recursos, fuentes y recorridos conservan sus comprobaciones con bases descartables.

La ampliación de `guide-learning.spec.js` incluye 31 retos sintéticos, paginación, búsqueda vacía, niveles, relación con el plan, apertura exacta desde un curso y vuelta al mismo curso. También comprueba el proveedor de solo lectura, enlace del certificado, error con edición conservada, reintento y un solo aviso. Las capturas se guardan en `.local/challenge-paths-review/`. `test_challenge_tracks.py` verifica los esquemas de nivel, soluciones privadas, banco sin mutaciones, historial compartido entre cursos y límites de configuración de producción. Ver [RETOS_APRENDIZAJE](../../RETOS_APRENDIZAJE.md).
