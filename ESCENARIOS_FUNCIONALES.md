# Escenarios funcionales para revisión local

Preparación: `backend/.venv/Scripts/python.exe -X utf8 scripts/local.py seed-scenarios`.

La carga crea un conjunto conectado de **26 cuentas nuevas**, **8 empresas**,
**26 vacantes**, **34 postulaciones** y **5 incidencias**, además de recursos,
planes, resultados, evidencias, seguidores, avisos e invitaciones. Todos son ficticios.
No se cambian cuentas, contraseñas, perfiles ni vacantes anteriores.

Los accesos y el recorrido detallado están en `.local/escenarios/GUIA_ESCENARIOS.md`.
Las contraseñas se generan por cuenta y permanecen fuera de Git, en esa guía y
`accounts.json`. La guía permite entrar por el portal correcto y explica qué
probar con cada cuenta. El administrador configura MFA en su primer ingreso.

| Rol | Cuentas y estados preparados |
| --- | --- |
| Candidato | Nuevo, correo pendiente, senior, junior, cambio de área, aprendizaje, plan lleno, privacidad, historial, condiciones imprescindibles, logística y diseño. |
| Empresa | Verificada con actividad, verificada con confianza reducida, verificada vacía, sin solicitud, en revisión, correcciones solicitadas, rechazada y suspendida. |
| Equipo empresarial | Reclutador, entrevistador con asignación, acceso retirado, invitación pendiente e invitación vencida. |
| Administrador | Cuenta nueva con todos los permisos administrativos; cola empresarial, revisión de incidencias, catálogo, auditoría y laboratorio. |

El candidato de historial tiene los nueve estados de postulación, además de
retirada, cierre por plazo y cierre de vacante. Hay selección anónima y visible,
etapas personalizadas, preguntas y respuestas, idiomas, formación y brechas.
El candidato de aprendizaje tiene un borrador, una práctica publicada, un recurso
sin comenzar, una evaluación aprobada, otra no aprobada, una acreditación caducada
y un reto SQL aprobado mediante el ejecutor real sobre datos sintéticos.

Los resultados precargados son **simulaciones**, no acreditaciones de personas
reales. Las prácticas se crean mediante las mismas validaciones del producto;
la carga usa una única transacción. Las cuentas de example.com se excluyen del
entrenamiento, por lo que el laboratorio sigue mostrando honestamente la falta
de muestra real. No se fabrican modelos entrenados ni servicios conectados.

Los archivos `catalogo-ejemplo.json`, `vacantes-ejemplo.csv`,
`vacantes-ejemplo.xlsx` y `vacantes-con-error.csv` permiten probar importación,
actualización sin duplicados y errores por fila desde administración. Los enlaces
de estos recursos/ofertas son ilustrativos y se identifican como ficticios.

Repetir la preparación no duplica ni restablece datos editados. Se conserva una
copia anterior en `.local/before-functional-scenarios.sqlite3`; no se restaura
automáticamente. Los plazos son relativos a la creación y las invitaciones
pendientes vencen en tres días. Los retos nuevos se inician al abrirlos.

Los recorridos que requieren OAuth, SSO, SMTP externo, API de vacantes o registros
oficiales necesitan configuración y credenciales reales. La guía diferencia
esas dependencias de las funciones disponibles localmente. No se modifican las
protecciones de seguridad para permitir el acceso a escenarios restringidos.
