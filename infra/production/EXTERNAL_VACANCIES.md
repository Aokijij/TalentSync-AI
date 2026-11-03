# Vacantes externas y vigencia

La postulación continúa en el portal original. TalentSync conserva atribución, identificador, ubicación y contenido publicado; las consultas de empleo no envían hojas de vida a los proveedores.

## Fuentes y actualización

- **JSearch / OpenWeb Ninja:** descubre ofertas de portales colombianos mediante la clave privada ya configurada. La paginación usa el cursor de la fuente. La presencia en el agregador exige una comprobación adicional del anuncio original.
- **Greenhouse y Lever:** APIs públicas de las empresas. Se conservan los encabezados y listas del anuncio. Lever consulta hasta 1.000 publicaciones por portal y la vista previa selecciona hasta 100 coincidencias; el tamaño máximo de respuesta es 16 MB.
- **Get on Board:** API pública documentada, sin clave. Se expanden empresa, habilidades, ciudades, regiones y contrato. Se incluyen ubicaciones explícitas de Colombia o regiones remotas que contienen Colombia; decir solo «remoto» no acredita elegibilidad.
- **CSV/Excel autorizado:** permite actualizar por origen e ID, con deduplicación adicional por URL y empresa/cargo/ubicación.

Administración → Vacantes muestra el progreso de la sincronización en segundo plano y separa registros guardados, disponibles, en revisión y cerrados. Las fuentes originales permanecen accesibles desde cada oferta. La consulta manual de un portal específico sigue disponible.

## Política de contenido

`source-facts-v3` exige fecha original dentro de los últimos tres meses, tres habilidades distintas identificadas en el anuncio, funciones y requisitos suficientemente descritos. La experiencia y formación ausentes se conservan como **no especificadas**. Su ausencia no equivale a un requisito cumplido ni provoca por sí sola el rechazo de una oferta útil. No se inventan fechas, títulos, requisitos ni salarios. Los importes extranjeros no se presentan como COP.

Un registro incompleto queda en revisión. Las ofertas repetidas se actualizan mediante su identidad de origen y las claves semánticas; no se crean cuentas empresariales verificadas por importar un anuncio.

## Comprobaciones automáticas

Con `PERIODIC_MAINTENANCE_ENABLED=true`, el catálogo se actualiza diariamente. `CATALOG_SYNC_KEYWORDS` define las búsquedas y `CATALOG_TARGET_ACTIVE=100` muestra la meta operativa, no una garantía de disponibilidad de terceros.

Con `EXTERNAL_JOB_CHECKS_ENABLED=true`, se revisan lotes de hasta 20 ofertas cada cinco minutos, con presupuesto de 45 segundos por ciclo. La próxima revisión se programa a las 24 horas si hay confirmación, o a las seis horas si no puede confirmarse.

| Estado | Tratamiento |
| --- | --- |
| `pending` | Pendiente de consulta original; fuera de recomendaciones. |
| `verified` | ID publicado por API original o evidencia estructurada exacta y vigente; visible hasta 72 horas desde la confirmación y antes de vencer. |
| `unknown` | Evidencia insuficiente; se conserva para revisión. |
| `unavailable` | Fallo temporal, límite o bloqueo; se reintenta y no se declara cierre. |
| `closed` | Cierre acreditado por la fuente o vencimiento explícito del anuncio. |

El límite de vigencia se aplica también en las consultas públicas aunque el trabajador se detenga. Se respetan robots, TLS y controles de acceso. LinkedIn y Computrabajo pueden aparecer en búsquedas sin quedar disponibles si impiden verificar su anuncio original; no se eluden esas restricciones.

Antes de una migración se conserva una copia verificada de PostgreSQL y la versión anterior del servicio para recuperación.
