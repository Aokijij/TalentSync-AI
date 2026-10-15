# Datos locales para pruebas de contratación

Para **actualizar el conjunto existente conservando las postulaciones**, usa
`backend/.venv/Scripts/python.exe scripts/local.py enrich-realistic`.
La actualización guarda una copia SQLite consistente y enriquece las 360 ofertas
en su lugar, sin cambiar sus ID, propietarios, cuentas, contraseñas, etapas ni
historial. Conserva ofertas editadas en la aplicación y respuestas ya existentes.
Solo añade respuestas de ejemplo a postulaciones de los perfiles de prueba.
Es idempotente y valida la misma ruta aislada que el generador original.

La ampliación contiene 161 habilidades, cinco niveles y 168 perfiles adicionales
(273 de prueba en total). Incluye grupos comparables de desarrollo inicial,
intermedio, senior y liderazgo en Medellín, salud junior en Bogotá, logística
intermedia en Medellín y ventas junior en Cali. Las tareas, herramientas, dos
resultados medibles y tres preguntas de cada oferta dependen del cargo, la
especialidad y un caso empresarial local. Todas tienen condiciones y proceso
completos; las diferencias de redacción permiten revisar su claridad.
El generador usa un mínimo fijo de 2.000.000 COP para los puestos de prueba a
tiempo completo. Es una decisión del conjunto sintético, no una referencia legal
ni una estadística salarial. La actualización corrige también los registros v2
generados con importes menores, sin sobrescribir ofertas editadas posteriormente.

El radar comienza con filtros editables sugeridos por el perfil; el nivel se
orienta por los meses registrados y no acredita seniority. Muestra todas las
habilidades ordenadas por demanda, con buscador y páginas de cinco. Los salarios
individuales están disponibles con cualquier combinación de filtros. Las
medianas conservan sus umbrales y condiciones comparables; no se mezclan cargos
para llenar una búsqueda vacía.

`backend/.venv/Scripts/python.exe scripts/local.py reset-realistic` reemplaza
vacantes, empresas y candidatos de prueba exclusivamente en
`.local/talentsync.sqlite3`. El comando valida la ruta exacta y el entorno de
desarrollo, realiza una copia SQLite consistente en `.local/backups/`, conserva
todos los administradores y los candidatos con correos personales, y elimina
las filas dependientes de las entidades retiradas en una sola transacción.
Verifica integridad referencial y conservación de los registros de administrador
antes de confirmar los cambios. No modifica archivos de configuración, claves,
MFA ni contraseñas de las cuentas conservadas.

Genera 30 empresas, 360 vacantes activas, 105 candidatos con nombre y perfil,
y 720 postulaciones distribuidas entre recepción, revisión, entrevista,
contratación y rechazo. Hay 12 ciudades y más de 12 sectores. Cada empresa tiene
ofertas completas y otras que necesitan mejorar condiciones o proceso, para
probar la revisión de calidad. Las vacantes de menor calidad se incluyen como
datos históricos de prueba; no se relajan las reglas para publicar nuevas ofertas.

Las cuentas nuevas tienen correos reservados bajo `example.com`. Los accesos seleccionados
y una contraseña aleatoria se escriben solo en los archivos ignorados
`.local/ACCESOS-PRUEBAS.md` y `.local/realistic-accounts.json`. Nunca se envían
correos a empresas. Las cuentas de empresa conservan la exigencia de MFA de la
configuración local. El comando vuelve a reemplazar el conjunto cuando se ejecuta
de nuevo: no acumula duplicados y genera una nueva copia y contraseña.

Los nombres conocidos sirven como referencias visuales para pruebas. Se han
consultado las páginas corporativas de [Grupo Éxito](https://www.grupoexito.com.co/es/negocios-marcas),
[Bancolombia](https://www.grupobancolombia.com/corporativo/conocenos) y
[Grupo Nutresa](https://gruponutresa.com/). Los cargos, salarios, perfiles,
credenciales, resultados y procesos son inventados y no representan publicaciones
oficiales, empleados reales ni evaluaciones de esas empresas.

El radar tiene una sola interfaz que consulta las vacantes de la plataforma.
Los datos locales llevan `source_name=local-realistic` y los perfiles,
`preferences.local_fixture=true`. Solo el servidor de desarrollo puede incluirlos
en los agregados; el cliente no puede activar esta autorización. En producción
quedan excluidos incluso cuando un perfil de prueba tiene correo verificado.
Una nota compacta identifica los datos locales. Se mantiene el mínimo de 20
participantes para comparar perfiles y 20 empresas distintas por grupo salarial,
sin mezclar contrato, modalidad, jornada u horas. Tres grupos tienen 30 empresas
y 30 perfiles: frontend junior en Medellín, datos intermedio en Bogotá y
contabilidad junior en Bogotá. Los accesos del radar se calculan a partir de las
ofertas disponibles, sin inventar resultados para búsquedas sin coincidencias.

La lista de postulados incluye a todas las personas del proceso, cualquiera sea
su compatibilidad. El umbral del 80% se aplica únicamente a las invitaciones.
La contratación anónima sigue disponible; los nuevos datos usan nombres visibles
porque las vacantes de prueba tienen esa opción desactivada.

## Carga de datos y concurrencia

SQLite de desarrollo usa WAL para que las consultas no bloqueen el cierre de
sesión ni las escrituras breves. Las colecciones necesarias para listar las
vacantes se cargan por lotes. Al guardar puntuaciones se conserva el estado ya
cargado durante esa operación, evitando recargar cada vacante al serializar.

Las pantallas del candidato usan `/recommendations/me/jobs/batch`: reciben las
compatibilidades disponibles y el número pendiente. Cada solicitud calcula hasta
12 vacantes por defecto (máximo 24), dando prioridad a habilidades relacionadas.
El cliente muestra perfil, postulaciones y vacantes en cuanto llega cada respuesta;
continúa con lotes pequeños mientras la vista esté abierta. Las vistas simultáneas
comparten solicitudes por cuenta. Salir de la pantalla detiene su actualización;
cerrar sesión cancela las solicitudes y descarta respuestas tardías.

Las puntuaciones se reutilizan mientras su versión de entrada sea igual. Cambios
en habilidades, experiencia, requisitos, modelo o mes de referencia invalidan
los resultados afectados. Editar solo el diseño del CV o transcurrir diez minutos
no obliga a repetir toda la inferencia. El endpoint de lista completa permanece
disponible para clientes anteriores. La lista de postulados calcula únicamente
las personas que pertenecen al proceso.

Los idiomas usan una identidad canónica compartida por la API, las puntuaciones
y sus explicaciones: «English», «Inglés» e «inglés» coinciden. La versión v10
invalida puntuaciones anteriores. Los campos académicos aceptados son alternativas
y el nivel explícito del estudio tiene prioridad sobre su nombre.
Con estudios estructurados, el cargo declarado no sustituye el título y un
grado de otra área no eleva el nivel académico solicitado.

Cambiar salario, ciudad, modalidad o sus casillas imprescindibles actualiza los
filtros y su explicación sin recalcular afinidad profesional. Cambiar el sector
preferido sí invalida la puntuación porque participa en la señal de contexto.
La búsqueda de cursos evalúa únicamente la vacante seleccionada y hasta diez
proyecciones. El contador de otras ofertas usa requisitos relacionados, sin
presentarlo como una mejora calculada de compatibilidad. Las pantallas de
aprendizaje y actualización progresiva conservan resultados disponibles y
permiten reintentar cuando una sección falla.
