# Funciones locales completadas — 9 de octubre de 2026

La revisión usa exclusivamente `.local/talentsync.sqlite3`, archivos y correo
locales. No se activaron proveedores externos, servicios facturables ni despliegues.

## Funciones añadidas

- Verificación de empresas: búsqueda y filtros completos desde el servidor,
  cinco organizaciones por página y contadores globales por estado.
- Comportamiento empresarial: seis empresas por página, búsqueda completa,
  filtros por valoración e incidencias; métricas agregadas en SQL sin cargar
  todos los procesos de todas las empresas. Se conserva el cálculo de reputación.
- Equipo: seis integrantes o invitaciones por página, búsqueda por nombre,
  correo o rol, estados, contadores globales y actualización tras guardar.
  Los tokens de invitación nunca forman parte del listado.
- Recomendaciones: calidad de oferta integrada en el orden dentro de bandas
  de afinidad, con explicación separada del porcentaje de compatibilidad.
  Las señales consentidas y la confianza empresarial mantienen su prioridad.
  Las fuentes externas son neutras. La vista permite elegir mayor compatibilidad.
- Redacción guiada: borradores editables desde datos registrados, comparación
  con texto anterior y aplicación por campo. No guarda ni publica automáticamente.
- Motor e integraciones: estados calculados desde configuración efectiva;
  distingue disponible localmente, manual, configurado por comprobar y pendiente
  de proveedor. No consulta servicios externos ni expone credenciales.
- Invitaciones: la pantalla respeta la pausa local de MFA al aceptar; las
  políticas del servidor y fuera del entorno de revisión siguen intactas.

Las pantallas utilizan los nuevos endpoints paginados. Los contratos antiguos se
conservan para clientes anteriores; sus límites no definen las nuevas bandejas.
Los indicadores de habilidades del ecosistema conservan su alcance de muestra
local, independiente de la paginación completa de empresas.

## Lo que no puede validarse sin servicios o datos reales

| Área | Función local | Dependencia para la versión real |
| --- | --- | --- |
| Certificados | Registro aportado por enlace, plan y evidencias | Verificación/sincronización con el emisor autorizado |
| Empresas | Solicitud, soportes, decisiones y seguimiento manual | Consulta de registro oficial y criterios operativos |
| Salarios | Muestra interna de empresas comparables | Fuente autorizada y representativa por rol y territorio |
| Acceso social y SSO | Adaptadores y pruebas aisladas | Aplicaciones, credenciales y cuentas autorizadas |
| Correo | Invitación y recuperación en bandeja local | Transporte real y comprobación de entrega |
| Catálogos | Importación manual y ejemplos | Acceso autorizado a APIs del proveedor |
| Aprendizaje estadístico | Reglas, métricas y laboratorio | Muestra real, consentida y suficiente |
| Capacidad | Pruebas sintéticas y recorridos locales | Ensayo representativo del entorno operativo |

Los escenarios ficticios permiten revisar estados preparados; no equivalen a una
certificación de cobertura absoluta, veracidad de certificados, existencia legal
ni capacidad de producción.

## Comprobación

`backend/tests/test_local_completion.py` cubre listados de más de 200 registros,
filtros, aislamiento entre empresas, permisos de administración, ausencia de
tokens privados, paridad de reputación, redacción sin persistencia y orden por
calidad sin alterar compatibilidad, incluida la caché.

Los comandos de validación y arranque continúan en `LOCAL_HANDOFF.md`. Las claves
y los accesos de revisión permanecen en `.local/escenarios/GUIA_ESCENARIOS.md`.

Resultado de la validación final:
- Backend: 487 pruebas aprobadas y una omitida, reservada para el entorno
  PostgreSQL de staging (no se conectó a PostgreSQL).
- Frontend: 28 pruebas aprobadas, ESLint y compilación Vite correctos.
- Ruff y comprobación de espacios del diff correctos.
- Navegador: paginación y búsqueda de organizaciones, filtros del equipo,
  invitaciones, estado de integraciones, redacción por campo y protección
  frente a borradores desactualizados. Diseño revisado en escritorio y móvil.
