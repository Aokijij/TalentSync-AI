# Retos por habilidad y relación con Mi plan

Revisión: 24 de octubre de 2026. Implementación dentro de TalentSync, sin un proveedor adicional de evaluación.

## Colección y niveles

Se añaden 31 formularios versionados: básico e intermedio para 14 recorridos, y avanzado para SQL, Excel e inventarios. Cubren comunicación, servicio al cliente, ventas, gestión documental, conciliación bancaria, inventarios, evaluación del aprendizaje, diseño visual, atención administrativa en salud, SQL, Python, seguridad de aplicaciones, Excel y diseño web adaptable. Las versiones anteriores siguen disponibles para historiales e intentos iniciados; los formatos sin reemplazo conservan su acceso.

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

El catálogo de retos muestra 12 tarjetas por página, búsqueda por contenido y filtros de nivel, avance y relación con Mi plan. Los retos del curso muestran seis por página. El acceso desde el curso enfoca el identificador exacto del reto, incluso si otros títulos son parecidos. El intento activo conserva un acceso para retomarlo aunque se cambie de filtro.

## Demanda observada y fuentes

Las menciones de habilidades se obtienen de ofertas activas, excluyendo demostraciones identificables. No equivalen al número de personas requeridas ni a un ranking nacional. Los formularios conservan su carácter editorial cuando no existe muestra de vacantes.

- [Future of Jobs 2025 · Skills outlook](https://www.weforum.org/publications/the-future-of-jobs-report-2025/3-skills-outlook/): tendencias internacionales y diferencias sectoriales.
- [Encuesta de demanda laboral de Bogotá 2025, publicada en abril de 2026](https://desarrolloeconomico.gov.co/asi-estan-contratando-las-empresas-en-bogota-perfiles-tecnicos-y-baja-experiencia-marcan-la-tendencia/): contexto de formación empresarial de Bogotá; no se extrapola a toda Colombia.

## Certificados y preparación de producción

El proveedor se toma del recurso en el servidor y se muestra como entidad emisora de solo lectura en el formulario. El candidato registra nombre, año, enlace HTTPS del certificado y código opcional, y confirma que recibió el documento. El enlace del curso no se utiliza como sustituto del certificado. Un error conserva la edición; cancelar cambios pide confirmación. El guardado emite un aviso y actualiza el plan y el perfil.

El radar normal, la orientación de demanda y las prioridades educativas excluyen las ofertas de demostración. La API rechaza el conjunto de demostración fuera de desarrollo. El buzón de desarrollo no tiene ruta en la compilación publicada y su API conserva la restricción de entorno y origen. Los textos del producto dejan de llamar locales a sus prácticas y proyectos. Los avisos de demostración se conservan si una herramienta de desarrollo solicita explícitamente esos datos; no se presentan como reales.

La configuración de producción rechaza excepciones de desarrollo, sesiones no seguras, origen público HTTP o de bucle local, hosts comodín, CORS HTTP y PostgreSQL sin TLS. Los scripts de creación y actualización incluyen los ajustes seguros sin ejecutarlos en esta entrega. Se conserva la configuración específica de la instalación al actualizar. La comprobación de sintaxis no sustituye un ensayo de despliegue.

Antes de publicar deben configurarse el dominio final, correo externo, callbacks OAuth y almacenamiento, y comprobarse con cuentas autorizadas. La imagen excluye bases SQLite, archivos subidos y credenciales de desarrollo; no se debe trasladar la base de demostración a producción. Esta entrega no elimina cuentas, postulaciones ni calendarios de la instalación de trabajo y no realiza despliegues.
