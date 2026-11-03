# Evaluación de extracción, compatibilidad y recorridos

`scripts/pilot_evaluation.py` calcula métricas agregadas a partir de muestras sintéticas o de un piloto autorizado. El ejemplo versionado es una fixture de pruebas; sus resultados no validan el comportamiento con personas reales.

## Ejemplo reproducible

Desde la raíz:

```powershell
backend/.venv/Scripts/python.exe scripts/pilot_evaluation.py backend/tests/fixtures/pilot-synthetic-example.json --output .local/pilot/synthetic-report.json
```

La entrada declara `mode`, `samples` y `critical_issues`. Cada muestra tiene un ID S001 único, un rol y `flow_completed`; puede incluir extracción con listas `expected` y `actual`, relevancia de vacantes J001 de 0 a 3 y un ranking sin duplicados. El informe conserva agregados y omite textos de CV.

## Métricas y límites

| Métrica | Qué mide | Qué requiere revisar por separado |
| --- | --- | --- |
| F1 de extracción | Coincidencia de conjuntos normalizados de entidades. | Cronología, veracidad y datos añadidos sin soporte. |
| NDCG@5 | Orden del ranking frente a una referencia humana. | Criterios de relevancia, preferencias y acuerdo entre evaluadores. |
| Finalización | Proporción de recorridos completados. | Ayudas recibidas, tiempo, errores y accesibilidad. |

El umbral inicial del programa requiere 20 muestras, al menos 5 por rol, 20 campos de extracción y 10 rankings. Los objetivos son F1 ≥ 0,90, NDCG@5 ≥ 0,80, finalización ≥ 90 % y cero incidencias críticas. Alcanzarlos solicita revisión humana; no declara validación real ni activa modelos.

## Pilotos con participantes

Usar `mode: consented_pilot` exige consentimiento documentado y posibilidad de retirada. La participación es independiente de la postulación. Guardar entradas y el mapa de identidades fuera de Git, sin nombres o documentos completos en informes.

Cubrir importación y corrección de CV, preparación y envío de una candidatura, seguimiento, revisión empresarial, entrevistas y permisos administrativos. Registrar tarea, versión, ayuda, error y gravedad. Detener la revisión ante exposición entre cuentas, pérdida de datos o acciones duplicadas.

Dos evaluadores deben acordar la referencia, resolver discrepancias y revisar resultados por área, ubicación y nivel cuando la muestra lo permita. Definir el plazo de conservación antes de recopilar datos; conservar después únicamente agregados adecuados al propósito de la evaluación.
