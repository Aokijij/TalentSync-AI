# Configuración y revisión de TalentSync

Guía del 13 de octubre de 2026. Se utiliza el entorno aislado `.local/`, SQLite y los servidores de tu computador. No requiere publicar la aplicación, comprar un dominio ni crear recursos de Azure.

## 1. Abrir el proyecto

Abre PowerShell en la carpeta del proyecto:

```powershell
cd "C:\Users\USUARIO\OneDrive\Escritorio\TalentSync AI"
```

Las dependencias ya están instaladas en esta máquina. Si preparas otro equipo, instala Python compatible con los requisitos del proyecto y Node.js, crea `backend/.venv`, instala `backend/requirements-lite.txt` y `backend/requirements-dev.txt`, y ejecuta `npm ci` dentro de `frontend`. Los pesos locales del motor se preparan con `scripts/local.py model-prepare`; ese paso requiere descargar el modelo. En esta máquina los pesos ya existen.

## 2. Preparar y comprobar la base local

```powershell
backend/.venv/Scripts/python.exe scripts/local.py setup
backend/.venv/Scripts/python.exe scripts/local.py doctor
```

`setup` aplica las migraciones existentes. Esta entrega conserva las fechas y preferencias en campos JSON existentes: no sustituye cuentas ni necesita una migración nueva. `doctor` comprueba archivos, base y servidores; los servidores pueden aparecer como aviso si todavía no los abriste.

No cambies DATABASE_URL al PostgreSQL de otro entorno. Los comandos locales no leen `backend/.env`; usan `.local/backend.env` y `.local/talentsync.sqlite3`.

## 3. Iniciar los dos servidores

En una primera terminal, desde la raíz:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py backend
```

En otra terminal:

```powershell
cd "C:\Users\USUARIO\OneDrive\Escritorio\TalentSync AI\frontend"
node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5173 --strictPort
```

Abre [TalentSync local](http://127.0.0.1:5173). Conserva ambas terminales abiertas. Si un puerto está ocupado, reutiliza el servidor del proyecto o detenlo con Ctrl+C en su terminal antes de iniciarlo otra vez. No cierres procesos desconocidos.

## 4. Entrar con las cuentas de revisión

Las cuentas ficticias y sus contraseñas se guardan en `.local/escenarios/accounts.json`. Usa el portal correspondiente a candidato, empresa o administrador. Ese archivo es privado y no se incorpora a Git.

Si estás preparando una base local nueva, puedes crear los escenarios con:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py seed-scenarios
```

La base actual ya contiene esos escenarios; no necesitas volver a generarlos para revisar esta entrega. El correo permanece en la bandeja local y la pausa local de la verificación en dos pasos se conserva.

## 5. Configurar el perfil del candidato

1. En **Mi perfil**, pulsa Editar.
2. Confirma tu ciudad y departamento.
3. En **Preferencias laborales → Ciudad y movilidad**, indica si aceptas trasladarte y si puedes viajar. Son decisiones diferentes.
4. Añade otras ciudades donde puedes asistir habitualmente, separadas por comas. Esto no representa una preferencia de viajes ocasionales.
5. Solo marca un trabajo como actual. Al seleccionar otro, revisa y completa la finalización del anterior. En cada experiencia, abre el calendario, escribe el año y elige un mes de la cuadrícula para inicio y finalización, o marca **Trabajo actualmente aquí**. Guarda el perfil.

En Formación académica, marca **Estudio actualmente aquí** para una carrera en curso. Se mostrará **En curso** en el perfil y la hoja de vida, y no se tomará como un nivel académico terminado.

Las fechas antiguas que solo tienen año siguen disponibles: no se inventaron meses. Las fechas futuras o invertidas se rechazan. Un final vacío no cuenta como empleo actual. Los meses de cargos simultáneos no se suman dos veces al calcular la experiencia total.

## 6. Revisar las vacantes y su calidad

1. En Empresa → **Calidad de ofertas**, elige una vacante.
2. Completa salario fijo o rango, contrato, días y horario, modalidad y ciudad/territorio.
3. Describe responsabilidades y al menos un resultado con su evaluación y plazo.
4. Indica nivel, años mínimos —pueden ser cero— y evidencia aceptada. Distingue habilidades esenciales, deseables y aprendibles.
5. En Idiomas, pulsa Añadir idioma, selecciona su nombre y nivel mínimo. Elimina filas que no vayas a completar.
6. Completa entrevistas, duración total y plazo de respuesta por avance.
7. Revisa las indicaciones. Pulsar una mejora abre el paso correspondiente y lleva al campo cuando está disponible.
8. Guarda como borrador o publica cuando la revisión y la verificación de empresa lo permitan.

La puntuación se recalcula con el borrador actual. Si una revisión falla, no se presenta la puntuación anterior como vigente. El horario debe explicar días y horas o turnos; texto de relleno no basta. La revisión sigue siendo orientativa, basada en reglas; no verifica contratos ni condiciones reales.

En **Mis vacantes**, Ver candidatos y Editar son las acciones principales. Debajo aparecen Revisar calidad, Pausar/Activar/Reabrir y Eliminar, sin desplegar un menú. En Postulaciones, guarda los movimientos pendientes antes de finalizar el proceso.

La puntuación muestra cuatro niveles: **A · Excelente (90–100)**, **B · Buena (75–89)**, **C · Por mejorar (50–74)** y **D · Inicial (0–49)**. Abre **¿Qué significa cada nivel?** junto a la puntuación para consultar la explicación. El nivel describe la claridad e información registrada; los requisitos obligatorios para publicar se revisan por separado.

En **Mejora la redacción de tu oferta**, pulsa Preparar mejoras. Revisa las pestañas Responsabilidades y Requisitos, consulta qué cambió y edita la propuesta. **Aplicar este texto** modifica el borrador; **Restaurar texto anterior** revierte esa aplicación. Guarda únicamente después de revisar. El asistente local conserva el contexto, organiza los datos y retira frases genéricas independientes; no inventa funciones, condiciones ni cifras. Si detecta información contradictoria, pide confirmarla.

## 7. Buscar talento y revisar procesos

1. En **Buscar talento**, selecciona la vacante y el grupo: personas para invitar o quienes ya se postularon.
2. Busca por nombre, profesión o habilidad y ajusta el porcentaje mínimo. Usa Anterior/Siguiente: se muestran nueve candidatos por página, en tres columnas cuando hay espacio.
3. Revisa **Ubicación y movilidad**. Para presencial/híbrido, se compara la ciudad y el departamento cuando están disponibles; también se consideran las ciudades de asistencia declaradas.
4. Un traslado aceptado se señala como pendiente de acordar. Poder viajar no se considera aceptación de asistencia diaria. Si faltan datos, se pide confirmar disponibilidad.
5. Cuando hay otra ciudad y el candidato rechaza tanto viajes como traslado, el índice mostrado a la empresa recibe un ajuste relativo de −20%, explicado junto al índice profesional, y se bloquea la invitación. Es una regla local de disponibilidad, no una probabilidad de contratación. Las preferencias no modifican el índice profesional del candidato.
6. En **Organización y equipo → Procesos asignados**, filtra por vacante, etapa o candidato. La lista muestra ocho procesos por página; Abrir proceso conserva el acceso a entrevista y evaluación interna según el rol.

El propietario y el reclutador pueden abrir **Asignar entrevistas**, elegir un entrevistador activo y seleccionar sus vacantes. Guardar reemplaza las asignaciones de ese entrevistador; desmarcar una vacante retira el acceso. Esta acción no cambia roles ni permite invitar o retirar integrantes. Cuando la empresa ya está verificada, Verificada pasa al último apartado y la pantalla abre Equipo o Procesos.

## 8. Administración y catálogo educativo

En **Salud del ecosistema** hay dos apartados: Comportamiento de empresas y Bandeja de incidencias. El mapa de habilidades y la auditoría están desplegables dentro del primero; las incidencias se atienden en su propia bandeja.

En **Catálogo educativo**:

1. Pulsa el nombre del recurso o **Ver ficha** para consultar descripción, habilidades, requisitos, duración, idioma, acceso y certificado. Desde la ficha puedes abrir la fuente o editar los recursos administrables. Biblioteca muestra una tabla administrativa con recursos publicados, sin publicar y base de plataforma. Permite buscar por título/habilidad, filtrar por proveedor, editar y abrir la fuente oficial.
2. Fuentes y conectores organiza cada proveedor en su propio apartado: Selección editorial, SENA, Sapiencia, YouTube y Microsoft. Muestra un conector a la vez y los pasos para activarlo.
3. Biblioteca oficial contiene la selección editorial de 65 recursos. SENA y Sapiencia consultan fuentes públicas; YouTube y Microsoft requieren su configuración externa.
4. Importa primero como borrador, comprueba contenido, habilidades, acceso y certificado, y publica la selección revisada.

Para cargar la selección editorial y actualizar las fuentes públicas en la base local:

```powershell
backend/.venv/Scripts/python.exe scripts/local.py seed-education
backend/.venv/Scripts/python.exe scripts/local.py sync-education
```

La carga conserva ediciones y planes existentes. La consulta al SENA y Sapiencia requiere Internet. Una inscripción anunciada no garantiza cupo.

## 9. Integraciones sin clave: SENA, Sapiencia, GitHub y Codewars

Edita únicamente `.local/backend.env`, conservando sus demás valores:

```dotenv
PUBLIC_LEARNING_REFRESH_ENABLED=true
GITHUB_PROJECT_ANALYSIS_ENABLED=true
CODEWARS_ENABLED=true
```

Reinicia el backend. El refresco de SENA/Sapiencia revisa fichas ya guardadas mientras el servidor está abierto; no publica cursos automáticamente. Desde el catálogo administrativo puedes buscar e incorporar otros programas del SENA.

GitHub y Codewars se consultan desde **Mi perfil → Evidencias → Otras fuentes de evidencia** o el apartado de programación, según el perfil. Son opcionales. Solo consultan información pública y no verifican por sí mismos la autoría ni el dominio de una habilidad.

La guía detallada para comenzar las dos integraciones está en [ACTIVAR_YOUTUBE_MICROSOFT.md](ACTIVAR_YOUTUBE_MICROSOFT.md).

## 10. YouTube: activado y comprobado localmente

Para configurar de nuevo el conector:

1. Crea o elige tu proyecto de Google Cloud.
2. Habilita **YouTube Data API v3**.
3. Crea una clave y restríngela a esa API. No la copies al chat ni al frontend.
4. Configura en `.local/backend.env`:

```dotenv
YOUTUBE_LEARNING_ENABLED=true
YOUTUBE_API_KEY=tu_clave_privada
YOUTUBE_LEARNING_DAILY_REQUESTS=100
```

5. Reinicia el backend y recarga Administración → Catálogo educativo → Fuentes y conectores → YouTube.
6. Consulta una lista pública. Revisa la muestra de vídeos y redacta una ficha propia antes de incorporarla.

El límite local es por proceso y día UTC; consulta también la cuota real del proyecto de Google. No se descargan vídeos, no hay búsqueda masiva y no se atribuye una certificación a una lista. El 13 de octubre de 2026 se activó en el entorno privado local y se comprobó una vista previa real de una lista pública. Las credenciales no se incluyen en esta guía ni en Git.

## 11. Microsoft Learn: acceso comprobado localmente

1. Registra una aplicación en Microsoft Entra y verifica que tiene acceso autorizado a Learn Platform API.
2. Obtén el tenant, el identificador de aplicación y un secreto vigente.
3. Configura privadamente:

```dotenv
LEARN_ENABLED=true
LEARN_TENANT_ID=uuid_del_directorio
LEARN_CLIENT_ID=uuid_de_la_aplicacion
LEARN_CLIENT_SECRET=secreto_privado
```

4. Reinicia el backend. En Fuentes y conectores → Microsoft Learn, consulta módulos o rutas e importa una selección.
5. Revisa el mapeo de habilidades antes de publicar. Completar un plan local no verifica credenciales de Microsoft.

El 13 de octubre de 2026 se comprobó el acceso real de la aplicación: la primera página devolvió 19 módulos importables y una página siguiente. Las pruebas no incorporaron ni publicaron recursos. La configuración de otro entorno depende del acceso que Microsoft conceda a su aplicación. No crea ni requiere desplegar TalentSync en Azure. Conserva LEARN_ENABLED=false si no dispones de esa configuración.

## 12. Correo y acceso social opcionales

**Correo:** `scripts/local.py` mantiene el buzón local y fuerza apagados Resend y SMTP. Cambiar RESEND_ENABLED en el archivo no convierte las cuentas ficticias en destinatarios reales. Puedes ver el diseño sin enviar correos:

```powershell
backend/.venv/Scripts/python.exe scripts/resend_test.py --preview
```

La prueba aislada de Resend usa `.local/resend.env`, `onboarding@resend.dev` y un único destinatario autorizado. El script impide repetir un envío ya aceptado. No borres su registro para reenviar accidentalmente. No necesitas dominio para continuar revisando localmente; el envío general con dominio propio es una etapa distinta.

**Acceso social:** si quieres Google o GitHub, registra una aplicación OAuth en el proveedor y usa sus variables OAUTH_GOOGLE_CLIENT_ID/OAUTH_GOOGLE_CLIENT_SECRET u OAUTH_GITHUB_CLIENT_ID/OAUTH_GITHUB_CLIENT_SECRET en el archivo privado. Registra exactamente estos retornos para el origen local actual:

```text
http://127.0.0.1:5173/api/v1/auth/social/google/callback
http://127.0.0.1:5173/api/v1/auth/social/github/callback
```

Reinicia el backend. No es necesario activar acceso social para revisar las cuentas locales existentes.

## 13. Comprobar la instalación

```powershell
backend/.venv/Scripts/python.exe scripts/local.py doctor
backend/.venv/Scripts/python.exe scripts/local.py verify
```

Los informes agregados están en `.local/verification/`. La verificación usa bases temporales y no envía correos ni despliega la aplicación. Conserva los archivos privados de configuración fuera de Git.

## Revisión del diseño y acceso

En **Mi desarrollo**, el área de aprendizaje se elige con tarjetas e iconos; puedes cambiar entre tu perfil y otras áreas. En **Seguridad de cuenta**, usa la navegación lateral para Correo y acceso, Verificación en dos pasos y Dispositivos; el candidato también tiene Privacidad. Los dispositivos se organizan en sesiones activas/cerradas y páginas de seis. La verificación en dos pasos continúa pausada durante la revisión local.

Después de actualizar, recarga la página con Ctrl+F5 para cargar los estilos actuales.

El 13 de octubre de 2026 se incorporó una muestra activa al catálogo local: seis rutas editoriales de YouTube (Excel, Power Query, Word, Python, Git y SQL) y seis módulos de Microsoft Learn (tres de Power BI, privacidad, riesgos y procesamiento de facturas con AI Builder). Puedes encontrarlos con el filtro Proveedor en la biblioteca administrativa. La duración de las rutas de YouTube es una estimación de estudio y práctica de TalentSync; no equivale a la reproducción total de cada lista.

## Aprendizaje: intentos, resultados y certificados aportados

- Los cursos se muestran en tres columnas en escritorio. Las horas se presentan con un decimal como máximo. Los filtros conservan proveedor, coste, idioma, nivel y certificado; se retiraron los accesos rápidos duplicados.
- En el laboratorio, Guardar borrador conserva respuestas sin corregirlas ni mostrar soluciones. Puedes avanzar aunque una respuesta sea incorrecta.
- Al entregar las tres actividades se guarda una puntuación. Se explican los aciertos; los errores indican qué actividad reforzar sin entregar la solución. Para modificar las respuestas usa Volver a intentarlo. Los intentos anteriores permanecen en Mis resultados, incluso si abandonas el plan después.
- Una práctica acertada puede publicar una evidencia declarada. Estas prácticas se distinguen de las evaluaciones independientes de fundamentos y de completar un curso externo.
- Mis resultados incluye intentos/prácticas, certificados aportados y evaluaciones. Añadir habilidades a mi perfil es una decisión explícita y las incorpora como declaradas, no verificadas. También puedes hacerlo desde una evidencia existente.
- El plan reconoce el certificado que ya aportaste y permite consultar o editar sus datos. Los recursos sin certificado anunciado se muestran como aprendizaje personal. TalentSync no valida certificados ni promete comprobar su autenticidad.
- Cuando una empresa tiene permiso para ver el perfil completo, puede abrir los documentos aportados. La selección ciega conserva su restricción de identidad.
- Microsoft Learn incorpora el idioma y nivel informados por la API, descripción limpia, duración y requisitos/unidades cuando el proveedor los entrega. Los campos ausentes remiten a la fuente; no se inventan temarios. Las fichas editoriales de YouTube conservan descripciones propias de TalentSync.


## Prácticas adaptadas y controles de aprendizaje

La selección de áreas está resumida por defecto; Cambiar área despliega opciones compactas. Los filtros de formación y vacantes incluyen un botón de restablecimiento con icono, y las señales de compatibilidad muestran ayuda al pasar el cursor, enfocarlas con el teclado o pulsar su icono.

Añadir habilidades se ofrece en Mi perfil → Evidencias de mi experiencia. Los planes y resultados conservan sus enlaces al perfil, sin repetir esa acción ni añadir habilidades al entregar una práctica.

Las prácticas complementarias se eligen por título, temario disponible, habilidades y descripción, con bancos locales por tema. El nivel determina la complejidad del cálculo; la duración amplía el caso, los pasos y los conceptos. La ficha muestra el nivel usado y el tiempo aproximado de práctica. Si no se puede identificar un tema específico, se indica que es una práctica de transferencia al área. No se presentan estos ejercicios como exámenes del proveedor ni como una cobertura completa de su curso.

Cada intento conserva sus preguntas y soluciones solo en el servidor. Una edición de la ficha no cambia un intento empezado; al iniciar otro se usa la ficha actual. Los borradores anteriores a este cambio conservan el banco original hasta iniciar un nuevo intento.


## Extracción contextual y compatibilidad por requisito

El motor `contextual-match-v6` compara cargos/profesión, funciones y conocimientos declarados por separado con el mismo modelo local. La formación y los idiomas mantienen sus señales específicas. En Recomendaciones → Compatibilidad y formación → Ver cumplimiento por requisito se muestra el respaldo de cada habilidad, su cumplimiento y la experiencia relacionada.

La extracción distingue menciones de uso, aprendizaje, proyectos y negación en español/inglés. Las menciones que solo aparecen en cursos, proyectos o aprendizaje no se incorporan automáticamente como habilidades dominadas. Mi perfil muestra su fragmento para revisión. Son reglas de contexto auditables combinadas con similitud semántica local; no es un nuevo modelo neuronal de extracción ni una garantía de precisión.

Cada habilidad puede quedar cumplida con datos declarados (100), parcial por uso explícito en la descripción de una evidencia/proyecto (70), conflicto con lo declarado (50), aprendizaje (35), o sin cumplimiento registrado (0). Una base relacionada se explica, pero no suma cobertura de otra habilidad; las etiquetas de una evidencia sin contexto de uso tampoco suman. Es una escala inicial explícita de respaldo; no mide nivel de dominio ni verifica certificados. Los pesos de requisitos siguen siendo los configurados por la empresa. Las condiciones imprescindibles laborales se mantienen separadas.

La experiencia mínima se lee del campo de la oferta o de un requisito numérico explícito. Se unen los meses de cargos relacionados sin duplicar periodos simultáneos. El total mide tiempo en esos cargos, no meses de uso probado de cada herramienta. Las fechas solo con año se muestran aproximadas; la falta de fechas no se interpreta como trabajo actual ni como experiencia suficiente. Si se exige un mínimo positivo, el tiempo relacionado ocupa el 20% de la señal de contexto, dentro de los pesos existentes.

Una nueva carga conserva registros previos y enlaces aportados. El contexto original del CV se devuelve solo en el perfil propio; el desglose público de compatibilidad no incluye fragmentos del CV ni empleadores. La versión y el mes del cálculo invalidan cachés antiguas para periodos actuales. Los perfiles existentes se recalculan al consultar; no se modifican masivamente sus habilidades ni se reimportan sus CVs.

## Recomendaciones para mejorar la hoja de vida

Mi perfil muestra recomendaciones dentro de «Qué mejorar». Se presentan tres recomendaciones prioritarias y una opción para desplegar las demás: explicar el aporte de una experiencia, precisar fechas, completar formación, priorizar habilidades y revisar contactos distintos en el texto disponible del PDF. Los intervalos entre empleos solo se calculan con meses completos; explicarlos es opcional y no reduce la compatibilidad. Cada consejo lleva al campo correspondiente. Se recalculan al guardar el perfil, sin puntuación de empleabilidad.

«Mejorar un texto» utiliza un modelo generativo local para proponer otra forma de contar la experiencia y una pregunta sobre un detalle que falta. El resultado adicional es opcional. El candidato compara, edita y decide si usar la propuesta; puede deshacer mientras esa experiencia siga intacta. Preparar un texto no modifica el perfil. La ruta anterior STAR se conserva para compatibilidad, pero no es la interfaz principal. No se presenta la sustitución de puntuación como generación con IA.

`skill-context-v2` separa aprendizaje explícito, formación, proyectos, falta de experiencia y contexto por confirmar. Solo una frase explícita como «estoy aprendiendo» activa aprendizaje; «Educación», «Cursos», «Fundamentos de» y «Machine learning» no lo activan por sí solos. Se muestran el motivo y el fragmento de origen. Los encabezados de contacto, habilidades y tecnologías detienen el alcance de formación; los encabezados mezclados quedan como contexto incierto.

Las importaciones antiguas se reinterpretan al consultar: si una etiqueta de aprendizaje solo estaba sustentada por el encabezado anterior, se marca contexto por confirmar. No se cambian habilidades declaradas ni se requiere volver a subir el CV para esta corrección. Las nuevas cargas conservan hasta 30.000 caracteres del texto original en las preferencias privadas para mantener el contexto; no se incluye ese campo en el perfil de empresa. Los motivos también se usan al recalcular la compatibilidad con versión v6.

El panel anterior de detecciones neuronales se retiró y GLiNER ya no se ejecuta al cargar un CV. Los archivos y comandos experimentales (`cv-runtime`, `cv-model-prepare`, `cv-model-check`, `cv-evaluate`) siguen disponibles para investigación local; sus rutas `CV_ENTITY_MODEL_PATH` y `CV_ENTITY_PYTHON` están desactivadas en este entorno. La evaluación anterior está documentada en `EVALUACION_EXTRACCION_CV.md`. El modelo local de matching continúa activo.

## Ayuda distribuida por tarea

El perfil muestra los apartados en una vista continua, con trayectoria a la izquierda y habilidades, formación complementaria y preferencias a la derecha; en móvil se apilan. El indicador circular conserva el porcentaje legible. La barra de subir CV, diseñar/exportar y editar/guardar permanece visible al desplazarse. El botón **Ideas para mejorar tu hoja de vida** está en la cabecera y abre un diálogo modal con foco contenido, cierre con Escape y retorno al botón. Las ediciones de una propuesta se conservan al cerrar el modal durante la misma visita.

**Diseñar y exportar** reúne la foto, tres tarjetas de diseño, colores con nombre y casillas por sección (contacto, resumen, experiencia, educación, cursos, habilidades, idiomas, preferencias y muestras de trabajo). La vista previa es el PDF real generado mediante ReportLab 4.4.9 y Pillow 12.3.0; la descarga reutiliza exactamente sus bytes. Cada cambio cancela la solicitud anterior y bloquea la descarga hasta disponer del documento actualizado. Las opciones del PDF y los borradores del editor no modifican el perfil guardado. Subir una foto sí la guarda en el perfil y se indica junto al control. El nombre y la profesión siempre se incluyen. Las fuentes Unicode admiten acentos y el documento pagina su contenido; se verificaron los tres estilos con datos ficticios y foto. No se garantiza compatibilidad con todos los ATS.

**Completa tus habilidades** convierte las menciones del CV en acciones: «La conozco» añade una habilidad declarada, «Ver formación» abre el catálogo y «Descartar» oculta la mención con opción de recuperarla. El fragmento original permanece disponible en un detalle. Solo se aceptan menciones del CV de la cuenta autenticada. Las decisiones privadas se guardan en `preferences.cv_mention_decisions`, sin migración nueva ni cambios al texto original. Confirmar no acredita dominio ni certifica la habilidad; durante una edición se pide guardar primero para evitar perder cambios.

- **En Mi perfil:** propuestas desde una experiencia, resultado adicional opcional, comparación editable, guardar y deshacer. «Guardar y continuar» conserva las ediciones pendientes. Las últimas 20 propuestas quedan en un historial privado.
- **En Mi desarrollo → Qué aprender:** elige primero una habilidad; luego explora sus cursos en un panel contiguo. Las habilidades por explorar y las ya declaradas tienen vistas separadas. Los filtros visibles incluyen cargo, selector de sector y ubicación con sugerencias, búsqueda y restablecimiento. Las fuentes se presentan en un detalle con cifras, fechas, etiquetas y tarjetas de ofertas de ejemplo. Se usan vacantes activas de los últimos 90 días y se eliminan duplicados por empresa/cargo/ubicación. Con menos de cinco ofertas se omiten porcentajes.
- **Dentro de cada vacante:** el botón **Destaca tu hoja de vida**, junto a los requisitos y la postulación, abre un modal de recomendaciones de solo lectura sobre requisitos y experiencia. Los enlaces llevan a los campos habituales del perfil. Cambiar de vacante reinicia el estado y cancela las consultas anteriores, evitando consejos acumulados o respuestas tardías de otra oferta. No prepara presentaciones, no guarda versiones alternativas y no modifica la postulación. Recomendaciones presenta cada oferta en una tarjeta con empresa, ubicación, compatibilidad y una acción principal; conserva los filtros y cálculos existentes.
- Se retiraron la creación y edición de presentaciones por vacante y su exportación. Sus antiguos endpoints devuelven HTTP 410. Las nuevas postulaciones rechazan `coach_draft_id`; se usa el perfil habitual. La descarga general mantiene el estilo y el color elegidos.
- La lectura técnica del PDF no se muestra en el perfil. Los endpoints privados de diagnóstico conservan lectura autenticada, sin OCR ni garantías sobre otros ATS.

La migración `0041_career_coach` sigue conservando el historial privado de redacción y las copias históricas de postulaciones anteriores. Esas copias no se borran ni se modifican al retirar la función; las empresas autorizadas mantienen la consulta con las reglas de selección ciega. La compatibilidad base usa el perfil actual registrado.

### Carga de recomendaciones

Se recalculan solo las vacantes ausentes, vencidas o cuyo contenido/versionado cambió. Cambiar el perfil invalida las puntuaciones pertinentes. Los textos neuronales faltantes se preparan por lotes; la caché de vectores está limitada a 2.048 entradas en memoria (hashes y vectores, sin texto original). Las relaciones necesarias para confianza empresarial se cargan por lotes. Inicio, Recomendaciones y Explorar comparten peticiones simultáneas por cuenta, sin guardar respuestas después de completarse. El cálculo no se repite automáticamente tras un timeout; se ofrece Reintentar. Explorar muestra el catálogo mientras calcula compatibilidad, sin presentar puntuaciones pendientes como 0% ni mensajes falsos de ausencia de vacantes.

Comparación local con el mismo perfil ficticio y 52 vacantes, motor MiniLM inicializado: un recálculo por una entrada vencida pasó de 0,389 s/55 consultas SQL a 0,046 s/7 consultas, con diferencia de puntuaciones 0. El cálculo completo sin vectores previos se mantuvo alrededor de 8,5 s; una consulta con caché vigente tomó unos 0,04 s dentro del proceso. La carga inicial del modelo y el tiempo HTTP se miden por separado. Son observaciones de este equipo, no garantías de rendimiento. Los informes privados están en `.local/verification/vacancy-performance.json` y `profile-revision-api.json`.

## IA de redacción sin API de pago

Ejecuta `backend/.venv/Scripts/python.exe scripts/career_writer_local.py` y reinicia la API local. El comando prepara dentro de `.local/career-writer` el modelo Qwen2.5-1.5B-Instruct Q4_K_M (aproximadamente 1,1 GB) y un runtime CPU de llama.cpp. Se descargan de sus repositorios oficiales con revisión/versiones fijadas y hashes SHA-256 comprobados. No se instala un servicio global ni se usa una cuenta de facturación. Se conservan los demás valores de `.local/backend.env`; nunca se lee `backend/.env`.

Las rutas privadas `CAREER_WRITER_MODEL` y `CAREER_WRITER_EXECUTABLE` habilitan el generador. La generación ejecuta un proceso local, sin cliente HTTP ni proveedor remoto, y solo recibe el cargo, las tareas, la condición de empleo actual y el resultado opcional. El prompt temporal se elimina al terminar y no se registra en logs. Solo se prepara una propuesta a la vez, con límite de tiempo. En las pruebas unitarias estas rutas permanecen vacías y se utilizan dobles de prueba, sin cargar pesos.

La IA puede equivocarse. Se bloquean cifras y herramientas nuevas reconocibles, se conservan negaciones y el nivel de apoyo y se filtran frases promocionales sin respaldo. La descripción se divide en responsabilidades y se genera una acción por cada una, sin el antiguo límite de resumen de 100 palabras. Cada acción se comprueba por separado; si pierde detalles o añade afirmaciones no respaldadas, se conserva esa responsabilidad original y se informa al candidato. Un resultado adicional se incorpora tal como lo aportó la persona. Esto conserva la cobertura, pero no sustituye una revisión de calidad humana. Esos controles no demuestran la veracidad de un texto: la persona debe revisarlo antes de guardarlo. Si el perfil cambia mientras se genera, la propuesta se rechaza para evitar sobrescribir datos. Si el modelo falla, falta o se agota el tiempo, se informa del problema y no se sustituye silenciosamente por reglas ni por una API de pago. La latencia depende del equipo y del número de responsabilidades; una prueba con cuatro acciones tomó unos 27 segundos. No se prometen logros inexistentes ni texto más largo cuando falten hechos.

Modelo y licencia: https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF. Runtime CPU: https://github.com/ggml-org/llama.cpp/releases/tag/b11609. La evolución y la evaluación de calidad están en `PLAN_COACH_CARRERA.md`.
