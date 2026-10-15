# Datos locales para pruebas de contratación

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
