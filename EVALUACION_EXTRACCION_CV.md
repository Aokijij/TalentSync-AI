# Primera evaluación del extractor de entidades

Nota de estado: el panel de detecciones neuronales se retiró del flujo del candidato. Este documento conserva la evaluación experimental; no describe la interfaz actual. El perfil ahora ofrece recomendaciones de claridad y una guía STAR.

13 de octubre de 2026. Diagnóstico sobre 12 textos sintéticos, con respuestas esperadas explícitas: cuatro de desarrollo y ocho separados para evaluación. No son hojas de vida reales ni etiquetas revisadas por personas independientes. La muestra es pequeña y no representa la distribución de usuarios de TalentSync.

El extractor anterior se compara con GLiNER multilingual v2.1, revisión `443d26d654e0324125a96bebd8e796c14ff2efe6`, con etiquetas `job title`, `employer`, `degree`, `university`, `technical skill`, `date` y umbral 0,5. Las etiquetas se eligieron usando los ejemplos de desarrollo; no se ajustaron al conjunto separado. El encoder y tokenizador provienen de mDeBERTa v3 base, revisión `a0484667b22365f84929a935b5e50a51f71f159d`.

Se evalúa coincidencia exacta de entidad/tipo/documento, ignorando mayúsculas, acentos y espacios repetidos. Menciones duplicadas cuentan una vez. El baseline incluye profesiones, cargos, empresas, títulos, instituciones y todas las habilidades detectadas por reglas, incluyendo menciones negativas o en aprendizaje. Se mide detección de menciones, **no dominio de habilidades**. Las fechas se muestran para revisión pero se excluyen de esta comparación porque el baseline devuelve años normalizados, no necesariamente fragmentos originales.

## Resultado del conjunto separado

| Campo | F1 por reglas | F1 neuronal |
| --- | ---: | ---: |
| Cargos | 0,0000 | 1,0000 |
| Empresas | 0,0000 | 0,8889 |
| Títulos/carreras | 0,2222 | 0,6000 |
| Instituciones | 0,0000 | 1,0000 |
| Habilidades mencionadas | 0,6923 | 0,1333 |
| Total micro | 0,3704 | 0,6786 |

En estos ocho ejemplos, las reglas obtuvieron 10 aciertos, 9 detecciones incorrectas y 25 omisiones; el modelo obtuvo 19 aciertos, 2 detecciones incorrectas y 16 omisiones. Precisión/recuperación micro: reglas 0,5263/0,2857; neuronal 0,9048/0,5429. La carga del modelo más la inferencia tardó aproximadamente 14 segundos por texto corto en este equipo. No es una medición de latencia con documentos largos ni concurrencia.

El modelo aportó más entidades de trayectoria en esta muestra, pero recuperó muchas menos habilidades. Por eso se conserva el extractor por reglas y el nuevo modelo funciona como complemento de revisión. No se ha sustituido el parser, cambiado los pesos del matching ni fusionado automáticamente sus resultados. Un nombre detectado tampoco establece qué empresa corresponde a qué cargo; esa asociación la confirma la persona.

## Reproducir e inspeccionar errores

```powershell
backend/.venv/Scripts/python.exe scripts/local.py cv-evaluate
```

Fixture versionado: `backend/tests/fixtures/cv_entities_v1.json`. El informe local `.local/verification/cv-entities-evaluation.json` conserva las entidades esperadas y obtenidas, las métricas por campo y los tiempos. No usa ni transmite CV de usuarios. El informe muestra falsos positivos y omisiones, no solo aciertos. Las reglas y la salida neuronal se evalúan independientemente; no se presenta una cifra para una fusión no implementada.

Quedan por medir: CV reales anonimizados y anotados con consentimiento, PDF con columnas, escaneos, fechas y asociaciones completas, habilidades fuera del diccionario, conservación de campos confirmados y calidad del ranking con juicios humanos. Para ajustar con estos resultados se necesitará otro conjunto separado antes de afirmar una mejora general.

Fuente del modelo: [GLiNER multilingual v2.1](https://huggingface.co/urchade/gliner_multi-v2.1). Sus benchmarks publicados no se trasladan a TalentSync.
