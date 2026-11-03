# Perfil, importación de CV y compatibilidad

## Lectura y revisión

Producción usa `CV_PARSER=auto`: primero extrae el texto nativo del PDF. El reconocimiento de documentos que lo necesitan tiene un límite de 40 segundos (`CV_DOCLING_TIMEOUT_SECONDS`). La interfaz informa que la extracción está en marcha, limita la espera y no repite automáticamente una carga. Los PDF cifrados, dañados o escaneados con poca calidad pueden requerir revisión manual; no se promete precisión universal.

El lector reconoce los registros de las plantillas de TalentSync con el formato «cargo · empresa» y «título · institución», seguidos por su propio periodo. Se respetan meses, estudios en curso y límites de sección. La ubicación se contrasta con el catálogo de municipios. El resumen profesional se extrae de su apartado, separado de cargos y títulos.

La carga desde el perfil utiliza `replace_profile=true`. Antes de reemplazar datos existentes, la interfaz explica qué cambiará: experiencia laboral, formación académica, habilidades y resumen. Los certificados aportados por separado y las muestras de trabajo se conservan. La importación se guarda en el servidor; después se abre la edición para revisar y corregir lo extraído. Cancelar la edición posterior no revierte una importación ya confirmada. Los clientes antiguos que omiten ese parámetro conservan el comportamiento de combinación anterior.

## Datos actuales como fuente de compatibilidad

`contextual-match-v14` invalida los resultados de versiones anteriores. Los cambios en habilidades, experiencias, estudios y datos de la oferta modifican la firma de cálculo. Una colección estructurada vacía no recupera información desde los antiguos campos de texto. Los resúmenes automáticos anteriores tampoco sirven como evidencia para volver a introducir funciones eliminadas.

Las menciones sin confirmar del PDF son sugerencias de revisión, no puntos de compatibilidad. Solo intervienen los datos profesionales actuales y las evidencias aportadas. Eliminar un registro profesional invalida sus contextos antiguos; descartar una sugerencia tampoco vuelve a convertirla en una habilidad declarada. El archivo original del CV puede seguir almacenado sin participar en el cálculo.

## Generador y entrada

Preparar resumen devuelve un borrador editable basado en los datos aportados. Cuando no hay un modelo de redacción configurado, utiliza una composición estructurada sin servicios externos ni logros inventados. Si falta contexto suficiente, pide completar información. Generar no guarda el resumen: primero se aplica al borrador y después se guardan los cambios del perfil.

El selector de profesión ofrece búsqueda, teclado y texto libre para cargos de distintos sectores. El título del navegador es TalentSync. Las rutas privadas ocultan el HTML público antes del primer dibujo y muestran la validación de sesión; esto no sustituye la autorización de la API.

## Validación de esta revisión

- Pruebas de extracción de plantillas: tres experiencias, dos estudios con estados distintos, fechas mensuales, ubicación y resumen.
- Prueba aislada con el PDF adjunto por el usuario a través de la ruta real de importación, sin escribir en su perfil ni en almacenamiento de producción.
- Regresiones de eliminación, reimportación sin duplicados, resumen automático antiguo y sugerencias de CV sin confirmar.
- Revisión del selector con teclado y a 390 px; propuesta del generador comprobada en producción y descartada sin guardar cambios.
- El segundo CV mencionado no fue adjuntado y necesita una comprobación específica con ese archivo.

Los documentos personales y las capturas privadas de validación se mantienen fuera del repositorio.
