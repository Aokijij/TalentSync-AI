# Retos por habilidad y relación con Mi plan

Revisión: 24 de octubre de 2026. Implementación dentro de TalentSync, sin un proveedor adicional de evaluación.

## Colección y niveles

La colección reúne 111 formularios con nivel: básico e intermedio para 54 recorridos, y avanzado para SQL, Excel e inventarios. Cubren comunicación, servicio al cliente, ventas, gestión documental, conciliación bancaria, inventarios, evaluación del aprendizaje, diseño visual, atención administrativa en salud, SQL, Python, seguridad de aplicaciones, Excel y diseño web adaptable. La ampliación incorpora JavaScript, TypeScript, React, Git, Linux, redes, análisis de datos, Power BI, uso responsable de IA, proyectos, talento humano, marketing, CRM, emprendimiento, costes, compras, calidad, SST, recepción hotelera, registros agrícolas, control documental de obra, inglés laboral, diseño instruccional y agenda administrativa en salud. Son 48 formularios nuevos con decisiones y casos propios. Las versiones anteriores siguen disponibles para historiales e intentos iniciados; los formatos sin reemplazo conservan su acceso.

| Nivel | Preguntas por intento | Tiempo disponible | Alcance |
| --- | ---: | ---: | --- |
| Básico | 10 | 20 minutos | Conceptos, criterios y aplicación guiada |
| Intermedio | 15 | 35 minutos | Aplicación, interpretación y comprobación de un caso |
| Avanzado | 20 | 50 minutos | Restricciones, granularidad, controles y alternativas de solución |

Los niveles son editoriales y describen las tareas del formulario; no se presentan como una escala psicométrica calibrada, años de experiencia ni certificación de una profesión. En salud se evalúa exclusivamente orientación administrativa y confidencialidad, sin decisiones clínicas.

Los formularios básicos e intermedios combinan decisiones, selección múltiple, ordenación, relaciones entre conceptos y cálculos, según la selección del intento. Los avanzados actuales se concentran en decisiones de análisis y casos con restricciones. La composición se fija mediante un esquema por secciones; no se eligen preguntas arbitrarias de todo el catálogo. Cada pregunta incluye tema y explicación. Las referencias externas orientan la cobertura: las preguntas y soluciones son contenido propio de TalentSync.

## Funcionamiento y conservación

- Cada formulario tiene identificador y versión. Una revisión sustantiva debe publicar un identificador nuevo y conservar el anterior para lectura de resultados.
- Al iniciar se seleccionan las preguntas según el esquema del nivel y se guarda una copia privada. Se mezclan preguntas y opciones, remapeando las soluciones de selección, orden y relaciones. El banco original no se modifica.
- El navegador recibe el enunciado, contexto y opciones, sin soluciones. La entrega exige exactamente las respuestas del intento y se califica en el servidor. Se conservan los límites de tiempo, propiedad, entrega única y reintento a partir de 24 horas.
- Cada actividad vale un punto; selección múltiple, ordenación y relaciones requieren la solución completa. Los cálculos actuales admiten una diferencia menor de 0,001. Se aprueba desde el 80 % y la vigencia sigue siendo 180 días.
- El resultado muestra aciertos por contenido, correcciones y el nivel evaluado. Aprobar puede incorporar la habilidad mediante el comportamiento existente de evaluaciones; no cambia sus niveles declarados ni termina cursos.
- Los borradores de los cuestionarios se conservan en la pestaña del navegador cuando su almacenamiento está disponible. Salir no pausa el tiempo. El contexto de cada caso aparece también en la revisión y en el historial.

## Cursos y resultados compartidos

El catálogo relaciona las habilidades declaradas de cada curso con la habilidad evaluada y los términos relacionados explícitos de cada reto. No deduce una equivalencia a partir del título. La ficha y Mi plan presentan los retos disponibles, ordenados por habilidad y nivel, con el resultado previo cuando existe. Los cursos con la misma habilidad pueden consultar el mismo intento: no se clona una evaluación por curso.

La relación no certifica que un reto cubra todo el temario. Si no existe un reto relacionado, se informa sin asignar un ejercicio de otro tema. El candidato puede estudiar y registrar el certificado independientemente. Las prácticas específicas ya guardadas se conservan en un apartado complementario del plan; la redacción administrativa anterior sigue disponible como opción.

El catálogo de retos es independiente de los cursos: muestra 12 tarjetas por página, búsqueda por habilidad/contenido y filtros de sector y nivel. Avance y ordenación se despliegan en «Más filtros»; no se busca por curso ni por pertenencia al plan. El área elegida en cursos no limita los retos. Los retos del curso muestran seis por página. El acceso desde el curso enfoca el identificador exacto del reto, incluso si otros títulos son parecidos. El intento activo conserva un acceso para retomarlo aunque se cambie de filtro.

## Demanda observada y fuentes

Las menciones de habilidades se obtienen de ofertas activas, excluyendo demostraciones identificables. No equivalen al número de personas requeridas ni a un ranking nacional. Los formularios conservan su carácter editorial cuando no existe muestra de vacantes.

- [Future of Jobs 2025 · Skills outlook](https://www.weforum.org/publications/the-future-of-jobs-report-2025/3-skills-outlook/): tendencias internacionales y diferencias sectoriales.
- [Encuesta de demanda laboral de Bogotá 2025, publicada en abril de 2026](https://desarrolloeconomico.gov.co/asi-estan-contratando-las-empresas-en-bogota-perfiles-tecnicos-y-baja-experiencia-marcan-la-tendencia/): contexto de formación empresarial de Bogotá; no se extrapola a toda Colombia.

## Certificados y preparación de producción

El proveedor se toma del recurso en el servidor y se muestra como entidad emisora de solo lectura en el formulario. El candidato registra nombre, año, enlace HTTPS del certificado y código opcional, y confirma que recibió el documento. El enlace del curso no se utiliza como sustituto del certificado. Un error conserva la edición; cancelar cambios pide confirmación. El guardado emite un aviso y actualiza el plan y el perfil.

El radar normal, la orientación de demanda y las prioridades educativas excluyen las ofertas de demostración. La API rechaza el conjunto de demostración fuera de desarrollo. El buzón de desarrollo no tiene ruta en la compilación publicada y su API conserva la restricción de entorno y origen. Los textos del producto dejan de llamar locales a sus prácticas y proyectos. Los avisos de demostración se conservan si una herramienta de desarrollo solicita explícitamente esos datos; no se presentan como reales.

La configuración de producción rechaza excepciones de desarrollo, sesiones no seguras, origen público HTTP o de bucle local, hosts comodín, CORS HTTP y PostgreSQL sin TLS. Los scripts de creación y actualización incluyen los ajustes seguros sin ejecutarlos en esta entrega. Se conserva la configuración específica de la instalación al actualizar. La comprobación de sintaxis no sustituye un ensayo de despliegue.

Antes de publicar deben configurarse el dominio final, correo externo, callbacks OAuth y almacenamiento, y comprobarse con cuentas autorizadas. La imagen excluye bases SQLite, archivos subidos y credenciales de desarrollo; no se debe trasladar la base de demostración a producción. Esta entrega no elimina cuentas, postulaciones ni calendarios de la instalación de trabajo y no realiza despliegues.


## Catálogo editorial ampliado

La selección reúne **169 cursos de 18 proveedores**: 104 incorporaciones revisadas el 24/10/2026, incluidas 95 de Saylor University, además de FAO, OIT, ONUDI, CITB y OpenLearn. Se conserva la fecha de revisión individual de las 65 fichas anteriores; no se presenta su información como comprobada de nuevo. La revisión consulta las páginas públicas y no acredita haber completado los cursos.

Cada ficha conserva idioma, horas orientativas, condiciones de acceso, alcance del documento y fuente. Los cursos de Saylor incorporados están en inglés: el certificado de finalización gratuito se distingue de los exámenes supervisados para solicitar créditos académicos. Las duraciones editoriales de OIT y ONUDI están identificadas como estimaciones. Los contenidos normativos extranjeros no se presentan como habilitación colombiana. No se crean prácticas automáticas para rellenar cursos sin un reto pertinente.

Fuentes principales de la ampliación:

- [Saylor: catálogo](https://www.saylor.org/CourseCatalog) y [condiciones generales](https://support.saylor.org/hc/en-us/articles/23586212781844-FAQ-General); las fichas enlazan al curso individual en `learn.saylor.org`.
- [FAO: escuelas de campo](https://elearning.fao.org/course/view.php?id=1140&lang=es).
- [OIT: condiciones de trabajo en agricultura](https://www.itcilo.org/courses/improving-working-and-health-conditions-agriculture).
- [ONUDI: gestión de calidad](https://www.unido.org/learning-resources/quality-management) y [RCA/CAPA](https://www.unido.org/learning-resources/rca-and-capa).
- [CITB: cursos de obras temporales](https://www.citb.co.uk/courses-tests/ecourses).
- [OpenLearn: catálogo oficial](https://www.open.edu/openlearn/free-courses/full-catalogue).

Administración → Formación → Fuentes permite revisar e importar selecciones de hasta 50 cursos por operación. Solo los nuevos se publican si se solicita; la reimportación respeta ediciones y archivos. El límite de recursos administrables se amplía a 1.000 para permitir crecimiento del catálogo. La instalación de trabajo incorporó las 104 fichas nuevas con el importador idempotente existente; se conservaron las 65 fichas previas y los recursos manuales.

La ficha del curso muestra «Retos asignados a este curso» con habilidad, nivel y acceso al reto exacto; Mi plan añade el resultado previo. Las asociaciones usan habilidades explícitas y términos relacionados delimitados, no el título ni únicamente el sector. Un curso de turismo sostenible no recibe por su sector una prueba de recepción hotelera. El catálogo público de retos no incluye identificadores de cursos relacionados ni soluciones.

El formulario de certificado agrupa nombre y año, muestra el emisor en una franja de solo lectura, reserva un campo ancho para el enlace y oculta el código opcional hasta solicitarlo. Guardar y cancelar están en un pie común; un error conserva los datos y descartar una edición requiere confirmación. Las tarjetas de retos tienen acciones alineadas, contenidos desplegables y una presentación adaptada a móvil y ambos temas.


## Simplificación del curso y segunda ampliación — 24/10/2026

Los cursos muestran únicamente sus retos por habilidad. El seguimiento deja de abrir prácticas complementarias antiguas; la ficha del curso ya no presenta sus actividades como contenido del proveedor. Los resultados históricos y sus datos se conservan. Las prácticas internas y los recursos con proveedor ficticio se retiran del catálogo y no admiten planes nuevos. Un plan antiguo de un recurso interno muestra su retirada y permite liberarlo, sin presentar la práctica como un curso vigente.

Las fichas de YouTube usan el nombre de la plataforma, con títulos editoriales más directos que identifican la formación en vídeo. Las tarjetas del catálogo presentan título, proveedor, una descripción breve, duración, coste, idioma y hasta tres habilidades. Temario, requisitos y condiciones se consultan en «Ver detalle», también disponible como «Detalle del curso» dentro del plan. El botón para aportar certificado utiliza la acción principal del panel.

Se añaden **32 formularios para 16 habilidades**: HTML, CSS, accesibilidad web, C#, Java, pruebas de software, API REST, Docker, Word, presentaciones, comercio electrónico, gestión ambiental, planificación del mantenimiento, atención en restaurantes, logística de transporte y protección de datos. Las tarjetas indican la habilidad practicada; las de cada curso muestran las habilidades de su ficha que justifican esa asignación. La accesibilidad genérica deja de asignar por sí sola un reto de diseño visual.

La selección editorial suma **228 cursos**, con **59 rutas nuevas en español** de programación, datos, seguridad, contabilidad, ventas, logística, proyectos y educación. La selección utiliza el [catálogo oficial en español de Microsoft Learn](https://learn.microsoft.com/es-es/training/support/catalog-api-developer-reference), comprueba el idioma comunicado por la fuente y conserva títulos de módulos, duración, nivel y condiciones. Se eliminaron tres coincidencias con fichas anteriores antes de importar. El contenido gratuito se distingue de las licencias, servicios o exámenes que podrían tener coste. Las rutas no se presentan como certificados profesionales.

El radar de desarrollo vuelve a incluir las ofertas de demostración usadas para recorrer los filtros; se identifica como «Datos de demostración» y no expone el identificador interno de la fuente. Producción sigue excluyendo esos registros y rechaza el conjunto de demostración. No se fabrican resultados para una consulta sin ofertas reales. La comprobación con el área de software, nivel junior y Medellín devuelve 30 ofertas de demostración en la base de trabajo.


## Recorrido de finalización del curso — 24/10/2026

Mi plan distingue En marcha y Finalizados con controles agrupados. Durante el curso muestra el acceso al proveedor, su detalle y los retos por habilidad. No presenta el formulario del certificado hasta que el usuario registra la finalización. La API también exige ese estado para aportar o editar el certificado. Retomar conserva documentos, habilidades y resultados.

Al terminar, la vista cambia: confirma la formación finalizada, prioriza el documento si el proveedor anuncia certificación y permite elegir las habilidades aprendidas para incorporarlas al perfil sin exigir certificado. Los cursos sin certificado anunciado presentan un cierre propio. Las habilidades se registran como declaradas, requieren selección y confirmación, no aceptan habilidades ajenas al curso y no generan un resultado validado. Las habilidades ya presentes no se duplican y el máximo del perfil sigue siendo cien.

Los retos siguen disponibles en un apartado secundario desplegable. Las prácticas antiguas salen de las pestañas principales de Mis resultados y permanecen en un historial de solo lectura con búsqueda, paginación y correcciones. No se borran intentos ni se vuelven a ofrecer como prácticas de los cursos actuales.

Las acciones de certificados tienen una sola prioridad visual: Ver certificado, Editar datos como secundaria y acceso al apartado correcto del perfil. La barra del perfil agrupa documentos y edición, mantiene textos en móvil y diferencia Quitar formación como acción de retirada del borrador.

Las ofertas de TalentSync muestran Nivel A–D de claridad en recomendaciones, tarjetas y detalle. Usan rating y rating_scale de la misma revisión del servidor, independientes del criterio de publicación y de la compatibilidad. La explicación describe los rangos, su alcance y la influencia existente en Recomendadas entre ofertas con afinidad cercana, manteniendo la prioridad de confianza empresarial. No se evalúan ofertas externas ni se garantiza la posición del anuncio.

Verificación: 235 pruebas de regresión de API y 241 de frontend aprobadas; 132 recorridos de interfaz aprobados y las 36 capturas compartidas comparadas sin modificar sus referencias. Tras corregir el retorno a Finalizados se repitieron los 18 recorridos de formación, incluidos móvil/escritorio, ambos temas, errores, selección parcial de habilidades, retorno al plan y conservación al retomar. ESLint, Ruff y compilación de producción correctos. El backend se reinició y respondió 200 a readiness; sus ofertas incluyen los cuatro rangos canónicos. Esta revisión no despliega la plataforma ni modifica los documentos históricos.
