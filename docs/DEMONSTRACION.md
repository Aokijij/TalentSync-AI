# Exposición de TalentSync

## Organización propuesta

**TalentSync · Demostración** identifica el espacio de la exposición. Su descripción debe indicar: «Organización ficticia para demostrar TalentSync. Las vacantes y candidaturas de este espacio no representan procesos de contratación reales».

La opción recomendada es una instancia separada con su propia base de datos, archivos y cuentas. Así se pueden recorrer contratación, cierre de procesos y notificaciones usando datos ficticios. Si se utiliza la plataforma publicada, comenzar con la organización identificada como demostración y las vacantes en **borrador**. Su activación y las cuentas que recibirán avisos deben elegirse de forma explícita.

La cuenta empresarial necesita un correo de acceso distinto del administrador: son roles y cuentas diferentes. No inventar verificaciones de una entidad real. Los datos de ejemplo se encuentran en [demo/exposicion.json](demo/exposicion.json); son fichas de preparación, no un importador que publique automáticamente.

## Personas y permisos

| Cuenta | Función en la exposición |
| --- | --- |
| Administración demo | Revisar organizaciones, fichas de cuentas, calidad y publicación de vacantes. |
| Empresa demo · Propietario | Presentar la organización, crear ofertas y asignar permisos. |
| Equipo demo · Reclutamiento | Revisar candidaturas y coordinar el proceso. |
| Equipo demo · Entrevistas | Consultar únicamente los procesos asignados y registrar evaluaciones. |
| Candidato 01 · Frontend | Mostrar CV, proyectos, comparación y postulación. |
| Candidato 02 · Datos | Mostrar compatibilidad, SQL, formación y evidencias. |
| Candidato 03 · QA | Mostrar pruebas funcionales, entrevista y evaluación. |
| Candidato 04 · Operaciones | Mostrar una trayectoria distinta de tecnología y brechas de habilidades. |

Usar estos identificadores en CV, proyectos, evidencias, archivos y capturas. Evitar nombres, fotografías, teléfonos, documentos y certificados de personas reales. En una instancia separada, el correo de demostración debe quedarse en la bandeja local; las conexiones externas requieren sus propias autorizaciones.

## Vacantes que conviene preparar

Los salarios del archivo son cifras ficticias para comparar condiciones durante la exposición, sin pretensión de representar el mercado.

| Vacante | Modalidad | Habilidades principales | Qué permite demostrar |
| --- | --- | --- | --- |
| Desarrollo Frontend Junior · Demostración | Remota | HTML, CSS, JavaScript, React, Git | Proyectos, importación del CV, evidencias y selección técnica. |
| Análisis de Datos Junior · Demostración | Híbrida, Medellín | Excel, SQL, Python, Power BI | Compatibilidad, habilidades esenciales/deseables y ruta de aprendizaje. |
| QA Funcional Junior · Demostración | Remota | Pruebas funcionales, documentación, SQL, comunicación | Requisitos, respuestas de preselección y evaluación de entrevista. |
| Auxiliar de Operaciones · Demostración | Presencial, Medellín | Excel, inventarios, organización, comunicación | Un área distinta, filtros de ubicación y formación para una brecha concreta. |

Preparar una oferta completa y otra que necesite mejorar sus condiciones. Conservar ambas como borradores al comenzar: la segunda sirve para explicar por qué la revisión pide más información. Para las vacantes externas, usar una oferta de la fuente pública y demostrar su ficha, vigencia y decisión editorial, sin presentarla como una vacante propia de TalentSync.

## Recorrido sugerido: 15–20 minutos

1. **Presentación pública.** Marcar y desmarcar las tres habilidades de la demostración. Mostrar el porcentaje y su variación. Aclarar que ese ejemplo utiliza pesos iguales; el motor de la plataforma considera más información.
2. **Perfil del candidato.** Abrir Candidato 01, importar un CV ficticio, revisar experiencia, estudios, proyectos e idiomas y ajustar los datos. Exportar los diseños clásica y moderna.
3. **Redacción asistida.** Elegir una experiencia, autorizar el envío del fragmento, generar el borrador, revisarlo, aplicarlo y deshacerlo. El resultado no se incorpora sin la decisión del candidato.
4. **Descubrimiento.** Con Candidato 02, comparar dos ofertas y consultar requisitos cubiertos, pendientes y condiciones. Añadir una habilidad que tenga respaldo real dentro del escenario ficticio y volver a calcular la compatibilidad. No prometer un aumento fijo por habilidad: depende de los requisitos y del resto del perfil.
5. **Aprendizaje.** Filtrar por la brecha de comunicación o SQL, abrir un recurso y añadirlo al plan. Mostrar finalización declarada, evidencia de formación sin certificado y aportación opcional de un documento de ejemplo claramente identificado.
6. **Preparar una oferta.** Entrar como propietario, revisar la organización y comparar el borrador incompleto con el completo. Mostrar salario, jornada, requisitos esenciales/deseables, plazo de respuesta y preguntas de preselección.
7. **Postular y seleccionar.** En el entorno elegido para la demostración, publicar la oferta preparada y postular dos candidatos ficticios con diferencias de habilidades. Revisar respuestas, evidencias, comparación y etapas. La compatibilidad orienta; la decisión sigue en el equipo.
8. **Entrevista y equipo.** Asignar una entrevista, consultar la agenda y la evaluación con la cuenta de entrevistas. Mostrar que sus permisos son distintos de los del propietario. Calendar y videollamada pueden mostrarse con cuentas y dispositivos expresamente autorizados; no simular una conexión como si estuviera operativa.
9. **Administración.** Abrir fichas de cuentas, organización y oferta. Filtrar por origen y disponibilidad. En una oferta externa del escenario, mostrar por qué cumple o no los controles, retirarla, revisar su historial y comprobar que desapareció del catálogo. Restaurar su revisión cuando corresponda.
10. **Cierre.** En el entorno de demostración, pausar una oferta para conservar procesos; contrastarlo con cerrar una vacante y sus efectos. Mostrar resultados, avisos de prueba y la separación entre datos profesionales y acceso de cuenta.

## Preparación práctica

- Preparar sesiones independientes para candidato, empresa y administración; usar perfiles de navegador distintos para conservar cada acceso.
- Tener dos candidatos postulados a la misma oferta en la instancia de demostración y otro perfil con una brecha evidente.
- Conservar una oferta en borrador, otra activa y un proceso listo para entrevista, todos identificados como demostración.
- Guardar un punto de partida para repetir el recorrido sin borrar ni reemplazar cuentas existentes.
- Antes de la exposición, recorrer el flujo elegido completo, incluidos documentos, enlaces de cursos y permisos del equipo. Las integraciones externas dependen de la conectividad y sus cuotas; el guion puede continuar con las funciones de perfil, exportación, vacantes y seguimiento.
