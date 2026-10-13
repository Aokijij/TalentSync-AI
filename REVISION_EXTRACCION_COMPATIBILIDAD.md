# Revisión de la propuesta de extracción y compatibilidad

Revisión del 13 de octubre de 2026, contrastada con el código y el entorno local de TalentSync. Este documento evalúa una mejora; no activa servicios externos ni modifica el motor de compatibilidad.

Actualización posterior: se implementó `contextual-match-v5` con reglas de extracción contextual, estados por requisito, meses en cargos relacionados y similitud separada por cargos, funciones y conocimientos. Se conservan datos y documentos aportados al importar. Se añadió GLiNER multilingüe local para sugerencias de entidades con revisión explícita y una evaluación sintética reproducible (`EVALUACION_EXTRACCION_CV.md`). El OCR, los formatos nuevos, la evaluación humana con CV reales y la confirmación previa de toda la extracción por reglas siguen pendientes. La tabla siguiente conserva el diagnóstico inicial; consulta `CONFIGURACION_LOCAL.md` para el comportamiento implementado y la escala de respaldo.

## Conclusión

Sí es viable. La prioridad es obtener datos correctos y confirmados del CV antes de cambiar los pesos del ranking. TalentSync ya tiene embeddings locales, desglose por señales, normalización básica y recomendaciones de formación por brechas. Incorporar otro proveedor de parsing no es un requisito para empezar.

## Qué existe y qué falta

| Área | Estado comprobado | Mejora propuesta |
| --- | --- | --- |
| Lectura de documentos | `ResumeReader` admite únicamente PDF, hasta 5 MB. Hay un adaptador opcional Docling/OCR en `pdf_reader.py`. En este entorno se usa `CV_PARSER=pypdf`, OCR desactivado y no están instalados Docling ni EasyOCR. | Preparar una versión compatible de Docling y su motor OCR; probar PDF escaneado, dos columnas y texto digital. Ampliar la entrada a DOCX e imágenes con validación del archivo. |
| Extracción estructurada | `text_processor.py` extrae experiencias, estudios, cursos, habilidades y contacto mediante reglas, diccionarios y heurísticas de estructura. La similitud neuronal del matching no convierte este parser en un extractor neuronal de entidades. | Añadir extracción por esquema con contexto y procedencia por campo. Mantener reglas fiables para correo, teléfono y fechas. Usar un modelo local de entidades o extracción estructurada como complemento, evaluado con CVs en español. |
| Confirmación de datos | `upload_cv` guarda el resultado directamente; puede sustituir las listas de experiencias, estudios y certificados si detecta registros. | Vista previa con datos actuales frente a detectados, corrección y aceptación por campo; conservar datos confirmados, documentos aportados y fechas desconocidas sin inventarlas. |
| Normalización | `skills.py` ya reconoce alias y bases relacionadas, sin tratarlas como equivalencias completas. | Ampliar ocupaciones y habilidades con identificadores, sinónimos y relaciones jerárquicas. ESCO puede aportar una base, adaptada a términos y ocupaciones locales. |
| Compatibilidad | Modelo Sentence Transformer local, señales de habilidades, contexto, formación, certificaciones e idiomas, y condiciones laborales separadas. | Comparar funciones y requisitos por bloques, e incorporar experiencia relevante por familia de cargo. Evaluar un reranker para un subconjunto de resultados antes de adoptarlo. |
| Aprendizaje de decisiones | Hay personalización por decisiones del candidato y entrenamiento en modo de evaluación, sin activación automática del modelo entrenado. | Incorporar feedback de reclutadores con motivos, suficiente muestra y evaluación separada; probarlo primero sin alterar recomendaciones reales. |

Evidencia principal: `backend/app/infrastructure/nlp/{resumes,pdf_reader,text_processor,matching_encoder}.py`, `backend/app/application/use_cases/{profiles,matching,personalization}.py` y `backend/app/domain/services/{skills,matching,matching_text}.py`.

## Ajustes necesarios al texto propuesto

- Inferir liderazgo por una experiencia puede producir una sugerencia con el fragmento que la respalda. No debería crear habilidades ocultas ni asumir metodologías ágiles por haber liderado un equipo. El candidato debe confirmar la sugerencia.
- Ingeniero de software y desarrollador backend pueden compartir una familia profesional; no son cargos intercambiables. React, Angular y diseño UX también son conceptos relacionados, no habilidades equivalentes.
- El contexto debería referirse a funciones, sector y requisitos laborales expresos. Evitar una puntuación vaga de “encaje cultural” basada en tamaño o prestigio de empleadores anteriores.
- Un rechazo no demuestra por sí mismo que la recomendación fuera incorrecta. Usarlo automáticamente puede reforzar preferencias arbitrarias o sesgos; hacen falta motivos y evaluación.
- El porcentaje actual es una puntuación compuesta de afinidad, no una probabilidad de contratación. La similitud de embeddings tampoco acredita una habilidad.
- Las citas `[cite: ...]` del texto no identifican fuentes consultables. Las afirmaciones de más del 90% de precisión, tiempos de procesamiento y planes gratuitos no se toman como garantías ni como precios verificados.

## Orden de implementación recomendado

1. **Datos antes de ranking:** vista previa y fusión del CV sin sobrescribir datos confirmados; procedencia y advertencias por campo; conjunto de CVs anonimizados con resultados esperados.
2. **Lectura y estructura:** OCR local, DOCX e imágenes; extracción contextual y revisión de fechas, columnas, trabajos simultáneos y estudios en curso. Separar lectura del documento de interpretación de campos. Limitar páginas y tiempo, procesar trabajos lentos fuera de la petición y limpiar archivos temporales.
3. **Compatibilidad contextual:** taxonomía de ocupaciones y habilidades, experiencia relevante sin sumar dos veces periodos simultáneos, similitud por funciones y requisitos. Evaluar recuperación más reranking, conservando las condiciones imprescindibles y las explicaciones del score.
4. **Aprendizaje controlado:** feedback con motivos, comparación contra el motor actual y activación solo si mejora las métricas y no introduce diferencias injustificadas.

La primera entrega útil sería **vista previa del CV + conservación de datos + OCR local comprobado**. Es posible avanzar sin una API comercial, aunque exige dependencias, pesos locales, recursos de CPU/memoria y pruebas de compatibilidad. Una API de pago se evaluaría después con el mismo conjunto de documentos, coste y tratamiento de datos definidos.

## Cómo comprobar que mejora

- Extracción: precisión y recuperación por campo; acierto de fechas, cargos, instituciones y habilidades; errores en escaneos; conservación de datos al fusionar; tiempo y memoria por documento.
- Recomendación: relevancia de las primeras ofertas (por ejemplo NDCG@k y Recall@k), cumplimiento de condiciones y comparación con juicios revisados por personas. Separar ejemplos de evaluación y de ajuste, incluyendo perfiles de distintos sectores e idiomas.
- Definir los objetivos después de medir la línea base. Los tests funcionales existentes comprueban comportamiento, pero no establecen la precisión del parser ni la calidad del ranking sobre CVs reales.

## Fuentes primarias contrastadas

- [Docling: ejecución local, lectura de estructura y OCR](https://github.com/docling-project/docling), y [formatos admitidos](https://docling-project.github.io/docling/usage/supported_formats/). Su soporte no implica que TalentSync acepte actualmente esos formatos.
- [Sentence Transformers: recuperación y reranking](https://sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html). La arquitectura es viable; su mejora en empleo debe medirse con datos del proyecto.
- [ESCO: clasificación europea de capacidades, competencias y ocupaciones](https://esco.ec.europa.eu/es). Se propone como base de normalización, sin asumir equivalencia automática ni cobertura completa del mercado colombiano.
