# Protocolo de evaluación de TalentSync

Estado: preparado para ejecutar; todavía no hay validación con personas reales. La autorización actual cubre protocolo y herramientas con datos sintéticos. No reclutar participantes, reutilizar sus CV ni contactar empresas sin autorización adicional.

## Preparación y consentimiento

Responsables: una persona coordina el piloto, dos revisan extracción y relevancia por separado, otra decide la aceptación. Usar un entorno aislado con cuentas de prueba, acceso restringido, correo de prueba y calendario autorizado. Documentar versión Git, configuración sin secretos y muestra antes de empezar.

Para un futuro piloto, explicar propósito, tareas, quién accede, plazo y retirada. Obtener consentimiento separado de la postulación. La negativa no afecta oportunidades. Registrar el consentimiento fuera del conjunto de evaluación; no guardar nombres, correos, documentos completos ni claves en Git, incidencias o informes. Identificadores S001/J001; el mapa de identidades queda separado y cifrado. Permitir revisión y corrección de los datos extraídos.

Propuesta de muestra inicial: 20 recorridos, al menos 5 por rol (candidato, empresa y administrador), al menos 20 campos de extracción y 10 conjuntos de relevancia; incluir varias áreas, ciudades y niveles, documentos con columnas y distintos idiomas. Es un piloto de usabilidad, no una muestra representativa del mercado ni evidencia de ausencia de sesgos.

## Recorridos y registro

| Rol | Tarea | Evidencia esperada |
| --- | --- | --- |
| Candidato | Importar un CV, revisar habilidades, idiomas y fechas | Campos comparados con referencia humana, corrección posible y ausencia de datos inventados |
| Candidato | Guardar preferencias del CV, nombrar una versión, postular y revisar documento enviado | PDF correcto, contenido elegido y confirmación sin doble postulación |
| Candidato | Filtrar vacantes y radar nacional, comparar dos, guardar/ocultar | Listados, contadores y estado postulado coherentes |
| Candidato | Iniciar, salir y continuar un reto; entregar | Respuestas conservadas, temporizador y explicación al finalizar |
| Empresa | Abrir candidatura, descargar CV, revisar respuestas y avanzar proceso | Permisos correctos, compatibilidad explicada y sin notas internas para el candidato |
| Ambos | Programar, sincronizar, mover y cancelar entrevista | Un solo evento propio; cambio/cancelación propagado; sin invitados ni notas privadas |
| Administrador | Consultar integraciones, correo y operaciones | Diferencia entre configurado, observado, aceptado, entregado y fallido |
| Candidato | Exportar y eliminar una cuenta exclusiva del piloto | ZIP propio sin credenciales/notas de empresa; sesiones revocadas, archivos borrados o reintento visible |

Registrar por recorrido: ID, rol, tarea, completado sin ayuda, tiempo, error observado, gravedad, evidencia sin datos personales y versión. Medir éxito sin ayuda; registrar ayudas aparte. Revisar teclado, móvil, tema claro/oscuro, estados vacíos, errores, cargas y confirmaciones. Detener el piloto ante exposición entre cuentas, pérdida de datos, postulación duplicada o borrado de otra cuenta.

## Etiquetado y métricas

Dos evaluadores revisan una referencia por habilidades, formación, experiencia e idiomas; resuelven discrepancias y anotan acuerdo. La F1 de conjuntos normaliza mayúsculas y espacios, pero no comprueba cronología ni veracidad: revisar fechas, solapamientos y hechos por separado. No aceptar añadidos inventados aunque mejore la métrica.

Calificar cada vacante de 0 (sin relación) a 3 (muy relevante), considerando requisitos y preferencias declaradas. Evaluadores no ven la puntuación del motor durante el etiquetado. Registrar orden y calcular NDCG@5 contra todas las opciones etiquetadas. Comparar con la versión anterior usando la misma muestra; no interpretar afinidad como probabilidad de contratación.

Umbrales de revisión inicial: F1 ≥ 0,90; NDCG@5 ≥ 0,80; recorridos completados ≥ 90 %; cero incidencias críticas. Muestra mínima según preparación. Revisar por área/ubicación/nivel cuando haya muestra suficiente (al menos 5); evitar publicar grupos pequeños. Documentar limitaciones y acuerdo humano antes de decidir. El programa nunca declara automáticamente validación real ni activa un modelo.

## Herramienta y datos

Ejecutar desde la raíz:

```powershell
backend/.venv/Scripts/python.exe scripts/pilot_evaluation.py docs/pilot/synthetic-example.json --output .local/pilot/synthetic-report.json
```

Para datos futuros autorizados usar `mode: consented_pilot`, `consent: {documented: true, withdrawal_available: true}` y el mismo esquema del ejemplo. Cada fila usa un ID único S001, `role`, `flow_completed`, opcionalmente `extraction` (listas `expected`/`actual` por campo), `relevance` (J001: 0–3) y `ranking`. `critical_issues` es obligatorio. El informe contiene agregados y nunca textos de CV ni respuestas. Guardar entradas fuera de Git. No confundir el ejemplo perfecto de tres muestras con una evaluación suficiente.

## Cierre, retirada y conservación

Propuesta operativa del piloto: borrar documentos y mapa de identidades al cerrar la revisión, máximo 30 días tras terminar; conservar solo agregados sin datos personales. Aprobar y comunicar el plazo antes de recopilar. Retirar datos de quien lo solicite y recalcular el informe. Registrar responsable, fecha y evidencia de limpieza sin copiar documentos. No es una política legal automática: el responsable de la plataforma debe aprobarla y comunicarla.

Entrega: informe agregado, incidencias priorizadas, comparación con versión anterior, limitaciones, acta de decisión y evidencia de borrado. Hasta entonces el panel y la documentación deben indicar pendiente de validación real.
