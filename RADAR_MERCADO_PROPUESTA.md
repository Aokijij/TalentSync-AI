# Propuesta: Radar laboral en Mi desarrollo

Esta es una propuesta de siguiente funcionalidad, no un panel ya activado. El objetivo es orientar decisiones de aprendizaje y presentación profesional con datos comparables, sin calificar a la persona ni sobrecargar Mi perfil.

## Ubicación y recorrido

Reutilizar la pestaña «Qué aprender» de **Mi desarrollo** y evolucionarla a **Radar laboral**, conservando sus cursos y navegación. Presentar tres vistas internas: «Qué piden las ofertas», «Perfiles comparables» y «Salarios publicados». Cargo, ubicación y nivel se eligen una sola vez y se conservan al cambiar de vista. El perfil solo tendría un enlace compacto «Ver mi posición en el mercado», junto a la ayuda de carrera; no otro dashboard permanente.

La entrada muestra hasta tres observaciones con una acción cada una. Abrir una observación permite consultar muestra, periodo, filtros y origen. Una habilidad lleva a revisar/añadir una habilidad declarada o al curso correspondiente en el catálogo. Una referencia salarial permite revisar la aspiración con una explicación, sin cambiarla automáticamente. El radar no modifica el perfil ni la compatibilidad por sí solo.

## Datos y mensajes

- **Demanda:** «TypeScript aparece en 18 de 30 ofertas comparables». Usar vacantes activas, recientes, sin duplicados y de familias de cargo comparables. Esta primera vista amplía el radar de demanda que ya existe.
- **Perfiles comparables:** «12 de 25 perfiles participantes declaran TypeScript». Se requiere participación voluntaria, agregación y exclusión de la cuenta consultante, cuentas de prueba, duplicados y datos demasiado antiguos. Mostrar habilidades declaradas, nunca afirmar que otras personas las dominan. Propuesta inicial: no publicar grupos de menos de 20 perfiles; revisar el umbral al evaluar privacidad y estabilidad. No mostrar nombres, CV, empresas previas ni listas de integrantes.
- **Salarios:** mostrar mediana y rango central (percentiles 25–75) de ofertas comparables, con tamaño de muestra, fecha y proporción de ofertas que informan salario. La aspiración del candidato es una referencia privada. Solo comparar importes con moneda, periodicidad, jornada, modalidad y tipo de contratación compatibles; distinguir salario base de comisiones y de aspiraciones de otros candidatos. Propuesta inicial: mínimo de 20 ofertas válidas. Si faltan datos, indicar «Todavía no hay una muestra comparable».

No sustituir una ciudad por todo el país silenciosamente. Cuando falte muestra, ofrecer ampliar ubicación o familia de cargo y explicar el cambio antes de recalcular. No usar edad, género, foto u otras características personales para formar los grupos.

## Implementación por etapas

1. Ampliar la vista actual de demanda con comparación explícita de habilidades y enlaces al catálogo. Mantener periodo, fuentes y tamaño de muestra visibles.
2. Completar los campos de salario publicados (moneda, periodicidad, jornada y componentes) y la clasificación de familia/nivel de cargo. Normalizar ubicaciones y fechas sin inferir datos ausentes.
3. Crear agregados de ofertas actualizados diariamente por familia de cargo, ubicación y nivel. Consultarlos mediante un endpoint autenticado; evitar calcular el conjunto completo cada vez que alguien abre el perfil. Guardar fecha y versión del agregado para poder explicar cambios.
4. Añadir la comparación de perfiles solo después de disponer de participación voluntaria, suficiente muestra real y pruebas de privacidad. Mantenerla separada de los datos de demanda y salarios.

El entorno local revisado tiene 41 cuentas candidatas y 52 ofertas activas; incluye datos ficticios y de prueba. Estos números no son una muestra de mercado ni permiten afirmar una comparación con 1.000 candidatos. Antes de habilitar el benchmarking se debe identificar y excluir explícitamente esos registros, además de verificar los datos comparables disponibles.

No requiere una API generativa de pago: los cálculos son agregaciones estadísticas locales y las observaciones pueden redactarse con plantillas transparentes. «Ver formación» debe respetar el coste y duración informados por el catálogo; no prometer cursos gratuitos o de dos horas sin respaldo.

## Validación

Comprobar que nadie pueda obtener datos individuales variando filtros, que los grupos pequeños no aparezcan, que no se mezclen periodos salariales, que se excluyan demos y duplicados, que las muestras y fechas sean reproducibles y que añadir una habilidad requiera una decisión explícita. Medir uso de las acciones y relevancia de la formación, sin atribuir más entrevistas al radar sin evidencia.
