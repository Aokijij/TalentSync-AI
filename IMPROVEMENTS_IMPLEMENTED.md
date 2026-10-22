# Mejoras de preparación y consistencia

## Espacio independiente para retos

- Empezar o continuar una evaluación abre un espacio dedicado en lugar de insertar el formulario debajo del catálogo. La salida regresa al catálogo y conserva el borrador sin reiniciar el tiempo.
- Navegación por preguntas con estado respondida/pendiente, opciones identificadas y selección visible, contador de tiempo y revisión de toda la entrega antes de enviarla.
- Pantalla de resultados con correcciones por pregunta y recursos de refuerzo; los errores de entrega mantienen las respuestas accesibles.
- Recuperación del borrador por cuenta e intento, primera pregunta pendiente al continuar, fechas UTC con/sin sufijo y avisos cuando el almacenamiento está bloqueado. El servidor mantiene las reglas de vencimiento, calificación y repetición.
- Pruebas de estados y recuperación en `frontend/tests/practiceWorkspace.test.mjs`; recorrido preparado en la página de revisión visual. La ejecución en navegador sigue pendiente.

## Revisión de vacantes, modales y preguntas

- Tarjetas compactas con modalidad sin cortes, tres habilidades iniciales, compatibilidad resumida y una acción principal. El icono de comparación reemplaza la fila de checkbox; el bloque de selección no aparece vacío y sus títulos se consultan desplegando la selección.
- Separación entre gestionar proceso (notas y fecha) y revisar respuestas (una pregunta por pantalla). Las valoraciones preparadas en el tablero conservan el guardado conjunto y los controles de versión existentes.
- CV por vacante en tres pasos: contenido, diseño/guardado y versiones. Experiencias y habilidades plegadas, sin una columna permanente de historial vacía. Los errores mantienen la edición; el cierre con notas pendientes se confirma dentro de la propia ventana.
- Preguntas con extractos reales de la vacante, prioridad de habilidades esenciales, nivel solicitado y puntos específicos para profundizar. Se conservan los identificadores de las preguntas para recuperar las notas; la revisión señala que la guía cambió. No se generan afirmaciones sobre la trayectoria ni puntuaciones de las respuestas privadas.

## Comparador y agenda · 22 de octubre de 2026

- Candidato → Explorar vacantes: selección de dos o tres ofertas, comparación de condiciones y habilidades del cálculo existente; filtro de condiciones diferentes. Selección por cuenta en la pestaña, sin nuevas solicitudes de compatibilidad al abrir el comparador.
- Candidato → Postulaciones: agenda ordenada de entrevistas futuras de procesos abiertos; tres citas inicialmente y expansión de las restantes. La carga de procesos ya no espera al catálogo de vacantes y un error no se presenta como una lista vacía.
- Proceso → entrevista: descarga privada de un archivo iCalendar con inicio en UTC, enlace al proceso, identificador estable y recordatorio de 30 minutos. Verifica acceso y estado actual, no incluye notas internas ni inventa duración. La importación es manual; no hay sincronización con cuentas externas.
- La edición de entrevistas convierte de UTC a hora de Colombia y vuelve a UTC sin desplazar la cita. La API normaliza los offsets antes de persistir. Los avisos diferencian programación, reprogramación y cancelación.
- `frontend/tests/comparisonAgenda.test.mjs` y `backend/tests/test_interview_calendar.py` cubren selección, datos desconocidos, horarios, permisos, estados y formato de calendario. Se amplió la página de revisión visual con comparador y agenda, conservando 24 combinaciones de tamaño/rol/tema. Su ejecución en navegador sigue pendiente.
- No requiere una migración ni nuevas dependencias. Consultar `GUIA_FUNCIONALIDADES.md` para los recorridos y límites de las funciones recientes y existentes.

## Recorridos disponibles

1. **Vacante → Prepara tu postulación → CV por vacante.** El candidato selecciona experiencias y habilidades que ya tiene guardadas, revisa el resumen y elige un diseño. Se conserva una versión independiente de su perfil, con el PDF exacto, su fecha y una huella SHA-256.
2. **Vacante → Practicar entrevista.** Preguntas relacionadas con las habilidades de la oferta, extractos reales de experiencia y respuestas estructuradas en contexto, responsabilidad, acción y resultado. Las notas se guardan en la cuenta del candidato y se pueden descargar como texto.
3. **Vacante → Usar al postularme → Enviar.** La selección se muestra junto al botón de postularse. Guardar un CV por sí solo no crea una postulación. Sin selección, se conserva una instantánea del perfil enviado, sin crear un PDF adicional.
4. **Postulaciones → Proceso → Prepara tu entrevista.** Se recuperan las notas y la información conservada de la oferta/perfil enviados, incluso si la oferta dejó de estar activa. Cuando se envió una versión del PDF, se puede consultar y descargar esa misma copia.
5. **Empresa → Perfil del candidato para la vacante → Descargar CV enviado.** Solo está disponible para una postulación accesible y con identidad visible en ese proceso. Las respuestas privadas de práctica no aparecen en la vista de empresa ni en su línea de tiempo.

Las ofertas externas permiten preparar y descargar un CV; el envío sigue ocurriendo en su portal. No se automatiza una postulación externa ni se afirma que su portal recibió un documento.

## Garantías y límites

- Guardar una versión no modifica la experiencia, habilidades, resumen ni diseño del perfil principal.
- Las habilidades y experiencias seleccionadas se validan contra el perfil. El resumen es editable y el candidato debe revisar sus afirmaciones. No se generan logros, cifras o credenciales.
- Un cambio del perfil o de los requisitos durante la edición impide guardar silenciosamente un CV basado en información desactualizada.
- La clave de solicitud evita duplicar una versión si se repite la misma petición. Un reintento de postulación devuelve la ya existente, incluso si la oferta se cerró después de confirmar el primer envío.
- Dos ventanas no pueden sobrescribir las notas guardadas sin detectar el conflicto. Ante un error, el formulario mantiene las respuestas para copiarlas o descargarlas.
- Una revisión de respuesta comprueba apartados completos; no puntúa la empleabilidad ni verifica que una afirmación sea verdadera.
- Hasta 30 versiones por candidato y vacante; máximo 5 MB por PDF. Los PDF se guardan en la base y deben incluirse en su política de copias de seguridad y conservación.
- Las versiones guardan los datos personales que el candidato había decidido hacer visibles al crearlas. Un PDF ya enviado conserva su contenido; cambiar después el perfil no reescribe ese archivo.
- La migración aditiva `0043_resume_versions` crea el almacén. No transforma ni elimina postulaciones o versiones históricas.

## Referencias y decisiones

- [AI Job Search](https://github.com/ai-job-search-dev/ai-job-search): inspiración para preparación por vacante, conservación del documento enviado y ejemplos STAR. La implementación usa la arquitectura de TalentSync y no requiere Claude Code ni ejecutar ese repositorio.
- [Taste-Skill](https://github.com/Leonxlnx/taste-skill): pautas de densidad, jerarquía y componentes, recogidas en `DESIGN.md`.
- [Breken](https://breken.ai/): referencia para escenarios de fallos. Se añadieron pruebas locales de reintentos, cambios simultáneos, oferta caducada y acceso cruzado. Esto no es una integración con Breken ni una validación de sus promesas comerciales.
- [ECC](https://github.com/affaan-m/ECC): se sigue la idea de cambios verificables con regresiones y revisión. No se instalaron sus automatizaciones globales.
- [Prompts.chat](https://github.com/f/prompts.chat): referencia de plantillas; las preguntas de esta función se construyen con los requisitos y hechos guardados. No hay dependencia de su servicio.
- Figma queda como posible fuente futura de componentes aprobados; no se ha conectado una cuenta ni existe un archivo de marca suministrado para sincronizar.
- Se conservan Lucide y las fuentes actuales. GSAP, Spline, escenas 3D y recursos de galerías no son necesarios para estos recorridos. Las transiciones simples usan CSS y respetan movimiento reducido.

## Verificación

- `backend/tests/test_application_preparation.py`: persistencia del PDF, permisos, integridad del documento, instantáneas, reintentos, datos obsoletos y notas privadas.
- `frontend/tests/applicationPreparation.test.mjs`: estados del editor, práctica, documento enviado y exportación de notas.
- `frontend/quality/specs/layout.spec.js`: 24 escenarios preparados de interfaz con componentes reales y datos ficticios. El listado/compilación y la ejecución de navegador son verificaciones distintas; consultar el informe de cada ejecución antes de afirmar que las capturas están revisadas.
- La suite general y las migraciones siguen formando parte del CI. Estas pruebas no prueban producción ni sustituyen un piloto con usuarios reales.
