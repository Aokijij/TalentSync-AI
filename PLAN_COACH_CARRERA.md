# Evolución hacia un asistente de carrera

13 de octubre de 2026. La propuesta tiene valor si cada observación lleva a una mejora concreta que el candidato puede revisar, guardar y usar. Retención, viralidad y más entrevistas son hipótesis a medir, no resultados garantizados.

## Primera entrega implementada

Nueva revisión del 14 de octubre: confirmación de habilidades sin diferencias por acentos; indicador de pendientes accionable; búsqueda de ciudades con combobox; recomendaciones compactas y orden por porcentaje corregido; historial agrupado por experiencia. La exportación distingue columna lateral clásica, cabecera moderna y composición editorial minimalista. El matching v7 deja de penalizar cursos no solicitados y conserva el contexto privado de las nuevas propuestas aplicadas sin modificaciones; las correcciones personales invalidan ese respaldo. El benchmarking de perfiles y salarios sigue como propuesta: véase [Radar laboral](RADAR_MERCADO_PROPUESTA.md).

Actualización del 14 de octubre: Mi perfil vuelve a mostrar todos los apartados en una vista continua. El botón «Ideas para mejorar tu hoja de vida» abre un modal con sugerencias y redacción. Mi desarrollo mantiene «Qué aprender», ahora con selección de habilidad y cursos en dos pasos. Cada vacante ofrece consejos de solo lectura sobre qué destacar o aclarar en el perfil habitual. Se retiraron la preparación, selección y exportación de versiones por vacante; las copias históricas ya enviadas se conservan. La exportación general respeta el diseño seleccionado. Se corrigió el fallo de variables fuera de alcance que dejaba la vista previa en negro, con pruebas de renderizado para los tres estilos.

La redacción ya usa Qwen2.5-1.5B-Instruct cuantizado, ejecutado localmente con llama.cpp, sin API de pago. Genera una acción por cada responsabilidad del texto original y una pregunta para concretar el aporte; evita reducir toda la experiencia a un resumen de 100 palabras. Cada responsabilidad se valida de forma independiente y se conserva el original si la IA pierde detalles o añade hechos; se compara, edita, aplica y deshace. Se filtran afirmaciones promocionales no respaldadas y se rechazan números y herramientas nuevos reconocibles. La revisión humana sigue siendo necesaria. Las propuestas se prueban con profesiones diferentes y no dependen de una cuenta concreta. Consulta `CONFIGURACION_LOCAL.md` para preparación reproducible, hashes, límites y operación. Los apartados siguientes describen la evolución deseada, incluyendo OCR y una evaluación más amplia con CV anonimizados.

Se corrigió el contexto de habilidades: formación y aprendizaje actual son estados diferentes. Cada mención tiene fragmento, motivo y, cuando existe, expresión explícita. Las etiquetas antiguas sin respaldo se presentan como contexto incierto. La importación no ejecuta GLiNER. No se penalizan periodos sin empleo ni se validan certificados.

## Criterios para evolucionar la redacción asistida

El generador de texto debe recibir únicamente hechos confirmados, el campo seleccionado y, opcionalmente, los requisitos de una vacante. Primero pregunta por la información que falta: qué hizo la persona, alcance real, herramientas usadas y resultado comprobable. Si no hay cifras, redacta un resultado cualitativo. Devuelve una propuesta por campo con su origen, preguntas pendientes y comparación antes/después; no completa datos desconocidos.

Cada propuesta queda asociada a una versión del perfil. El candidato puede editarla, aceptarla o descartarla y recuperar el texto previo. Las métricas, nombres, fechas y habilidades nuevas requieren respaldo en los datos o confirmación explícita. El cambio no afecta una postulación ya enviada. Una prueba debe rechazar sugerencias que añadan porcentajes inexistentes, transformen responsabilidades en ascensos o declaren herramientas no registradas.

Para una vacante, la plataforma muestra requisitos que ya tienen respaldo y los que conviene aclarar. Sugiere editar la experiencia o las habilidades habituales, sin crear otra versión del perfil ni de la postulación. Administrar servidores no permite afirmar experiencia en AWS. La compatibilidad se recalcula con datos confirmados; mejorar la redacción por sí solo no acredita una habilidad.

## Exportación diseñada y lectura del PDF

Actualización del 14 de octubre: «Diseñar y exportar» permite elegir secciones, foto, estilo y color y revisar el PDF exacto antes de descargarlo. Se genera con fuentes Unicode, paginación y tres diseños mediante ReportLab; no depende del antiguo renderizador HTML de vista previa. Las opciones de exportación no alteran los datos guardados. La lectura técnica del documento permanece como diagnóstico privado, fuera del flujo principal del candidato.

Las menciones del CV ahora ofrecen confirmar una habilidad declarada, explorar formación y descartar/recuperar, conservando el fragmento original. Los consejos por vacante se abren desde su barra lateral en un modal. La navegación a una vacante similar reinicia las consultas y el estado completo de esa pantalla. «Qué aprender» dispone de filtros visibles, acciones compactas y fuentes presentadas en tarjetas; Recomendaciones separa visualmente cada oportunidad. La cabecera del perfil reúne el acceso a ideas y la barra de edición/exportación permanece visible al desplazarse.

Como evolución del diagnóstico, comparar el PDF privado con su texto original extraído y marcar secciones incompletas o mezcladas. El texto normalizado usado por el matching no sustituye esa vista. Medir orden de lectura, contactos y cobertura de campos de la exportación diseñada con ejemplos revisados.

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
