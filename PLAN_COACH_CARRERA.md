# Evolución hacia un asistente de carrera

13 de octubre de 2026. La propuesta tiene valor si cada observación lleva a una mejora concreta que el candidato puede revisar, guardar y usar. Retención, viralidad y más entrevistas son hipótesis a medir, no resultados garantizados.

## Primera entrega implementada

Actualización de implementación: el módulo compartido «Coach de Carrera» ya está disponible para todos los candidatos en Mi perfil. Incluye historial privado de propuestas con antes/después y deshacer, versiones por vacante seleccionables al postularse, copia profesional de lo enviado, PDF original frente a texto extraído y radar de demanda observado con enlaces al catálogo. Se prueba con perfiles de distintas profesiones; no depende de una cuenta ni de un CV concreto. Consulta `CONFIGURACION_LOCAL.md` para límites y uso. Los apartados siguientes conservan la arquitectura de evolución, incluyendo generación con IA y OCR que aún no se han activado.

Se sustituyó la lista de entidades detectadas por recomendaciones priorizadas de claridad y consistencia. Cada consejo enlaza con el campo a revisar. La experiencia de uso ahora genera una propuesta desde el texto guardado, con resultado adicional opcional, comparación editable y deshacer. El generador es local y conservador: transforma expresiones reconocidas sin aportar hechos. Un modelo de lenguaje generativo continúa pendiente. La vista del PDF prioriza comprobaciones accionables y la formación muestra primero tres habilidades por aprender; los detalles técnicos quedan desplegables.

Se corrigió el contexto de habilidades: formación y aprendizaje actual son estados diferentes. Cada mención tiene fragmento, motivo y, cuando existe, expresión explícita. Las etiquetas antiguas sin respaldo se presentan como contexto incierto. La importación no ejecuta GLiNER. No se penalizan periodos sin empleo ni se validan certificados.

## Siguiente entrega propuesta: redacción asistida y adaptación por vacante

El generador de texto debe recibir únicamente hechos confirmados, el campo seleccionado y, opcionalmente, los requisitos de una vacante. Primero pregunta por la información que falta: qué hizo la persona, alcance real, herramientas usadas y resultado comprobable. Si no hay cifras, redacta un resultado cualitativo. Devuelve una propuesta por campo con su origen, preguntas pendientes y comparación antes/después; no completa datos desconocidos.

Cada propuesta queda asociada a una versión del perfil. El candidato puede editarla, aceptarla o descartarla y recuperar el texto previo. Las métricas, nombres, fechas y habilidades nuevas requieren respaldo en los datos o confirmación explícita. El cambio no afecta una postulación ya enviada. Una prueba debe rechazar sugerencias que añadan porcentajes inexistentes, transformen responsabilidades en ascensos o declaren herramientas no registradas.

Para el modo por vacante, conviene guardar un borrador específico de la postulación, separado del perfil principal. Se pueden resaltar términos equivalentes ya respaldados y pedir aclaraciones sobre requisitos sin evidencia. Administrar servidores no permite afirmar experiencia en AWS automáticamente; la herramienta pregunta por tecnologías realmente utilizadas y conserva el cargo formal. La compatibilidad solo se recalcula con datos confirmados y muestra qué señal cambió; mejorar redacción por sí solo no acredita una habilidad.

## Lectura del PDF y exportación simple

Comparar el PDF privado con su texto original extraído y marcar secciones incompletas o mezcladas. El texto normalizado usado por el matching no sustituye esa vista. Reutilizar la exportación de perfil existente para ofrecer un PDF simple de una columna y permitir comprobar qué se pudo extraer de él. Medir orden de lectura, contactos y cobertura de campos con ejemplos revisados.

El visor requiere lectura autenticada del archivo, límites de tamaño/páginas y manejo de PDF sin texto. Para escaneos habrá que añadir OCR local y mostrar sus limitaciones. No debe llamarse «pasa cualquier ATS»: distintos parsers tienen comportamientos distintos. [Greenhouse documenta problemas con columnas, tablas, gráficos y encabezados](https://support.greenhouse.io/hc/en-us/articles/200989175-Unsuccessful-resume-parse).

## Radar de oportunidades con datos reales

Empezar por la demanda de las vacantes disponibles: qué habilidades se piden en ofertas de la misma familia de cargo, ciudad y nivel. Mostrar periodo, número de ofertas, origen, duplicados eliminados y datos faltantes. Conectar cada brecha con formación del catálogo y con la opción de declarar una habilidad que la persona realmente conoce. Esto informa demanda, no dominio de otros candidatos.

Las referencias salariales requieren suficiente muestra comparable, moneda, periodicidad, jornada y tipo de remuneración. Si faltan datos, se indica que no hay referencia suficiente. No inventar una comparación con «1.000 perfiles» ni porcentajes de dominio. Un eventual benchmarking de perfiles sería agregado, con protección frente a grupos pequeños y una finalidad definida; no mostrar datos individuales ni convertir similitud demográfica en empleabilidad.

## Consistencia como ayuda

Priorizar fechas imposibles, empleos marcados como actuales por error, contactos inconsistentes y textos confusos. Un intervalo laboral se muestra como una pregunta opcional, sin penalización ni obligación de explicar circunstancias personales. Estas ayudas no deben bloquear la publicación ni crear una puntuación oculta de calidad personal.

## Cómo medir el valor

- Corrección del contexto con casos de secciones mezcladas, negación, aprendizaje explícito, cursos terminados, proyectos y encabezados multicolumna; después, CV reales anonimizados y revisados con consentimiento.
- Proporción de consejos que producen una edición guardada; aceptación, edición y descarte de propuestas; hechos añadidos incorrectamente y restauraciones del texto anterior.
- Exactitud de campos y orden de lectura del PDF; tasa de datos desconocidos bien señalados; latencia.
- Relevancia de recomendaciones y resultados de postulaciones con suficiente muestra y sin atribuir causalidad a una mera mejora del texto.

La orientación de redacción se apoya en describir hechos y resultados, coherente con la [guía de Harvard para preparar un CV](https://careerservices.fas.harvard.edu/resources/create-a-strong-resume/). Ninguna guía garantiza obtener entrevistas ni superar todos los filtros.
