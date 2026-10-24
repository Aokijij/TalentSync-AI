# Cierre funcional local: prioridades 1 a 9

Revisión del 23 de octubre de 2026. El paso 10, preparación y comprobación de producción, continúa separado.

## Comprobaciones aprobadas

- [x] Componentes compartidos para candidato, empresa y administración: campos, botones, pestañas, tarjetas, avisos y confirmaciones.
- [x] Landing pública con dos caminos de registro, acceso a cuentas existentes y demostración identificada como ficticia. La sesión iniciada conserva su entrada al panel del rol.
- [x] Bienvenida del candidato con preferencias guardadas, campos opcionales y salida hacia ofertas sin escribir datos. La modalidad no se selecciona por defecto.
- [x] Guardado de preferencias con lectura reciente del perfil, conservación de campos no editados, bloqueo durante el envío, error visible y reintento. Se confirma salir sin guardar desde las acciones de la bienvenida.
- [x] Acceso al control existente de CV con desplazamiento y foco, sin forzar la edición completa del perfil.
- [x] Bienvenida empresarial con solicitud, revisión, correcciones, aprobación y suspensión diferenciadas. La exención de verificación obligatoria no se presenta como una aprobación administrativa.
- [x] Accesos al formulario de verificación, seguridad y preparación de vacantes. Los enlaces de creación abren una oferta nueva y los borradores conservan el identificador de la vacante elegida.
- [x] Límites de navegación por autenticación y rol, junto con pruebas API de organizaciones y calidad. El código de autorización del servidor se conserva.
- [x] Móvil y escritorio, temas claro/oscuro, teclado y texto al 200 % en las nuevas entradas. Revisión manual de capturas de los tres recorridos.
- [x] Comparación de las 36 referencias visuales de componentes compartidos, sin actualizar imágenes para ocultar diferencias.
- [x] Regresiones de postulaciones, entrevistas, plazos, CV, cuentas, filtros, estados vacíos y listas voluminosas mediante las pruebas existentes.
- [x] Análisis ESLint, pruebas unitarias y compilación de la aplicación.

## Evidencia reproducible

| Comprobación | Resultado |
| --- | --- |
| Pruebas unitarias frontend | 236 aprobadas |
| API: cuentas, organizaciones, ofertas y perfil | 53 aprobadas, bases descartables |
| Suite completa de interfaz | 109 aprobadas; 12 casos de imágenes reservados para la ejecución visual |
| Revisión final de entrada y enlaces empresariales | 18 aprobadas; incluye los 17 recorridos de entrada de la suite completa |
| Comparación visual compartida | 36 capturas aprobadas en 12 casos, referencias sin cambios |

Comandos de interfaz: `npm run lint`, `npm test`, `npm run build`, `npm run quality:ui`, `npx playwright test entry.spec.js` y `npm run quality:visual`, desde `frontend/`. La comparación visual se registra junto al cierre en `REVISION_PLATAFORMA.md`.

Los informes privados están en `.local/entry-*.log` y las capturas nuevas, en `.local/entry-review/`. Las pruebas de interfaz interceptan las API y bloquean servicios externos; las pruebas backend usan bases aisladas. Estas comprobaciones se ejecutan sin decisiones sobre candidaturas reales, conexiones externas o escrituras en calendarios personales.

La validación cubre los recorridos descritos y los controles compartidos. No acredita conformidad completa de accesibilidad, rendimiento a escala ni operación de producción. Esta entrega no despliega servicios ni modifica bases de trabajo o migraciones.

## Ampliación de guía y aprendizaje

- [x] Guía por funciones desde bienvenida y menú, con pasos, límites, accesos directos y temas filtrados por permisos de equipo.
- [x] Inicio público con funcionalidades por rol y diferencias del recorrido basadas en comportamiento implementado.
- [x] Curso, práctica opcional y certificado independientes. El catálogo permite asociar actividades revisadas o redactar otras; los intentos conservan sus preguntas y soluciones privadas.
- [x] Resultados por categorías, búsqueda y paginación; sin calificaciones para finalizaciones declaradas o certificados aportados.
- [x] Un único aviso al añadir un recurso, con acceso a Mi plan y recuperación tras errores.

Validación posterior: 238 pruebas frontend, 159 pruebas backend de aprendizaje y fuentes, 118 recorridos completos de interfaz y 36 capturas compartidas en 12 casos. ESLint, Ruff y compilación aprobados. Referencias visuales sin cambios. Ver `REVISION_PLATAFORMA.md` y `.local/learning-guide-*.log`. Esta ampliación añade endpoints de seguimiento y edición del catálogo, utiliza los campos JSON existentes y conserva pendiente el paso de producción.

## Retos por habilidad, Mi plan y certificados

- [x] 31 retos versionados con niveles y 10/15/20 preguntas; esquemas de selección, soluciones privadas y conservación de intentos.
- [x] Relación de cursos y retos por habilidades, con resultado compartido entre cursos y avance de formación independiente.
- [x] Catálogo paginado con búsqueda, nivel, avance, relación con Mi plan y acceso al intento activo.
- [x] Diseño de planes y certificado con proveedor, enlace del documento, guardado, error y reintento.
- [x] Estadísticas sin ofertas sintéticas en el recorrido normal, herramientas de desarrollo restringidas y configuración de producción sin excepciones locales.

Verificación del 24/10/2026: 239 pruebas frontend, 238 backend y 122 recorridos de interfaz. ESLint, Ruff, compilación y sintaxis de los scripts de despliegue aprobados. Las comprobaciones de entorno no equivalen a un despliegue: dominio, correo, OAuth, almacenamiento y operación con usuarios autorizados se verifican al preparar la instalación pública. No se han trasladado datos de demostración ni modificado calendarios personales. Ver `RETOS_APRENDIZAJE.md` y `.local/challenge-paths-*.log`.
