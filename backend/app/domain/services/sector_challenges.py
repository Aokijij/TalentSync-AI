"""Original occupational cases. Separate item pools per level, without course filters.

These assess bounded tasks, not professional licensure or legal/clinical competence.
"""
from copy import deepcopy

# id, area, skill, related skills, scope. Existing v2 banks remain immutable.
TRACKS = [
    ("javascript", "technology", "javascript", ["js", "programacion web"], "Tipos, colecciones, asincronía y validación"),
    ("typescript", "technology", "typescript", ["ts"], "Tipos, uniones, contratos y comprobaciones en ejecución"),
    ("react", "technology", "react", ["reactjs", "react.js"], "Estado, componentes, listas, formularios y efectos"),
    ("git-workflow", "technology", "git", ["control de versiones"], "Ramas, revisión, recuperación y colaboración"),
    ("linux", "technology", "linux", ["sistemas operativos", "administracion de sistemas"], "Archivos, permisos, procesos y diagnóstico"),
    ("networks", "technology", "redes", ["redes informaticas", "networking"], "Direccionamiento, resolución de nombres y diagnóstico"),
    ("data-analysis", "technology", "analisis de datos", ["estadistica", "business analytics"], "Calidad, muestras, métricas e interpretación"),
    ("power-bi", "technology", "power bi", ["powerbi", "dax"], "Power Query, modelos, medidas y filtros"),
    ("responsible-ai", "technology", "inteligencia artificial", ["ia generativa", "alfabetizacion en ia"], "Verificación, límites, datos y supervisión de resultados"),
    ("project-management", "administration", "gestion de proyectos", ["planificacion", "scrum", "agile"], "Alcance, dependencias, riesgos y seguimiento"),
    ("human-resources", "administration", "gestion del talento humano", ["recursos humanos", "reclutamiento", "seleccion de personal"], "Criterios de selección, entrevistas y registros de equipo"),
    ("digital-marketing", "sales", "marketing digital", ["mercadeo", "marketing", "publicidad digital"], "Objetivos, embudos, campañas y medición"),
    ("crm", "service", "crm", ["gestion de clientes", "seguimiento comercial"], "Contactos, oportunidades, historial y calidad de datos"),
    ("entrepreneurship", "sales", "emprendimiento", ["modelo de negocio", "plan de negocios"], "Problema, propuesta, validación y sostenibilidad"),
    ("cost-accounting", "finance", "contabilidad de costos", ["costos", "contabilidad", "presupuestos"], "Costes, contribución, bases y control presupuestario"),
    ("procurement", "logistics", "compras", ["abastecimiento", "gestion de proveedores", "supply chain"], "Requisitos, propuestas, recepción y seguimiento de proveedores"),
    ("quality", "industry", "control de calidad", ["gestion de calidad", "mejora continua"], "Criterios de aceptación, registros y análisis de desviaciones"),
    ("workplace-safety", "industry", "seguridad y salud en el trabajo", ["sst", "prevencion de riesgos"], "Identificación y comunicación de peligros; sin habilitación profesional"),
    ("hospitality", "hospitality", "recepcion hotelera", ["hoteleria", "reservas"], "Reservas, disponibilidad, recepción y atención de incidencias"),
    ("farm-records", "agriculture", "gestion de registros agricolas", ["gestion agricola", "trazabilidad agricola"], "Planificación de tareas y trazabilidad documental, sin prescripción agronómica"),
    ("construction-control", "construction", "control documental de obra", ["gestion documental de obra", "programacion de obra"], "Versiones, avances, dependencias y soportes; sin cálculo estructural"),
    ("workplace-english", "general", "ingles laboral", ["ingles", "business english"], "Lectura y comunicación escrita en situaciones de trabajo"),
    ("instructional-design", "education", "diseno instruccional", ["formacion virtual", "e-learning", "planificacion educativa"], "Objetivos, secuencias, actividades y evaluación accesible"),
    ("appointments", "care", "gestion de citas", ["agenda de salud", "servicios administrativos en salud"], "Disponibilidad, confirmación y privacidad de citas; sin decisiones clínicas"),
]

# Each row is an independent authored item: prompt|correct|distractor|distractor|explanation.
CONTENT = {
"javascript": """
¿Qué comparación evita convertir automáticamente los tipos?|===|==|=|La igualdad estricta compara sin coerción de tipos.
¿Qué método transforma cada elemento y devuelve otro array?|map|push|pop|map devuelve un array con el resultado de cada transformación.
¿Qué valor representa una variable declarada sin valor asignado?|undefined|null siempre|0 siempre|Una declaración sin asignación tiene el valor undefined.
¿Qué hace const con una referencia a un objeto?|Impide reasignar la referencia, no sus propiedades|Congela todas sus propiedades|Convierte números en texto|La declaración no hace inmutable el objeto referenciado.
¿Qué estructura evita claves duplicadas y conserva valores por clave?|Map|Una cadena|Una fecha|Map mantiene pares de clave y valor con claves únicas.
Una API devuelve "12" como texto y necesitas sumar 3. ¿Qué haces?|Validar y convertir el dato antes de sumar|Concatenar siempre|Asumir que + detecta la intención|La suma requiere controlar el tipo y la validez del dato de entrada.
Una función async falla al esperar una operación. ¿Dónde manejas el rechazo?|Con await dentro de try/catch o un manejador de rechazo|Solo con un comentario|Con un if sobre la promesa sin esperarla|El rechazo debe manejarse en el flujo asíncrono correspondiente.
Una respuesta HTTP tiene estado 404 pero fetch se resuelve. ¿Qué compruebas?|response.ok o el estado antes de usar el contenido|Solo que fetch devolvió algo|Solo el tamaño de la URL|fetch no rechaza automáticamente todos los estados HTTP de error.
El usuario busca rápido y llega primero una respuesta antigua. ¿Qué evita mostrarla?|Cancelar o descartar respuestas que ya no corresponden a la búsqueda|Pintar cualquier respuesta al llegar|Ordenar por tamaño del texto|La respuesta debe pertenecer a la solicitud vigente.
Filtrar un array y modificar sus objetos cambia el original. ¿Por qué?|Los objetos internos siguen compartidos|filter copia profundamente siempre|El array se vuelve una cadena|Crear otro array no copia profundamente sus elementos.
Un cálculo recibe NaN. ¿Qué validación necesitas?|Comprobar que el valor convertido sea finito según el contrato|Compararlo únicamente con cero|Sumar una cadena vacía|Un dato numérico debe validarse antes de producir un resultado.
Un botón tiene dos escuchadores registrados en cada renderizado manual. ¿Qué revisas?|Ciclo de registro y retirada de manejadores|Solo el color del botón|Duplicar más escuchadores|La acumulación de manejadores puede ejecutar la acción varias veces.
Una lista vacía pasa una comprobación if(lista). ¿Por qué?|Los arrays son valores verdaderos; comprueba su longitud|Una lista vacía siempre equivale a false|if cuenta los elementos automáticamente|La existencia del objeto es distinta de contener elementos.
Una propiedad puede estar ausente en una respuesta. ¿Qué debes definir?|Validación y comportamiento explícito cuando falte|Inventar siempre un valor válido|Ocultar todos los errores|La ausencia requiere un tratamiento acorde al contrato.
Un sort numérico sin comparador ordena 10 antes que 2. ¿Qué usas?|Un comparador numérico como (a,b) => a-b|Solo reverse|Convertir todo a booleano|El orden predeterminado no es una comparación numérica general.
""",
"typescript": """
¿Qué describe una interface de TypeScript?|La forma esperada de un dato|Una validación de servidor automática|Una tabla de base de datos|Los tipos describen contratos para el análisis estático.
¿Qué ventaja tiene unknown frente a any al recibir datos externos?|Exige comprobar el valor antes de usarlo|Acepta cualquier operación sin comprobar|Siempre convierte a string|unknown obliga a estrechar el tipo antes de operar.
¿Qué significa una unión de string con null?|El valor puede ser texto o null|El valor siempre es texto|La variable no existe|La unión expresa las alternativas permitidas.
¿Qué representa una propiedad opcional con ? en un tipo?|Puede no estar presente|Debe ser siempre null|Es de solo lectura automáticamente|Una propiedad opcional puede estar ausente.
¿Qué hace un genérico en una función?|Relaciona tipos de entrada y salida reutilizables|Ejecuta más hilos|Borra la validación|Permite expresar relaciones entre tipos sin fijar uno concreto.
Un JSON cumple una aserción as User pero trae campos inválidos. ¿Qué faltó?|Validar los datos en ejecución|Añadir más aserciones|Renombrar User|Una aserción no transforma ni valida el contenido recibido.
Una unión tiene éxito y error con distintos campos. ¿Qué ayuda a tratarla?|Un discriminante común y comprobación de cada variante|Acceder a todos los campos sin distinguir|Convertir todo a any|El discriminante permite seleccionar una variante válida.
Un campo puede ser 0 y usas OR lógico con 10 como alternativa. ¿Qué revisas?|Si necesitas ?? para conservar cero|Que cero equivale siempre a ausencia|Eliminar los tipos|El operador OR lógico también sustituye valores falsos que podrían ser válidos.
Una función acepta string o number. ¿Cómo usas métodos de texto?|Comprobar typeof antes de tratarlos como string|Forzar siempre cualquier valor a string sin contrato|Ignorar el compilador|El estrechamiento permite operaciones válidas para la variante comprobada.
Un tipo readonly protege una API del navegador frente a ataques. ¿Es cierto?|No; no sustituye controles en ejecución y servidor|Sí, bloquea las peticiones manipuladas|Sí, cifra la red|Los tipos no son una barrera de autorización.
Una función promete devolver datos pero puede no retornar. ¿Qué revisas?|Todas las ramas y su tipo de retorno|Solo su nombre|Solo el archivo de estilos|El contrato debe coincidir con lo que retorna cada camino.
Un array puede estar vacío y accedes a su primer elemento. ¿Qué defines?|Tratamiento del caso vacío antes de usar el dato|Que siempre tiene elementos|Que el tipo crea un elemento|El tipo del contenedor no garantiza contenido en ejecución.
Cambias una variante de un flujo con tres estados. ¿Qué prueba ayuda?|Comprobar exhaustividad y comportamiento de cada estado|Solo comprobar que compila un archivo|Borrar los estados anteriores|La exhaustividad evita omitir una alternativa del contrato.
Una biblioteca cambia su contrato de respuesta. ¿Qué actualizas?|Tipos, validadores y consumidores afectados|Solo el comentario del paquete|Solo el icono|El contrato debe reflejarse en comprobaciones y usos reales.
Una cadena tiene un identificador vacío aunque su tipo es string. ¿Qué falta?|Una regla de validación del contenido|Otro alias de string solamente|Un cast adicional|El tipo primitivo no expresa todas las reglas del negocio.
""",
"react": """
¿Cómo se transmite información a un componente hijo?|Mediante props|Modificando el DOM de todos los hijos|Con una contraseña de componente|Las props representan entradas del componente.
¿Qué debe ocurrir al cambiar estado mostrado en pantalla?|Usar el mecanismo de actualización del estado|Modificar silenciosamente el objeto existente|Cambiar solo una variable fuera de React|React necesita una actualización de estado para reflejar el cambio.
¿Qué key conviene para una fila que puede reordenarse?|Un identificador estable de la fila|Math.random en cada renderizado|Su posición siempre|La clave estable permite reconocer el elemento entre cambios.
¿Qué controla un input controlado?|Su valor de estado y el manejador de cambios|Solo el atributo placeholder|Solo el color de fondo|El valor mostrado y su actualización deben mantenerse relacionados.
¿Dónde se llaman normalmente los hooks de un componente?|En el nivel superior, sin ramas condicionales|Dentro de cualquier bucle variable|Solo después de un click|El orden de llamada debe mantenerse entre renderizados.
Necesitas incrementar dos veces usando el valor anterior. ¿Qué actualización ayuda?|Usar actualizadores funcionales para cada incremento|Reutilizar dos veces una copia antigua del valor|Modificar directamente la propiedad del estado|El actualizador funcional recibe el valor pendiente correspondiente.
Una lista cambia de orden y las respuestas quedan en otra persona. ¿Qué revisas?|Las keys y la identidad de cada fila|Solo el texto del título|Solo el ancho de la tarjeta|Las claves por posición pueden asociar estado con el elemento equivocado.
Un efecto abre una suscripción. ¿Qué debe devolver cuando corresponde?|Una limpieza que cierre la suscripción|Una copia del CSS|Una llamada para duplicarla|La limpieza evita mantener recursos después de dejar de necesitarlos.
Una petición del perfil anterior termina después de cambiar de usuario. ¿Qué haces?|Cancelar o ignorar la respuesta obsoleta|Mostrarla aunque sea de otra cuenta|Borrar todos los permisos|La respuesta debe corresponder a la identidad y consulta vigentes.
Un valor puede calcularse a partir de props. ¿Qué evalúas antes de duplicarlo como estado?|Derivarlo durante el renderizado si no necesita estado propio|Añadir un efecto siempre|Mantener dos copias independientes sin sincronización|El estado redundante puede quedar desactualizado.
Un componente define otro componente dentro de su función y pierde estado. ¿Qué revisas?|La identidad del tipo entre renderizados|Solo el nombre del archivo|Solo el número de props|Redefinir el tipo puede hacer que React trate la instancia como nueva.
Un formulario falla al guardar. ¿Qué comportamiento conserva trabajo?|Mantener los valores y mostrar un error con reintento|Vaciar todos los campos|Navegar sin explicar|El error no debe borrar una edición que aún necesita guardarse.
Un efecto usa una variable reactiva que cambia. ¿Qué revisas?|Dependencias y ciclo de sincronización|Ocultar todas las advertencias|Usar siempre un array vacío|Las dependencias deben reflejar los valores leídos por el efecto.
Una respuesta de búsqueda llega tarde tras cerrar la vista. ¿Qué evitas?|Aplicar una respuesta que ya no corresponde al flujo activo|Crear más solicitudes al cerrar|Cambiar el estado de otra búsqueda|El ciclo de la petición debe respetar la vigencia de la vista.
Un array de estado requiere añadir una fila. ¿Qué opción conserva la actualización explícita?|Crear otro array con las filas previas y la nueva|Hacer push y no notificar el cambio|Cambiar solo el DOM|La actualización inmutable permite reconocer el nuevo estado.
""",
"git-workflow": """
¿Qué muestra git status?|Estado de archivos y preparación de cambios|La contraseña remota|Todos los cambios futuros|Permite revisar qué está modificado y preparado.
¿Qué compara git diff sin opciones sobre archivos seguidos?|Cambios de trabajo respecto a lo preparado|Todos los repositorios del equipo|Solo la rama remota|La comparación distingue trabajo aún no preparado.
¿Qué representa un commit?|Un registro versionado de un cambio|Una publicación obligatoria en producción|Una copia de credenciales|Un commit conserva un estado identificable del historial.
¿Qué aporta una rama de trabajo?|Una línea de cambios para desarrollar y revisar|Otro usuario con permisos|Un respaldo externo automático|La rama permite separar el desarrollo de cambios.
¿Qué hace git revert sobre un commit compartido?|Crea otro commit que revierte sus cambios|Borra todo el historial|Revoca claves expuestas|Revert permite deshacer conservando la historia compartida.
Una fusión deja conflictos. ¿Cómo continúas?|Revisar ambas intenciones, resolver y comprobar el resultado|Eliminar siempre el trabajo ajeno|Guardar los marcadores como solución|La resolución debe conservar el comportamiento correcto.
Una clave entró en una rama pública. ¿Qué haces sobre la clave?|Revocarla o rotarla|Solo borrar el archivo actual|Cambiar el mensaje del commit|El historial y las copias pueden conservar la credencial.
Un cambio mezcla una corrección y datos personales sin relación. ¿Qué ayuda?|Preparar solo los archivos y fragmentos necesarios|Publicar todo para ahorrar tiempo|Ocultar el diff|Un cambio acotado facilita revisión y evita incluir datos ajenos al propósito.
La rama remota cambió antes de tu push. ¿Qué haces?|Integrar según la política y comprobar el resultado|Forzar siempre sin revisar|Borrar el remoto|La colaboración requiere respetar el trabajo ya compartido.
Una prueba pasa antes de resolver un conflicto. ¿Cuándo la repites?|Después de la resolución que cambia el código|Nunca|Solo al final del año|La resolución puede modificar el comportamiento comprobado.
Un archivo sensible está seguido por Git y lo añades a gitignore. ¿Qué ocurre?|No deja de estar seguido por ese solo cambio|Se borra de todo el historial|Se revocan sus secretos|gitignore no elimina automáticamente archivos ya versionados.
Un rebase modifica commits compartidos. ¿Qué necesitas considerar?|Coordinación y política de reescritura del equipo|Que nunca afecta a otras personas|Que equivale a una copia de seguridad|Cambiar la historia compartida puede exigir acciones a sus consumidores.
Una corrección se necesita en otra rama sin todos sus cambios. ¿Qué evalúas?|Aplicar el commit concreto y revisar dependencias y conflictos|Copiar toda la rama sin comprobar|Borrar pruebas de la otra rama|Un cambio aislado puede depender del contexto de su rama.
Una revisión necesita saber qué cambió. ¿Qué descripción sirve?|Problema, comportamiento resultante y comprobaciones realizadas|Solo «varios cambios»|La lista de secretos del entorno|La revisión necesita propósito y evidencia de funcionamiento.
Debes recuperar una versión conocida. ¿Qué referencia ayuda?|Un commit o etiqueta comprobados|El archivo más reciente por nombre|Una carpeta sin historial|Una referencia versionada identifica el estado que se quiere recuperar.
""",
"linux": """
¿Qué indica pwd?|El directorio de trabajo actual|La contraseña del usuario|El uso de memoria de todos los procesos|Permite conocer desde dónde se resuelven rutas relativas.
¿Qué permite ls -l?|Consultar atributos de las entradas del directorio|Borrar todos sus archivos|Cambiar el usuario administrador|La salida incluye información de permisos y propiedad.
¿Qué representa una ruta absoluta?|Una ruta que parte de la raíz|Una ruta que depende del nombre del usuario siempre|Solo el nombre del archivo|No necesita resolver su inicio respecto al directorio actual.
¿Qué limita un permiso de lectura de archivo?|La posibilidad de leer su contenido según identidad y permisos|La velocidad de internet|El idioma del sistema|Los permisos regulan operaciones sobre archivos y directorios.
¿Qué ayuda a identificar un proceso en ejecución?|Su identificador y contexto de ejecución|El color del terminal|Solo el tamaño del monitor|El PID y el propietario ayudan a identificar el proceso correcto.
Un servicio no responde. ¿Qué revisas antes de reiniciarlo?|Estado, registros y dependencias con alcance autorizado|Borrar sus datos|Cambiar permisos de todo el disco|El diagnóstico debe preceder a cambios que puedan ocultar la causa.
Una aplicación no puede escribir en una carpeta. ¿Qué compruebas?|Usuario efectivo, permisos y espacio disponible|Aplicar permisos totales a todo el sistema|Desactivar todas las cuentas|El fallo puede depender de permisos o recursos; no se corrige abriendo todo.
El disco se llena por registros. ¿Qué solución planificas?|Rotación y conservación acordes a su finalidad|Borrar cualquier archivo al azar|Guardar más copias en el mismo disco|La gestión necesita límites de espacio y conservación.
Un comando debe actuar en una carpeta concreta. ¿Qué verificas?|Ruta resuelta y alcance antes de una operación destructiva|Solo el nombre abreviado|Que el terminal esté maximizado|Las rutas relativas o calculadas pueden apuntar a otro destino.
Un proceso escucha en un puerto inesperado. ¿Qué relacionas?|Puerto, PID y servicio autorizado|Solo la hora del equipo|Solo el teclado|La relación permite diagnosticar qué proceso ocupa el puerto.
Un script falla solo cuando se ejecuta programado. ¿Qué revisas?|Entorno, directorio y permisos de la ejecución programada|Solo su icono|Que el texto tenga más comentarios|La ejecución programada puede tener otro entorno y directorio.
Una variable contiene un secreto. ¿Dónde evitas imprimirla?|Registros y argumentos visibles a otras personas|Solo en el título de la ventana|Solo en los comentarios|La exposición puede ocurrir a través de logs y procesos.
Un archivo cambia de propietario inesperadamente. ¿Qué necesitas?|Investigar origen y corregir con autorización y trazabilidad|Dar permisos a todo el mundo|Eliminar el sistema de registros|La propiedad forma parte del control de acceso y debe revisarse.
Debes detener un servicio gestionado por un supervisor. ¿Qué usas normalmente?|El mecanismo de gestión del servicio según su configuración|Matar todos los procesos con el mismo nombre|Reiniciar toda la red|El supervisor puede reiniciar un proceso detenido fuera de su ciclo de gestión.
Una configuración nueva impide iniciar. ¿Qué facilita recuperarse?|Versión anterior, validación y procedimiento de restauración|Cambiar varios archivos sin registro|Borrar la configuración anterior|La recuperación requiere un estado conocido y verificable.
""",
"networks": """
¿Para qué sirve normalmente DNS?|Resolver nombres a registros de red|Cifrar todos los archivos locales|Asignar permisos de una carpeta|DNS permite localizar servicios mediante nombres.
¿Qué identifica una dirección IP en el contexto de una red?|Una dirección usada para comunicación en esa red|La identidad legal de una persona|Una contraseña universal|Una IP no demuestra por sí sola quién opera el equipo.
¿Qué papel tiene la puerta de enlace predeterminada?|Encaminar tráfico fuera de la red local cuando corresponde|Guardar todos los documentos|Sustituir a DNS siempre|La puerta de enlace conecta con otras redes.
¿Qué expresa un puerto junto a una dirección de destino?|Un punto de acceso a un servicio de transporte|El número de empleados|El tamaño del disco|La dirección y el puerto permiten dirigirse a un servicio concreto.
¿Qué protege HTTPS durante el transporte si se valida correctamente?|La conexión mediante TLS|Todos los errores de la aplicación|Todos los permisos de usuario|El transporte cifrado no sustituye la autorización de la aplicación.
Un servicio responde por IP pero no por nombre. ¿Qué investigas?|Resolución DNS y configuración del nombre|Solo el cable de alimentación|El color de la página|La diferencia orienta a comprobar el nombre y su resolución.
Dos equipos usan la misma IP en una red. ¿Qué riesgo hay?|Conflicto de direccionamiento y comunicación inestable|Más capacidad garantizada|Cifrado doble|Las direcciones en conflicto pueden impedir dirigir el tráfico correctamente.
Un cliente obtiene una dirección inesperada. ¿Qué revisas?|Asignación DHCP y configuración de la red correspondiente|Borrar la base de usuarios|Cambiar el idioma|El origen de la configuración de red debe identificarse.
Un puerto está abierto en el servidor pero falla desde otra red. ¿Qué contrastas?|Escucha, ruta y controles de tráfico entre ambos puntos|Solo la aplicación del teclado|Solo el nombre del usuario|La conexión depende de todas las capas del recorrido.
Un ping no responde. ¿Qué puedes concluir por sí solo?|Que no hubo respuesta ICMP, no que todo servicio esté caído|Que el servidor se borró|Que la contraseña cambió|Un filtro puede bloquear ICMP mientras otros servicios funcionan.
Un certificado TLS no coincide con el nombre solicitado. ¿Qué haces?|Corregir el nombre o certificado válido, sin omitir la comprobación|Desactivar siempre la validación|Compartir la clave privada|La validación del nombre forma parte de la confianza en la conexión.
Una red de invitados accede a archivos internos. ¿Qué revisas?|Segmentación y reglas de acceso|Solo la velocidad anunciada|Solo el nombre del Wi-Fi|La separación debe reflejar los accesos permitidos.
Una avería es intermitente. ¿Qué registro ayuda?|Hora, origen, destino y observaciones reproducibles|Solo «a veces falla»|Contraseñas de todos los equipos|El contexto permite correlacionar el fallo sin exponer credenciales.
Debes cambiar una regla de red. ¿Qué preparación ayuda?|Alcance, validación y recuperación si bloquea tráfico legítimo|Aplicar muchas reglas sin registro|Borrar todas las reglas|Los cambios deben comprobar acceso permitido y bloqueado.
La conexión funciona en una red y no en otra. ¿Qué comparas?|Ruta, DNS, proxy y controles de cada entorno|Solo el tamaño de pantalla|Solo la versión del documento|Comparar entornos permite localizar diferencias relevantes.
""",
"data-analysis": """
¿Qué representa una fila en una tabla bien definida?|Una observación según su granularidad|Siempre una persona|Siempre un mes|La unidad de observación debe definirse antes de analizar.
¿Por qué distinguir ausencia de cero?|Porque significan situaciones diferentes|Porque siempre son equivalentes|Porque ambos deben borrarse|Un dato ausente no demuestra un valor medido de cero.
¿Qué necesita una tasa de conversión?|Numerador y denominador comparables|Solo el número de ventas|Solo el máximo histórico|La tasa debe referirse a la misma población y periodo.
¿Qué describe la mediana?|El valor central al ordenar los datos|Siempre el promedio aritmético|Siempre el valor más frecuente|La mediana es una medida de posición distinta de media y moda.
¿Qué debes revisar antes de eliminar duplicados?|Clave y regla que define una observación única|Solo el color de la fila|Solo que dos importes coincidan|Dos filas parecidas no son necesariamente la misma observación.
Una encuesta solo responde a tus clientes más activos. ¿Qué límite señalas?|Sesgo de selección respecto a todos los clientes|Representatividad nacional automática|Que el tamaño elimina todo sesgo|La forma de seleccionar la muestra condiciona a quién representa.
Dos variables crecen juntas. ¿Qué no puedes afirmar solo con esa relación?|Que una causa la otra|Que existe una asociación observada|Que conviene investigar el contexto|Una correlación por sí sola no identifica una causa.
El promedio cambia mucho por un valor extremo. ¿Qué revisas?|Distribución, calidad y medidas complementarias|Eliminarlo siempre sin investigar|Publicar solo el mayor valor|Un extremo puede ser un error o una observación legítima relevante.
Dos periodos tienen distinta cantidad de días. ¿Qué haces al comparar ventas?|Aclarar la base temporal y usar métricas comparables|Comparar solo los totales sin contexto|Duplicar el periodo menor|La exposición temporal afecta la interpretación del cambio.
Un gráfico empieza en un valor que exagera una variación. ¿Qué revisas?|Escala y contexto para comunicar la magnitud con claridad|Solo la tipografía|Solo el tamaño del archivo|La escala puede cambiar la percepción del resultado.
Un modelo se evalúa con los mismos datos usados para ajustarlo. ¿Qué riesgo hay?|Sobreestimar su capacidad fuera de esa muestra|Garantizar mejor generalización|Evitar cualquier error|La evaluación debe representar el uso en datos no vistos.
Un informe combina monedas distintas sin convertir. ¿Qué falla?|Comparabilidad de los importes y sus unidades|Solo el idioma|Solo el orden de filas|La unidad de medida debe ser coherente al agregar valores.
Hay 24 respuestas válidas de 40 invitaciones. ¿Cuál es la tasa de respuesta?|60%|24%|40%|24 dividido entre 40 por 100 equivale a 60%.
Un indicador sube de 30% a 36%. ¿Qué cambio en puntos porcentuales hay?|6 puntos porcentuales|20 puntos porcentuales|66 puntos porcentuales|La diferencia es 36 menos 30, no la variación relativa.
Una conclusión no muestra periodo ni fuente. ¿Qué falta para revisarla?|Procedencia, definición y alcance de los datos|Más decimales solamente|Un color distinto|La trazabilidad permite contrastar cómo se obtuvo el indicador.
""",
"power-bi": """
¿Qué función cumple Power Query en un flujo de datos?|Conectar y transformar datos|Definir contraseñas de todos los usuarios|Imprimir certificados|Power Query organiza pasos de preparación de datos.
¿Qué representa una relación en el modelo?|Una conexión entre tablas mediante columnas|Una copia automática de todas las filas|Un gráfico decorativo|La relación permite propagar filtros según su configuración.
¿Qué distingue normalmente una medida de una columna calculada?|La medida se evalúa en el contexto de la consulta|La medida siempre almacena una fila por registro|La columna cambia la identidad del usuario|El contexto de filtro afecta la evaluación de las medidas.
¿Qué tabla suele contener observaciones de ventas?|Una tabla de hechos con granularidad definida|Una imagen del informe|La lista de contraseñas|Los hechos representan eventos o mediciones del negocio.
¿Qué facilita una tabla de fechas coherente?|Análisis temporal con fechas y atributos consistentes|Eliminar todos los filtros|Convertir ventas en texto|El análisis temporal necesita una base de fechas adecuada.
El informe no refleja filas nuevas del origen. ¿Qué compruebas?|Actualización, pasos y rango de datos incorporados|Solo el color de los gráficos|Solo el título|El resultado depende de que el flujo haya incorporado los datos.
Una relación produce resultados inesperados al filtrar. ¿Qué revisas?|Cardinalidad, dirección y unicidad de las claves|Solo el tipo de icono|Solo el número de páginas|La propagación de filtros depende del modelo.
Un importe se duplica al combinar tablas. ¿Qué analizas?|Granularidad y claves antes de agregar|Multiplicar por un factor arbitrario|Ocultar el total|La combinación puede multiplicar filas si no respeta su unidad de observación.
Una medida cambia al seleccionar una región. ¿Qué explica el cambio?|El contexto de filtro aplicado a la medida|Un certificado nuevo|Un cambio del idioma del sistema|La selección modifica qué datos contribuyen al cálculo.
Un porcentaje divide entre cero en un grupo. ¿Qué necesitas?|Definir el comportamiento y manejar la división adecuadamente|Mostrar siempre 100%|Sustituir cualquier dato por uno|La ausencia de base requiere un tratamiento explícito.
Un usuario no debe consultar todas las regiones. ¿Qué evalúas?|Seguridad de acceso y, cuando corresponda, seguridad por filas|Solo ocultar un gráfico|Solo cambiar el color de la región|La presentación no es un control suficiente de autorización.
Una página contiene demasiados gráficos. ¿Qué priorizas?|Preguntas del usuario y jerarquía de información|Máximo número de colores|Todos los campos disponibles|Un informe útil debe facilitar decisiones y lectura.
El total de una medida no coincide con sumar sus porcentajes por fila. ¿Qué revisas?|Si el total debe recalcularse en su propio contexto|Forzar siempre una suma de porcentajes|Eliminar la fila total|Una medida no aditiva puede requerir otro cálculo al cambiar de contexto.
Una categoría se presenta dos veces por espacios ocultos. ¿Qué haces?|Normalizar y validar las claves en la preparación|Dibujar otra leyenda|Ocultar una categoría sin soporte|La calidad del origen afecta las agrupaciones del informe.
Antes de compartir el informe, ¿qué validación es útil?|Conciliar una muestra y totales con el origen y los permisos|Solo comprobar que abre en tu equipo|Solo cambiar el nombre del archivo|Deben comprobarse los datos, sus definiciones y el acceso autorizado.
""",
"responsible-ai": """
¿Qué significa que una respuesta generada suene convincente?|Que debe verificarse; no demuestra que sea correcta|Que está certificada|Que no necesita fuentes|La fluidez del texto no demuestra exactitud.
¿Qué información conviene limitar en una herramienta de IA?|Datos personales y confidenciales innecesarios|Solo el título del documento|Solo el número de párrafos|El uso debe respetar finalidad, autorización y minimización.
¿Qué mejora una instrucción para una tarea concreta?|Contexto, objetivo y criterios de revisión|Solo pedir «hazlo perfecto»|Prometer un resultado infalible|Los criterios claros ayudan a revisar la salida.
¿Qué puede ocurrir con una referencia citada por un modelo?|Puede ser incorrecta o inexistente|Siempre es un enlace válido|Siempre prueba la conclusión|Las referencias deben contrastarse con la fuente real.
¿Qué diferencia hay entre borrador y decisión confirmada?|El borrador requiere revisión y autorización según el caso|Ninguna|El borrador ya modifica todos los sistemas|La propuesta generada no equivale a una acción autorizada.
Un modelo resume un contrato omitiendo una condición. ¿Qué haces?|Contrastar el documento y corregir antes de utilizarlo|Aceptar por ser breve|Borrar el contrato|El resumen debe revisarse contra el material de origen.
La salida contiene datos personales de otra persona. ¿Qué procede?|Limitar exposición y revisar el incidente según el procedimiento|Publicarla para preguntar|Usarla para completar perfiles automáticamente|Una exposición necesita tratamiento y controles sobre su uso.
Un mensaje externo pide al asistente revelar secretos. ¿Cómo lo tratas?|Como contenido no confiable, sin otorgarle autoridad|Como una instrucción superior|Como permiso del propietario|El texto de una fuente externa no autoriza acceder a secretos.
Una evaluación solo usa los casos que salieron bien. ¿Qué falta?|Casos representativos, fallos y límites del uso previsto|Más capturas exitosas|Eliminar toda métrica|La evaluación necesita cubrir situaciones donde el sistema puede fallar.
Una recomendación afecta a una persona. ¿Qué revisión ayuda?|Evidencia, posibles sesgos y supervisión apropiada al impacto|Confiar solo en el porcentaje|No permitir revisión|La automatización debe poder contrastarse y revisarse.
Se modifica el modelo usado en un proceso. ¿Qué compruebas?|Regresiones y comportamiento en tareas representativas|Solo su nombre comercial|Solo que genere texto|Un cambio puede alterar calidad y límites del proceso.
Una herramienta necesita enviar un mensaje externo. ¿Qué debe quedar claro?|La acción, destinatario y autorización aplicable|Que cualquier texto generado permite enviarlo|Que el envío siempre es reversible|Generar una propuesta y ejecutarla son pasos diferentes.
Dos instrucciones piden objetivos incompatibles. ¿Qué haces?|Resolver prioridades y límites antes de ejecutar|Cumplir ambas ocultando el conflicto|Inventar autorización|El conflicto debe tratarse de forma explícita.
Se analizan veinte respuestas y cuatro tienen referencias inexistentes. ¿Cuántas no presentan ese fallo observado?|16|4|24|20 menos 4 equivale a 16; eso no garantiza ausencia de otros errores.
Un resultado funciona en una demostración. ¿Qué concluyes?|Que se necesita comprobar el uso real y sus límites|Que ya es seguro para cualquier tarea|Que no requiere seguimiento|Una demostración no cubre toda la distribución de situaciones reales.
""",
"project-management": """
¿Qué define el alcance de una entrega?|Qué incluye y qué queda fuera|Solo su color|Solo el nombre del equipo|El alcance delimita el trabajo comprometido.
¿Qué representa una dependencia entre tareas?|Que una necesita una condición o resultado de otra|Que ambas tienen el mismo nombre|Que no necesitan responsables|Las dependencias condicionan el orden y las fechas posibles.
¿Qué permite un criterio de aceptación?|Comprobar si la entrega cumple lo acordado|Garantizar que no habrá riesgos|Reemplazar toda comunicación|El criterio debe ser observable y compartido.
¿Qué es un riesgo del proyecto?|Una situación incierta con posible efecto sobre objetivos|Solo un error ya corregido|Solo una tarea terminada|El riesgo combina incertidumbre y efecto potencial.
¿Qué necesita una acción de seguimiento?|Responsable, plazo y resultado esperado|Solo una etiqueta|Solo un porcentaje|El seguimiento debe permitir comprobar compromisos.
Se pide una función nueva sin cambiar fecha ni recursos. ¿Qué haces?|Evaluar impacto y acordar el cambio de alcance|Aceptarla sin revisar|Ocultarla al equipo|Un cambio puede afectar tiempo, coste y otras entregas.
Una tarea de cuatro días depende de otra de tres, sin solapamiento. ¿Qué duración mínima conjunta resulta?|Siete días|Cuatro días|Un día|Las duraciones se suman cuando la segunda empieza al terminar la primera.
El avance dice 90% durante tres semanas. ¿Qué revisas?|Entregables verificables y trabajo pendiente|Solo cambiarlo a 95%|Solo el color del indicador|El porcentaje necesita una base que permita contrastar el progreso.
Una persona acumula todas las tareas críticas. ¿Qué riesgo investigas?|Capacidad, continuidad y concentración de dependencias|Solo estilo de su agenda|Solo antigüedad|La concentración puede afectar la viabilidad del plan y su recuperación.
Una entrega terminó pero nadie la aceptó. ¿Qué falta?|Revisión y aceptación según los criterios acordados|Otra etiqueta de estado|Cambiar el nombre del archivo|Terminar una actividad no equivale a aceptar su resultado.
Un problema ya ocurrió y bloquea el trabajo. ¿Cómo lo registras?|Como incidencia con acción y seguimiento|Solo como riesgo hipotético futuro|Como tarea completada|Una incidencia requiere gestionar una situación existente.
Se decide una prioridad en una reunión. ¿Qué conservas?|Decisión, motivo y efectos en el plan|Solo lista de asistentes|Solo el enlace de la llamada|La trazabilidad permite explicar por qué cambió el trabajo.
Una estimación no incluye pruebas ni revisión. ¿Qué debes ajustar?|El esfuerzo necesario para completar y aceptar|Solo el formato del número|Solo la descripción comercial|La estimación debe cubrir el trabajo requerido por la definición de terminado.
Un proveedor retrasa una dependencia. ¿Qué comunicas?|Impacto, alternativas y próximo compromiso verificable|Solo una disculpa al final|Una fecha sin confirmar|El equipo necesita información para decidir cómo responder al retraso.
Al cerrar el proyecto, ¿qué facilita futuros trabajos?|Resultados, pendientes transferidos y aprendizajes documentados|Borrar el historial|Solo celebrar la entrega|El cierre debe permitir continuidad y aprendizaje.
""",
"human-resources": """
¿Qué conviene definir antes de revisar candidaturas?|Criterios relacionados con las tareas del cargo|Preferencias personales sin relación con el trabajo|Solo una fotografía|La selección debe apoyarse en requisitos pertinentes y evidencias.
¿Qué aporta una entrevista estructurada?|Preguntas y criterios comparables para la misma función|Una decisión automática infalible|La ausencia de notas|La estructura permite contrastar respuestas con criterios comunes.
¿Qué distingue una habilidad declarada de una evaluada?|La evidencia y el alcance de su comprobación|El tamaño de la letra|El nombre del candidato|Una declaración no equivale a haber demostrado la habilidad.
¿Qué debe contener una invitación a entrevista?|Fecha, zona horaria, modalidad y acceso|Solo «nos vemos mañana»|Solo el salario|Los datos completos permiten preparar y asistir a la cita.
¿Qué acceso necesita un entrevistador?|El necesario para sus procesos asignados|Todas las contraseñas del equipo|Todos los expedientes sin límite|Los permisos deben ajustarse a su función.
Dos evaluadores discrepan mucho. ¿Qué revisas?|Evidencias y aplicación de los criterios|Solo promediar sin analizar siempre|Elegir la nota del más antiguo por defecto|La discrepancia puede mostrar interpretaciones distintas de la rúbrica.
Una candidata cumple tareas pero no una preferencia irrelevante. ¿Qué procede?|Revisar pertinencia del criterio antes de decidir|Descartarla por costumbre|Inventar otro motivo|Los criterios deben responder a necesidades justificadas del cargo.
Un candidato espera respuesta tras una entrevista. ¿Qué comunicación ayuda?|Estado confirmado y próximo compromiso|Silencio hasta que pregunte|Un mensaje que afirme una decisión inexistente|El seguimiento debe reflejar el estado real del proceso.
Una nota interna contiene información sensible innecesaria. ¿Qué revisas?|Pertinencia, acceso y conservación|Compartirla con todos|Copiarla al mensaje público|El registro debe limitarse a información necesaria para su finalidad.
Una persona deja la empresa. ¿Qué coordina la salida?|Retirada de accesos, entrega de responsabilidades y registros|Solo cambiar la foto|Compartir su usuario|La salida necesita continuidad y protección de acceso.
Un indicador de contratación usa etapas con definiciones diferentes. ¿Qué haces?|Unificar definiciones antes de comparar|Sumar todos los porcentajes|Elegir solo la cifra favorable|La comparación requiere medir el mismo proceso.
Se reprograma una entrevista. ¿Qué debes actualizar?|Agenda, acceso y comunicación a las personas afectadas|Solo una nota privada|Solo la fecha en tu memoria|El cambio debe ser consistente entre los medios que usan sus participantes.
Una prueba técnica no representa las tareas del cargo. ¿Qué revisas?|Validez del contenido para el objetivo de selección|Solo su dificultad extrema|Solo el número de preguntas|Una evaluación útil debe aportar evidencia pertinente.
Se publica una oferta con responsabilidades ambiguas. ¿Qué mejora?|Resultados esperados y funciones concretas|Más adjetivos sin contenido|Ocultar el alcance|La claridad permite al candidato y al equipo contrastar expectativas.
Un expediente se solicita fuera del proceso autorizado. ¿Qué haces?|Verificar finalidad y autorización antes de compartir|Enviarlo por rapidez|Publicarlo en un canal general|El acceso a datos del candidato requiere un alcance justificado.
""",
"digital-marketing": """
¿Qué necesita una campaña antes de elegir canales?|Objetivo, audiencia y forma de medirlo|Solo una imagen llamativa|Solo el presupuesto máximo|El canal debe responder al objetivo y al público.
¿Qué diferencia un clic de una conversión?|La conversión es la acción objetivo definida|Son siempre equivalentes|El clic garantiza una venta|La métrica debe distinguir interés de resultado esperado.
¿Qué permite una etiqueta de campaña consistente?|Atribuir visitas según una convención|Certificar la identidad legal del visitante|Garantizar rentabilidad|Las etiquetas ayudan a analizar procedencia con reglas consistentes.
¿Qué debe respetar un mensaje comercial?|Condiciones claras y preferencias de comunicación|Solo longitud máxima|Cualquier promesa llamativa|La comunicación debe ser comprensible y respetar sus condiciones.
¿Qué indica la tasa de clics?|Clics respecto a impresiones comparables|Ventas respecto a empleados|Ingresos menos gastos|La tasa relaciona interacciones con su exposición.
Una campaña logra 60 clics de 3000 impresiones. ¿Qué tasa de clics tiene?|2%|20%|60%|60 dividido entre 3000 por 100 equivale a 2%.
Se comparan campañas con objetivos distintos. ¿Qué revisas?|Métrica y población pertinentes a cada objetivo|Solo número de seguidores|Solo el color del anuncio|No todas las campañas buscan el mismo resultado.
Un anuncio promete un precio sin cargos obligatorios. ¿Qué corriges?|Precio total y condiciones antes de la decisión|Solo el tamaño del precio|Ocultar los cargos en otro idioma|La información comercial debe permitir comprender el coste.
Una prueba A/B cambia cinco elementos a la vez. ¿Qué limitación tiene?|Dificulta atribuir el efecto a un cambio concreto|Demuestra qué elemento ganó por separado|Evita toda incertidumbre|El diseño de la prueba condiciona la interpretación del resultado.
Una campaña tiene muchas visitas pero pocas compras. ¿Qué investigas?|Embudo, calidad del tráfico y experiencia posterior|Solo aumentar impresiones|Borrar la métrica de compra|El problema puede estar en distintas etapas del recorrido.
Un informe atribuye ventas de meses anteriores a la campaña actual. ¿Qué falla?|Ventana de atribución y periodo comparable|Solo el título|Solo la moneda|La atribución debe tener un periodo y definición explícitos.
Los resultados provienen de una muestra muy pequeña. ¿Qué comunicas?|Incertidumbre y límites antes de generalizar|Una conclusión definitiva|Que más decimales eliminan la incertidumbre|El tamaño y selección de la muestra condicionan la conclusión.
Un usuario retira consentimiento para mensajes. ¿Qué haces?|Aplicar su preferencia en las herramientas correspondientes|Importarlo de nuevo por otra lista|Cambiar su identificador|Las preferencias deben respetarse de manera consistente.
El coste por conversión baja mientras empeora la calidad de clientes. ¿Qué revisas?|Definición y valor de la conversión|Solo el coste aislado|Solo el número de anuncios|Una conversión barata no garantiza el objetivo del negocio.
Antes de publicar una pieza, ¿qué compruebas?|Mensaje, enlace, accesibilidad y condiciones|Solo que tiene muchos colores|Solo que el archivo pesa poco|El control debe cubrir contenido y funcionamiento del destino.
""",
"crm": """
¿Qué organiza normalmente un CRM?|Relaciones, contactos e historial con clientes|Solo archivos de sistema|Solo diseño de logos|El registro permite continuar la relación con contexto.
¿Qué identifica mejor un contacto dentro del sistema?|Una clave estable y datos contrastados|Solo su posición en una lista|Siempre su nombre de pila|Los nombres pueden repetirse o cambiar.
¿Qué debe mostrar una oportunidad comercial?|Estado y siguiente paso verificable|Solo un color|Solo el último saludo|El estado debe facilitar una acción de seguimiento.
¿Qué ayuda al derivar una solicitud de cliente?|Historial y contexto necesarios|Pedir que repita siempre todo|Enviar contraseñas|El contexto permite continuar sin duplicar trabajo.
¿Qué debe respetar la comunicación del CRM?|Preferencias y autorización aplicables|Solo la hora del agente|Cualquier dato importado como permiso|Tener un contacto no equivale a permiso ilimitado de comunicación.
Dos fichas parecen del mismo cliente. ¿Qué haces antes de fusionar?|Verificar identidad y reglas de deduplicación|Fusionar por nombre solamente|Borrar una al azar|La fusión incorrecta puede mezclar personas e historiales.
Una oportunidad figura ganada sin aceptación del cliente. ¿Qué revisas?|Evidencia y definición de la etapa|Solo el tamaño del importe|Solo la fecha actual|El estado debe reflejar un hecho comprobable del proceso.
Un agente sale del equipo y deja seguimientos pendientes. ¿Qué coordinas?|Reasignación y conservación del historial|Borrar los contactos|Compartir su contraseña|La continuidad debe mantenerse con identidades y permisos propios.
Un reporte cuenta la misma oportunidad varias veces por sus actividades. ¿Qué falla?|Granularidad y deduplicación del informe|Solo el título del gráfico|Solo el número de agentes|Actividades y oportunidades son unidades de análisis diferentes.
Se solicita exportar todos los contactos para otra finalidad. ¿Qué verificas?|Autorización, necesidad y alcance de los datos|Solo velocidad de descarga|Solo formato de archivo|La exportación debe respetar la finalidad y los permisos.
Una nota dice «cliente difícil» sin hechos. ¿Cómo la mejoras?|Registrar hechos relevantes y acciones de seguimiento|Añadir opiniones personales|Hacerla pública|El historial debe ser útil y pertinente para la atención.
Una integración reenvía dos veces una actividad. ¿Qué control ayuda?|Identificador y tratamiento de duplicados|Cambiar siempre la fecha|Aceptar todas las copias|Las repeticiones no deben inflar actividad ni generar mensajes duplicados.
Un cliente corrigió su correo pero sigue recibiendo mensajes en el anterior. ¿Qué revisas?|Sincronización de datos y preferencias entre sistemas|Solo el asunto|Solo el idioma|La corrección debe propagarse a los sistemas que utilizan el dato.
Hay 50 oportunidades y 10 cerradas con venta en el mismo grupo. ¿Cuál es su conversión?|20%|10%|50%|10 dividido entre 50 por 100 equivale a 20%.
Un registro no tiene próximo paso ni responsable. ¿Qué falta?|Una acción y una persona responsables de continuar|Una etiqueta más vistosa|Otro duplicado de la ficha|El seguimiento debe permitir saber quién hará qué.
""",
"entrepreneurship": """
¿Qué debe aclarar una propuesta de valor?|Problema, destinatario y beneficio relevante|Solo un eslogan|Solo el nombre del negocio|La propuesta debe responder a una necesidad identificable.
¿Qué aporta una entrevista de descubrimiento?|Evidencia sobre necesidades y contexto|Una venta garantizada|Una aprobación legal automática|La conversación ayuda a contrastar supuestos, no garantiza demanda.
¿Qué representa un coste fijo en un periodo relevante?|Un coste que no varía directamente con el volumen dentro de ese alcance|Un coste que nunca cambia en la historia|Siempre un coste por unidad|La clasificación depende del periodo y rango de actividad.
¿Qué describe un canal de llegada al cliente?|Cómo se alcanza y atiende al público objetivo|Solo el logotipo|Solo la oficina|El canal conecta la propuesta con sus destinatarios.
¿Qué permite un experimento pequeño?|Contrastar un supuesto con criterio definido|Eliminar todo riesgo|Demostrar dominio de todo el mercado|El experimento necesita una pregunta y evidencia observables.
Muchas personas elogian una idea pero nadie compra. ¿Qué investigas?|Disposición real a pagar y barreras de adopción|Solo más elogios|Dar por validado el negocio|El interés declarado no equivale necesariamente a una compra.
El ingreso sube pero falta efectivo para pagar. ¿Qué revisas?|Flujos de cobro, pago y obligaciones|Solo el número de seguidores|Solo ingresos facturados|Rentabilidad e ingreso contable no equivalen a liquidez disponible.
Una venta aporta 30 y su coste variable es 18. ¿Qué contribución por unidad queda?|12|48|18|La contribución es ingreso menos coste variable: 30 menos 18.
Un experimento no define qué resultado cambiaría la decisión. ¿Qué falta?|Criterio de evaluación y siguiente decisión|Más nombres de producto|Más colores|La evidencia debe permitir decidir qué hacer después.
Un solo cliente concentra casi todos los ingresos. ¿Qué riesgo consideras?|Dependencia comercial y continuidad|Solo el tamaño del logo|Que no existe riesgo por ser una venta|La concentración puede afectar sostenibilidad si cambia la relación.
Un producto mínimo necesita datos personales. ¿Qué mantienes desde el inicio?|Controles y uso limitado según su finalidad|Exposición pública por ser piloto|Contraseñas compartidas|La condición de piloto no elimina la protección de datos.
El precio se fija sin calcular costes ni valor. ¿Qué revisas?|Costes, alternativas, público y sostenibilidad|Solo la cifra del competidor|Solo el precio más bajo|El precio debe contrastarse con el modelo de negocio.
Una prueba se hace solo con amigos que conocen la idea. ¿Qué límite reconoces?|Posible sesgo de selección y respuestas|Representatividad universal|Ausencia de necesidad de otra evidencia|El grupo puede no representar al público objetivo.
La demanda cambia según temporada. ¿Qué ajustas?|Capacidad y flujo financiero considerando esa variación|Promediar y garantizar ventas constantes|Ignorar los meses bajos|La planificación debe contemplar periodos con comportamientos distintos.
Antes de escalar una solución, ¿qué necesitas comprobar?|Entrega repetible, demanda y viabilidad con sus restricciones|Solo una buena demostración|Solo más gasto publicitario|El crecimiento requiere sostener la promesa a mayor volumen.
""",
"cost-accounting": """
¿Qué diferencia coste total y coste unitario?|El unitario relaciona el total con una base de unidades|Siempre son iguales|El total excluye toda materia prima|La base usada debe ser explícita y pertinente.
¿Qué representa el margen de contribución?|Ingresos menos costes variables según el alcance|Ingresos menos cualquier cifra elegida|Solo el saldo bancario|La contribución ayuda a analizar cobertura de costes fijos.
¿Qué necesita un presupuesto revisable?|Supuestos, periodo y partidas definidos|Solo una cifra final|Solo una imagen|Los supuestos permiten contrastar por qué cambia el resultado.
¿Qué debe tener una asignación de costes indirectos?|Una base de reparto explicada|Un reparto oculto|Siempre el mismo importe por producto|La base elegida afecta la interpretación del coste.
¿Qué debe comprobarse antes de comparar presupuesto y ejecución?|Periodo, alcance y criterios equivalentes|Solo orden alfabético|Solo el color de las cifras|Sin una base comparable, la desviación puede ser engañosa.
Se producen 100 unidades con coste total de 1500. ¿Cuál es el coste medio unitario?|15|150|100|1500 dividido entre 100 equivale a 15 por unidad.
Un producto vende a 50 y tiene coste variable de 32. ¿Qué contribución unitaria aporta?|18|82|32|50 menos 32 equivale a 18 por unidad.
Los costes fijos son 900 y la contribución unitaria 30. ¿Qué volumen los cubre en el caso simplificado?|30 unidades|900 unidades|27000 unidades|900 dividido entre 30 da 30, bajo los supuestos del caso.
La compra de un equipo se compara con consumo mensual sin distinguir partidas. ¿Qué revisas?|Naturaleza, periodo y tratamiento de cada importe|Solo el símbolo de moneda|Solo el proveedor|La comparación requiere clasificar correctamente los conceptos.
Un coste real supera el presupuesto. ¿Qué análisis ayuda?|Separar cambios de precio, volumen y alcance|Asignar una causa sin datos|Ocultar el coste|La desviación puede tener varios componentes que requieren evidencia.
Un presupuesto usa una tasa de cambio no documentada. ¿Qué falta?|Referencia temporal y supuesto de conversión|Más decimales solamente|El nombre del archivo|Las monedas y sus bases deben quedar identificadas.
Se repartió dos veces el mismo coste indirecto. ¿Qué control lo detecta?|Conciliar importes asignados con el total de origen|Aumentar las ventas previstas|Cambiar la categoría del producto|La conciliación evita duplicar costes al distribuirlos.
Una decisión considera solo costes ya incurridos e irrecuperables. ¿Qué revisas?|Costes futuros relevantes y alternativas|Que todo gasto pasado obliga a continuar|Solo la fecha de la compra|Los costes hundidos no deben sustituir el análisis de las alternativas futuras.
Un producto tiene buen margen porcentual pero pocas ventas. ¿Qué contrastas?|Contribución total, capacidad y objetivos|Solo el porcentaje|Solo el nombre comercial|El porcentaje y el aporte total responden preguntas distintas.
Una proyección supone demanda constante sin evidencia. ¿Qué haces?|Analizar escenarios y explicitar la incertidumbre|Presentarla como garantía|Ocultar el supuesto|La decisión necesita conocer la sensibilidad a sus supuestos.
""",
"procurement": """
¿Qué necesitas antes de pedir cotizaciones?|Requisitos y criterios de aceptación|Solo el nombre de un proveedor|Solo el precio deseado|Las propuestas deben responder a una necesidad definida.
¿Qué permite comparar proveedores?|Alcance y condiciones equivalentes|Solo el menor número de la oferta|Solo antigüedad de la marca|La comparación debe incluir prestaciones y condiciones comparables.
¿Qué documento conecta una recepción con lo solicitado?|Pedido o acuerdo y soporte de entrega|Solo una fotografía decorativa|Solo el correo del comprador|La recepción debe contrastarse con el compromiso de compra.
¿Qué debe registrarse si una entrega no cumple?|Diferencia, soporte y acción acordada|Solo una opinión|Marcarla como completa sin revisión|El incumplimiento necesita trazabilidad.
¿Qué incluye el coste de adquirir una alternativa?|Importes y condiciones relevantes definidos para la comparación|Solo precio de portada|Solo el descuento anunciado|El precio aislado puede excluir gastos necesarios.
Una oferta barata exige transporte adicional no incluido. ¿Qué comparas?|Coste total y condiciones de entrega|Solo la cifra inicial|Solo el tamaño del catálogo|Los gastos necesarios pueden cambiar la comparación.
Un único proveedor abastece un insumo crítico. ¿Qué riesgo evalúas?|Continuidad, alternativas y plazo de recuperación|Solo color del empaque|Que no hay riesgo si cumple una vez|La dependencia puede afectar la operación ante una interrupción.
La entrega incluye 80 unidades de 100 pedidas. ¿Qué queda pendiente?|20 unidades|80 unidades|180 unidades|100 menos 80 equivale a 20 por entregar.
Un cambio de especificación llega después de ordenar. ¿Qué haces?|Acordar y registrar impacto y aceptación del cambio|Suponer que el proveedor lo adivina|Rechazar sin revisar el acuerdo|El pedido vigente debe reflejar lo que ambas partes aceptaron.
Un proveedor pide cambiar su cuenta de pago por un mensaje inesperado. ¿Qué procede?|Verificación por el procedimiento autorizado antes del cambio|Cambiarla de inmediato|Compartir credenciales bancarias|Los cambios de datos de pago requieren comprobación independiente.
Una recepción tiene productos dañados. ¿Qué haces?|Separar, documentar y gestionar la diferencia según el acuerdo|Aceptar todos como aptos|Borrar el pedido|La recepción debe distinguir cantidad de condición aceptable.
Los plazos varían mucho entre pedidos. ¿Qué analizas?|Distribución y causas, además del promedio|Solo la entrega más rápida|Solo el importe total|El promedio puede ocultar variabilidad relevante para planificar.
Una evaluación de proveedores solo cuenta cantidad entregada. ¿Qué falta considerar?|Calidad, plazo y condiciones relevantes|Solo número de logos|Solo tamaño del camión|La evaluación debe reflejar los criterios de servicio acordados.
Una compra urgente salta un control obligatorio. ¿Qué haces?|Usar el procedimiento de excepción autorizado y su registro|Ocultarla del sistema|Aceptar cualquier condición|La urgencia no elimina la necesidad de autorización y trazabilidad.
Al cerrar un pedido, ¿qué verificas?|Recepción aceptada, pendientes y documentación pertinente|Solo que salió el pago|Solo que llegó un correo|El cierre debe reflejar el cumplimiento completo del acuerdo.
""",
"quality": """
¿Qué permite un criterio de aceptación?|Decidir si una salida cumple una condición definida|Garantizar cero errores para siempre|Eliminar la inspección necesaria|El criterio debe poder comprobarse con evidencia.
¿Qué representa una no conformidad?|Un incumplimiento respecto a un requisito definido|Cualquier opinión sin criterio|Siempre una sanción personal|La diferencia debe vincularse con el requisito incumplido.
¿Qué debe identificar un registro de inspección?|Objeto revisado, criterio, resultado y responsable|Solo un color|Solo el nombre de la empresa|La trazabilidad permite reconstruir la comprobación.
¿Qué diferencia corregir un defecto de actuar sobre su causa?|La segunda busca evitar recurrencia según la causa comprobada|Son siempre lo mismo|La corrección elimina toda investigación|La corrección inmediata puede no resolver el origen del problema.
¿Qué necesita un instrumento de medición para su uso previsto?|Condición y comprobación adecuadas al procedimiento|Solo que parezca nuevo|Solo una etiqueta vistosa|El resultado depende de usar un medio apto para la medición.
Un lote tiene 6 unidades no conformes de 200 revisadas. ¿Qué proporción se observó?|3%|6%|30%|6 dividido entre 200 por 100 equivale a 3% en la muestra revisada.
Una inspección usa criterios distintos entre turnos. ¿Qué revisas?|Definición, comunicación y aplicación del criterio|Solo el horario|Solo la marca del uniforme|La comparación requiere una evaluación consistente.
Se atribuye un fallo a una persona sin revisar el proceso. ¿Qué haces?|Investigar hechos, condiciones y causas posibles|Cerrar la investigación con una sospecha|Borrar el registro|La causa debe sustentarse en evidencia.
Una mejora reduce un defecto y aumenta otro. ¿Qué evalúas?|Efecto global y posibles consecuencias del cambio|Solo la cifra favorable|Solo el número de reuniones|La mejora debe comprobar el proceso completo relevante.
Una muestra pequeña sale sin defectos. ¿Qué puedes afirmar?|Que no se observaron defectos en esa muestra|Que todo el lote es perfecto con certeza|Que nunca volverá a fallar|La observación tiene límites según muestra y método.
Dos registros del mismo lote tienen identificadores diferentes. ¿Qué riesgo hay?|Perder trazabilidad entre inspección y producto|Mejorar automáticamente el control|Aumentar la precisión|La identidad del objeto revisado debe conservarse.
Se cambia una especificación y siguen usando la anterior. ¿Qué control falta?|Gestión de versiones y comunicación del cambio|Solo otro gráfico|Solo cambiar el archivo de carpeta|El punto de uso debe tener el requisito vigente.
Una acción correctiva se cerró al enviar un correo. ¿Qué falta comprobar?|Implementación y eficacia según el objetivo|Que el asunto era largo|Que todos respondieron con un saludo|El cierre debe verificar el resultado esperado de la acción.
Una métrica mejora al excluir registros difíciles sin criterio. ¿Qué falla?|Integridad y comparabilidad de la medición|Solo presentación|Solo el tamaño de muestra final|La selección de datos no debe ocultar el desempeño del proceso.
Una desviación afecta entregas ya realizadas. ¿Qué necesitas?|Identificar alcance, destinos y tratamiento autorizado|Solo revisar el último producto|Borrar las fechas|La trazabilidad permite delimitar qué salidas pueden estar afectadas.
""",
"workplace-safety": """
¿Qué debe comunicarse al detectar un peligro de trabajo?|Hechos, ubicación y condición observada por el canal previsto|Solo una opinión sobre una persona|Únicamente una foto pública|La comunicación necesita contexto útil sin exponer innecesariamente a personas.
¿Qué diferencia peligro y riesgo en una evaluación básica?|La fuente potencial de daño y la valoración de su posibilidad y efecto|Son siempre dos nombres del equipo|El riesgo es solo el precio|La identificación del peligro precede al análisis de su riesgo.
¿Qué información ayuda antes de una tarea no rutinaria?|Procedimiento, peligros y autorizaciones pertinentes|Solo cuánto tarda|Solo quién terminó primero|La planificación debe considerar las condiciones y controles de la tarea.
¿Qué papel tiene un registro de incidentes?|Conservar hechos para seguimiento y prevención|Sustituir toda atención competente|Publicar datos personales|El registro apoya investigar y actuar dentro del procedimiento.
¿Qué debe hacer quien no está autorizado para una operación de riesgo?|No asumirla y acudir al responsable competente|Improvisar para ahorrar tiempo|Pedir una contraseña ajena|La competencia y la autorización forman parte del control de la tarea.
Se informa un peligro repetido sin acción registrada. ¿Qué revisas?|Responsable, tratamiento y comprobación del seguimiento|Solo cambiar el número del reporte|Borrar reportes iguales|La repetición requiere verificar si se trató la condición.
Un cambio de proceso introduce otro equipo. ¿Qué debe revisarse?|Peligros y controles de las nuevas condiciones|Solo el logotipo|Solo el color del equipo|Los controles previos pueden no cubrir el cambio.
Una persona detecta una condición que considera insegura. ¿Qué corresponde dentro del procedimiento?|Avisar y seguir el mecanismo autorizado para evitar exposición|Ocultar el hecho por temor a retrasar|Continuar siempre sin consultar|El reporte debe facilitar que personal competente valore y controle la condición.
Una inspección encuentra doce condiciones y cuatro se corrigen y verifican. ¿Cuántas siguen pendientes?|8|4|16|Doce menos cuatro equivale a ocho pendientes; eso no determina su prioridad de riesgo.
Una protección se retira para ganar velocidad. ¿Qué haces?|Reportar y tratar la condición según el procedimiento, sin normalizarla|Considerarla una mejora automática|Ocultar su ausencia|La productividad no sustituye la comprobación de condiciones de seguridad.
Un equipo desconoce a quién reportar una emergencia. ¿Qué falta?|Información accesible y preparación del procedimiento aplicable|Más abreviaturas|Solo una lista de compras|Las personas deben saber cómo activar el canal competente.
Una capacitación se registra solo por asistencia. ¿Qué más puede necesitarse?|Comprobar comprensión y aplicación según la tarea|Asumir competencia universal|Eliminar supervisión|Asistir no demuestra por sí solo que se puede ejecutar una tarea.
Se propone un control sin revisar su efecto. ¿Qué debe definirse?|Cómo comprobar si reduce el riesgo previsto|Solo el coste de la etiqueta|Solo una fecha de correo|Un control debe poder evaluarse en las condiciones de uso.
Un incidente se describe con rumores. ¿Qué debe conservar el informe?|Hechos comprobados y lo que queda por confirmar|Culpables elegidos sin evidencia|Solo comentarios de redes|La investigación debe distinguir observaciones de interpretaciones.
Una acción preventiva tiene fecha pero no responsable. ¿Qué falta?|Asignación y mecanismo de seguimiento|Un título más largo|Otro duplicado del informe|El compromiso debe permitir saber quién actuará y cómo se verificará.
""",
"hospitality": """
¿Qué información esencial identifica una reserva?|Persona autorizada, fechas, alojamiento y condiciones|Solo el primer nombre|Solo un color|La reserva necesita datos suficientes para prestar el servicio acordado.
¿Qué debe comprobarse antes de confirmar disponibilidad?|Capacidad real para las fechas y condiciones solicitadas|Solo el precio de portada|Solo cantidad de empleados|La confirmación debe basarse en disponibilidad vigente.
¿Qué ayuda durante un cambio de turno en recepción?|Pendientes y compromisos documentados|Solo una despedida|Contraseñas compartidas|La continuidad exige transferir contexto relevante.
¿Qué debe protegerse en el mostrador?|Datos de huéspedes y documentos de acceso|Solo material decorativo|Solo folletos públicos|La atención no debe exponer información de otras personas.
¿Qué debe quedar claro en el precio comunicado?|Servicios incluidos y cargos o condiciones aplicables|Solo el valor más pequeño|Solo la moneda|La persona debe comprender qué está contratando.
Hay veinte habitaciones y quince comprometidas para una noche. ¿Cuántas quedan antes de otros bloqueos?|5|15|35|Veinte menos quince equivale a cinco; faltaría revisar bloqueos de mantenimiento.
Una habitación vendida está fuera de servicio. ¿Qué haces?|Verificar alternativas y comunicar una solución autorizada|Ocultarlo hasta la llegada|Cambiar la reserva sin avisar|La incidencia necesita una respuesta coordinada con condiciones claras.
Un tercero pide el número de habitación de un huésped. ¿Qué verificas?|Autorización y procedimiento de privacidad|Solo que parece amable|Solo que conoce su nombre|Conocer una identidad no habilita acceso a su información.
Un cambio de fechas modifica el precio. ¿Qué debes confirmar?|Nuevas condiciones y aceptación antes de aplicarlas|Solo la disponibilidad|Que el cliente lo adivine|El cambio debe ser informado y aceptado según el acuerdo.
Dos canales venden la última habitación a la vez. ¿Qué control ayuda?|Actualizar disponibilidad de forma consistente y gestionar conflictos|Duplicar la capacidad en el informe|Ignorar un canal|La coordinación evita comprometer el mismo recurso varias veces.
Una queja requiere mantenimiento. ¿Qué debe incluir su derivación?|Condición observada, ubicación y seguimiento sin datos innecesarios|Solo «arreglar»|Toda la documentación del huésped|La derivación debe permitir actuar con el contexto pertinente.
Se cancela una reserva con condiciones publicadas. ¿Qué haces?|Aplicar el procedimiento y explicar las condiciones correspondientes|Inventar una penalidad distinta|Borrar el historial|La cancelación debe conservar trazabilidad y coherencia con lo acordado.
Una persona solicita una adaptación de acceso. ¿Qué verificas?|Necesidad, disponibilidad y solución autorizada|Solo el precio|Que no haga preguntas|La atención debe comprobar qué puede ofrecerse realmente.
Un pendiente desaparece del cambio de turno. ¿Qué mejora el proceso?|Registro con responsable, estado y siguiente acción|Más mensajes sin identificar|Depender solo de memoria|La continuidad necesita información recuperable.
Antes de cerrar la estancia, ¿qué contrastas?|Servicios y cargos con el registro y las condiciones aceptadas|Solo el total estimado inicialmente|Solo el número de llamadas|El cobro debe corresponder a servicios y condiciones verificables.
""",
"farm-records": """
¿Qué identifica un lote en un registro productivo?|Una referencia estable que relaciona sus actividades|Solo su color en un mapa|Solo el nombre del encargado|La identificación conecta el lote con su historial.
¿Qué datos ayudan a planificar una tarea de campo?|Actividad, lugar, responsable, recursos y fecha|Solo un saludo|Solo el precio final|La planificación necesita condiciones verificables para ejecutar y seguir la tarea.
¿Qué debe distinguirse en un registro de producción?|Cantidad, unidad y periodo|Solo el nombre comercial|Solo la longitud del texto|La unidad y el periodo hacen interpretable la cantidad.
¿Qué requiere una corrección de un dato registrado?|Soporte y trazabilidad del cambio|Borrar el registro sin dejar rastro|Inventar un valor plausible|La corrección debe permitir revisar qué cambió y por qué.
¿Qué conecta una entrega con su origen?|Identificador de lote y soporte de movimiento|Solo la marca del transporte|Solo la hora del mensaje|La trazabilidad necesita mantener el vínculo entre origen y destino.
Se programan ocho tareas y tres quedan pendientes. ¿Cuántas se registran como terminadas?|5|3|11|Ocho menos tres equivale a cinco, según el estado registrado.
Dos cuadrillas anotan la misma tarea como dos ejecuciones. ¿Qué revisas?|Identidad, fecha y regla de deduplicación|Sumar siempre ambos registros|Borrar todo el día|La duplicidad puede alterar el avance y el consumo informado.
La lluvia cambia el plan de trabajo. ¿Qué debe actualizarse?|Fechas, dependencias y comunicación del plan autorizado|Solo el título|Solo el archivo de imagen|La planificación debe reflejar las condiciones reales sin prescribir una técnica agronómica.
Un consumo se registra en litros y otro en mililitros. ¿Qué haces antes de agregar?|Normalizar las unidades y validar la conversión|Sumar los números sin convertir|Eliminar el menor|Las cantidades deben tener unidades comparables.
Una entrega no tiene lote de origen. ¿Qué límite existe?|No se puede reconstruir completamente su procedencia|Se conoce todo por el total|Solo falta un color|La ausencia del vínculo limita la trazabilidad.
Un registro dice «se hizo» sin fecha ni lugar. ¿Qué falta?|Contexto para comprobar la actividad|Solo más adjetivos|Solo otra copia|El registro debe permitir identificar la ejecución concreta.
Una recomendación técnica excede el rol administrativo. ¿Qué haces?|Derivarla al personal competente y registrar la consulta|Inventar una dosis|Aplicar cualquier instrucción de redes|La gestión documental no habilita prescripciones técnicas.
El reporte semanal mezcla áreas medidas con criterios diferentes. ¿Qué revisas?|Unidad, alcance y método de registro|Solo el nombre del archivo|Solo el orden de parcelas|La comparación requiere una base homogénea.
Una entrada de almacén ya se había registrado. ¿Qué control ayuda?|Referencia única del movimiento y verificación de duplicados|Cambiar la fecha para sumarla|Crear otro lote sin soporte|La identidad del movimiento evita inflar existencias.
Al pasar el turno, ¿qué información permite continuar?|Actividades pendientes, condiciones observadas y responsable siguiente|Solo cantidad total|Credenciales de otra persona|La continuidad necesita contexto y responsabilidades claras.
""",
"construction-control": """
¿Qué debe identificarse en un plano utilizado en obra?|Versión vigente y aprobación aplicable|Solo su tamaño de papel|Solo el nombre de la carpeta|La versión evita trabajar con instrucciones desactualizadas.
¿Qué debe mostrar un registro de avance?|Trabajo medido, unidad, periodo y soporte|Solo un porcentaje sin base|Solo el clima|El avance necesita una base comprobable.
¿Qué representa una dependencia del cronograma?|Una condición que debe cumplirse para continuar otra actividad|Una factura duplicada|Una lista de colores|La secuencia condiciona las fechas posibles.
¿Qué debe quedar registrado ante un cambio de alcance?|Cambio, motivo, autorización e impacto|Solo un mensaje informal|Solo el nombre del contratista|La trazabilidad permite entender qué se autorizó.
¿Qué información debe acompañar una entrega de materiales?|Referencia, cantidad, condición y soporte|Solo la matrícula del vehículo|Solo una fotografía sin identificación|La recepción debe contrastarse con lo solicitado.
Una actividad dura cinco días y la siguiente cuatro sin solapamiento. ¿Qué duración mínima suman?|9 días|5 días|1 día|Las actividades sucesivas suman sus duraciones en el caso dado.
Se reportan metros y metros cuadrados en una sola suma. ¿Qué revisas?|Compatibilidad de unidades y definición de la medición|Solo redondear|Sumar igual por ser números|Las magnitudes diferentes no se agregan directamente.
Dos documentos aprobados se contradicen. ¿Cómo procedes desde control documental?|Solicitar aclaración autorizada y conservar la trazabilidad|Elegir el que parezca más fácil|Modificar el diseño estructural por tu cuenta|El conflicto debe resolverlo quien tenga competencia y autoridad.
Un proveedor entrega una especificación distinta. ¿Qué haces?|Registrar y remitir la diferencia para aceptación o tratamiento autorizado|Usarla sin informar|Borrar la orden original|La recepción no debe dar por conforme un cambio no autorizado.
El avance del mes incluye trabajo ya contabilizado. ¿Qué control falta?|Conciliación de mediciones por periodo e identificación|Solo otro color|Solo más decimales|El control debe evitar contar dos veces la misma ejecución.
Un cambio afecta una actividad sucesora. ¿Qué revisas?|Cronograma, dependencias y compromisos relacionados|Solo la fecha de una foto|Solo el título del plano|El efecto puede propagarse a otros trabajos.
Una bitácora no identifica quién registró un hecho. ¿Qué limita?|Autoría y trazabilidad del registro|Solo la estética|Solo el tamaño|El registro debe poder asociarse a una observación y responsable.
Se pide aprobar un cálculo fuera de tu competencia administrativa. ¿Qué haces?|Remitirlo al profesional competente|Aprobarlo porque el total parece razonable|Cambiar cifras hasta que coincidan|El control documental no sustituye una revisión técnica habilitada.
Se requiere recuperar una instrucción vigente de meses atrás. ¿Qué ayuda?|Historial de versiones y fechas de vigencia|Solo la última carpeta|Un archivo sin fecha|La gestión documental permite reconstruir el estado aplicable en un momento.
Antes del cierre de un frente, ¿qué contrastas?|Entregables, pendientes y aceptación documentada|Solo el pago|Solo el número de trabajadores|El cierre debe reflejar los compromisos cumplidos y pendientes transferidos.
""",
"workplace-english": """
Which sentence politely asks for information?|Could you confirm the delivery date?|You confirmation date?|Confirming you yesterday?|Could you is a standard polite request form.
What does «deadline» mean in a work schedule?|The latest time to complete something|A meeting room|A holiday destination|A deadline is the time by which a task should be finished.
Choose the correct sentence about a daily routine.|She checks the reports every morning.|She check the reports every morning.|She checking the reports every morning.|The third-person singular present simple uses checks.
Which message says the file is included with the email?|Please find the report attached.|Please report yesterday attachment.|Please attaching was tomorrow.|Attached identifies a file included with the message.
What does «reschedule» mean?|Arrange a new time for an event|Delete every contact|Confirm the same event happened|Rescheduling changes the planned time.
Read: «The meeting has moved from Tuesday to Thursday». When is it now?|Thursday|Tuesday|Both days at the same time|The new scheduled day is Thursday.
Which request asks someone to explain something again?|Could you clarify the last point?|Could you delete all the points?|You clarification yesterday?|Clarify asks for a clearer explanation.
Read: «Submit the form by Friday». What must you do?|Send the form no later than Friday|Send it only after Friday|Wait until next month|By expresses the latest allowed time in this instruction.
Choose the sentence describing an action happening now.|We are reviewing your application.|We reviews your application.|We reviewed tomorrow now.|Present continuous describes an action in progress.
Read: «The order is delayed, but it has not been cancelled». What is its status?|It is late and still expected to continue.|It has been cancelled.|It was delivered on time.|Delayed and cancelled describe different states.
Which reply acknowledges a mistake and offers a next step?|We will correct the invoice and send an updated copy.|Your invoice is always wrong you.|No next step because mistake.|A useful reply explains the action that will address the issue.
Read: «Please contact Ana if Luis is unavailable». Who is the alternative contact?|Ana|Nobody|Only Luis regardless of availability|The condition identifies Ana as the alternative.
Choose a professional subject line for a changed interview time.|Interview rescheduled: new time confirmation|Hello!!!! anything|No subject because time|The subject should identify the purpose of the message.
Read: «We need three additional copies, not three copies in total». What is requested?|Three more copies than the number already available|Exactly three including existing copies|No copies|Additional refers to copies added to those already present.
Which sentence communicates uncertainty accurately?|We expect delivery on Monday, subject to confirmation.|Delivery happened next Monday yesterday.|Delivery is guaranteed even though we do not know.|Expected and subject to confirmation distinguish an estimate from a guarantee.
""",
"instructional-design": """
¿Qué debe describir un objetivo de aprendizaje?|Una capacidad observable al terminar|Solo el nombre del video|Solo la duración|El objetivo orienta qué actividad y evidencia se necesitan.
¿Qué relación debe haber entre objetivo y evaluación?|La evaluación debe pedir la capacidad prevista|Pueden ser totalmente independientes|Basta con que tengan el mismo color|La alineación permite interpretar la evidencia de aprendizaje.
¿Qué ayuda a ordenar una secuencia formativa?|Prerrequisitos y dificultad progresiva|Solo el orden alfabético|Solo cantidad de pantallas|Las actividades deben preparar lo necesario para las siguientes.
¿Qué aporta una rúbrica con descriptores?|Criterios para distinguir niveles de una evidencia|Una calificación infalible automática|Un certificado legal|Los descriptores hacen explícito qué se observa.
¿Qué debe facilitar un material accesible?|Acceso al contenido y operación según las necesidades del público|Solo que sea pequeño|Solo que tenga animaciones|La accesibilidad debe considerarse en el diseño y sus alternativas.
Se pretende enseñar a resolver casos pero solo se pide memorizar definiciones. ¿Qué revisas?|Actividad y evaluación respecto al objetivo|Solo el número de páginas|Solo el color del curso|Las tareas deben comprobar la aplicación que se pretende enseñar.
Un módulo depende de un concepto que no se explicó. ¿Qué haces?|Introducir o comprobar el prerrequisito|Aumentar la penalidad|Ocultar la dependencia|La secuencia necesita atender los conocimientos necesarios.
Un video contiene información esencial sin alternativa textual. ¿Qué mejoras?|Una alternativa equivalente que permita acceder al contenido|Eliminar todos los textos|Cambiar solo el fondo|El contenido esencial debe poder consultarse de forma accesible.
Dos versiones de una evaluación tienen dificultades distintas. ¿Qué necesitas revisar?|Cobertura, criterios y comparabilidad antes de usarlas como equivalentes|Solo el mismo número de preguntas|Solo el mismo título|La equivalencia requiere más que igual longitud.
Una persona completa el curso muy rápido. ¿Qué puedes afirmar solo con ese dato?|Que finalizó el recorrido registrado, no que domina toda la habilidad|Que es experta|Que no necesita evaluación|El tiempo y la completitud no sustituyen evidencia de desempeño.
La retroalimentación revela solo una nota. ¿Qué añades?|Criterio, explicación y siguiente acción de mejora|Otra cifra sin explicación|Un juicio personal|El feedback debe permitir actuar sobre una dificultad.
El material se actualiza después de iniciar intentos. ¿Qué conservas?|Versión y condiciones del intento ya iniciado|Cambiar sus preguntas sin aviso|Borrar el historial|La trazabilidad permite interpretar el resultado de cada versión.
Un cuestionario repite la misma idea con distinto texto. ¿Qué revisas?|Cobertura de contenidos y redundancia|Solo aumentar el número de preguntas|Solo el título|Más ítems no garantizan una evaluación más completa.
Una actividad requiere una herramienta de pago no anunciada. ¿Qué falta?|Condiciones y alternativas de acceso claras|Solo un enlace al inicio|Solo el nombre del docente|Las barreras y requisitos deben conocerse antes de comprometer el recorrido.
Al terminar un piloto, ¿qué evidencia sirve para mejorar?|Errores frecuentes, comprensión y dificultades observadas|Solo número de visitas|Solo opiniones positivas seleccionadas|La mejora debe considerar resultados y barreras del recorrido.
""",
"appointments": """
¿Qué necesita una cita para ser interpretable?|Fecha, hora, zona horaria y servicio correspondiente|Solo «mañana»|Solo un color|La agenda requiere información temporal y de servicio suficiente.
¿Qué evita reservar un mismo espacio incompatible dos veces?|Comprobación de disponibilidad y confirmación consistente|Cambiar el nombre de la persona|Duplicar todas las citas|La reserva debe respetar la capacidad vigente.
¿Qué datos se solicitan para confirmar una cita?|Solo los necesarios por el canal autorizado|Toda la historia clínica siempre|Contraseñas del paciente|La finalidad administrativa no justifica cualquier dato.
¿Quién debe resolver instrucciones clínicas no documentadas?|El personal competente según el procedimiento|Quien atiende el teléfono aunque no esté autorizado|Cualquier mensaje de redes|La gestión de agenda no habilita indicaciones clínicas.
¿Qué debe quedar al cancelar una cita?|Estado y comunicación según el procedimiento|Un hueco sin registro siempre|La eliminación de todo historial|La cancelación necesita trazabilidad.
Hay doce espacios, tres bloqueados y dos reservas en espacios distintos. ¿Cuántos quedan libres?|7|12|5|Doce menos tres menos dos equivale a siete espacios disponibles.
Una cita cambia de modalidad. ¿Qué debe actualizarse?|Acceso, instrucciones administrativas y aviso a la persona|Solo el nombre del profesional|Solo la hora en una nota privada|La persona necesita conocer cómo asistir en la nueva modalidad.
Dos mensajes dan horas diferentes. ¿Qué haces?|Contrastar el registro vigente y comunicar la corrección|Dejar que la persona adivine|Eliminar ambos mensajes sin aclarar|La agenda y la comunicación deben coincidir.
Una persona pide detalles de una cita ajena. ¿Qué verificas?|Identidad, autorización y alcance de la información|Solo que conozca el nombre|Solo que llame varias veces|La cita también puede revelar información personal.
Un recordatorio llega a un contacto antiguo. ¿Qué revisas?|Actualización del dato, canales y tratamiento de la exposición|Solo el diseño del mensaje|Solo su longitud|La corrección debe llegar a los sistemas que usan el contacto.
Un servicio requiere una duración diferente a la habitual. ¿Qué usas?|Duración confirmada por el procedimiento correspondiente|Siempre el bloque más corto|Una duración inventada|La capacidad debe planificarse según el servicio autorizado.
El profesional no estará disponible. ¿Qué coordinación necesitas?|Reprogramación autorizada y aviso a personas afectadas|Marcar las citas como realizadas|No actualizar la agenda|La disponibilidad debe reflejar el cambio real.
Una fecha pasada se interpreta como asistencia confirmada. ¿Qué falta?|Un registro que distinga fecha y realización|Solo otra etiqueta de color|Una nueva contraseña|Que haya pasado la hora no confirma asistencia.
Se solicita priorizar un caso por motivos clínicos. ¿Qué haces desde agenda?|Remitir la valoración al personal competente según el protocolo|Decidir la prioridad clínica por intuición|Publicar los síntomas para preguntar|La prioridad clínica debe tratarla quien tenga la competencia correspondiente.
Un cupo liberado se ofrece a otra persona. ¿Qué debe quedar consistente?|Reserva vigente, confirmación y comunicación a las partes pertinentes|Dos personas confirmadas en el mismo espacio incompatible|Solo una nota local|La reasignación debe mantener una disponibilidad y comunicación coherentes.
""",
}

# Context, valid procedure, numerical check and domain terms for each skill.
CASE_DATA = """
javascript|Un formulario recibe diez registros. Dos no tienen identificador y otro distinto tiene un importe no numérico. Solo deben procesarse registros completos y válidos.|Definir el contrato de entrada>Validar tipos e identificadores>Procesar solo los registros válidos>Comprobar la salida con casos límite|¿Cuántos registros cumplen las condiciones del caso?|7|Diez menos dos menos uno equivale a siete registros válidos.|Validación=Comprueba el contrato de entrada;Promesa=Representa un resultado asíncrono;Array=Contiene una colección ordenada
typescript|Una API devuelve doce objetos. Tres no cumplen la estructura comprobada en ejecución. El formulario debe distinguir respuestas válidas y errores sin aserciones que oculten el fallo.|Definir el contrato de respuesta>Comprobar los datos externos>Tratar cada variante válida>Verificar errores y casos ausentes|¿Cuántos objetos superan la comprobación descrita?|9|Doce menos tres equivale a nueve; el tipo estático no sustituye esa comprobación.|unknown=Requiere comprobar el valor antes de usarlo;Unión=Expresa variantes de un dato;Validador=Comprueba el contenido en ejecución
react|Una tabla tiene ocho filas con identificadores estables. El usuario retira tres filas distintas. La selección de las cinco restantes debe conservar su identidad al reordenarlas.|Identificar filas con claves estables>Actualizar el estado sin mutar la lista>Representar las filas vigentes>Comprobar selección y reordenación|¿Cuántas filas quedan en la tabla?|5|Ocho menos tres equivale a cinco filas, manteniendo las identidades restantes.|Prop=Entrada de un componente;Estado=Información que cambia y participa en la representación;Key=Identifica un elemento entre renderizados
git-workflow|Una revisión tiene diez archivos cambiados: siete corresponden al objetivo y tres son archivos temporales ajenos. Debe prepararse un cambio acotado sin incluir esos temporales.|Revisar estado y diferencias>Seleccionar cambios del objetivo>Comprobar el cambio preparado>Registrar el commit y solicitar revisión|¿Cuántos archivos corresponden al cambio que se revisará?|7|El caso identifica siete archivos pertinentes y tres temporales que deben excluirse.|Commit=Registro versionado de un cambio;Rama=Línea de desarrollo;Conflicto=Combinación que requiere resolución explícita
linux|Un servidor tiene doce tareas registradas. Cuatro terminaron y ocho siguen en ejecución. Necesitas identificar procesos y consultar registros sin detener tareas ajenas.|Identificar el servicio y su proceso>Consultar estado y registros>Aplicar una acción autorizada si corresponde>Comprobar el estado resultante|¿Cuántas tareas siguen en ejecución según el registro?|8|Doce menos cuatro equivale a ocho tareas aún en ejecución.|PID=Identifica un proceso;Permiso=Regula operaciones según identidad;Registro=Conserva hechos de la ejecución
networks|Se prueban diez conexiones al mismo servicio desde distintas sedes. Tres fallan y siete responden. Debe conservarse origen, destino y hora para investigar las diferencias.|Definir origen y destino de las pruebas>Comprobar resolución y conectividad>Contrastar rutas y controles>Registrar resultados y verificar cambios|¿Cuántas conexiones respondieron en el caso?|7|Diez menos tres equivale a siete respuestas observadas, sin atribuir aún una causa a los fallos.|DNS=Resuelve nombres mediante registros;Puerta de enlace=Encamina tráfico hacia otras redes;Puerto=Identifica un punto de acceso al servicio de transporte
data-analysis|Una tabla contiene cuarenta respuestas. Cinco son duplicados y otras tres no cumplen el criterio publicado de inclusión. Se analizarán solo las respuestas únicas elegibles.|Definir población y criterio de inclusión>Comprobar calidad y duplicados>Calcular sobre registros elegibles>Documentar fuente y límites|¿Cuántas respuestas son elegibles según el caso?|32|Cuarenta menos cinco menos tres equivale a treinta y dos observaciones elegibles.|Granularidad=Define qué representa cada fila;Muestra=Conjunto de observaciones analizadas;Sesgo=Desviación sistemática que afecta la interpretación
power-bi|Un origen de treinta ventas contiene dos duplicados y tres filas distintas sin fecha. El informe mensual exige ventas únicas con fecha y debe conciliar su cantidad con la tabla preparada.|Definir la pregunta y granularidad>Preparar y validar los datos>Modelar y construir la medida>Contrastar filtros y totales con el origen|¿Cuántas filas cumplen el criterio del caso?|25|Treinta menos dos menos tres equivale a veinticinco ventas elegibles.|Power Query=Prepara y transforma datos;Relación=Conecta tablas para el modelo;Medida=Calcula un resultado en el contexto de consulta
responsible-ai|Un equipo revisa veinte borradores generados. Cuatro contienen referencias inexistentes. Los dieciséis restantes aún deben comprobarse en cuanto a contenido y autorización antes de usarse.|Definir tarea y criterios>Generar un borrador con datos autorizados>Contrastar contenido y referencias>Aprobar o corregir antes del uso|¿Cuántos borradores no presentan el fallo de referencia observado?|16|Veinte menos cuatro equivale a dieciséis; eso no demuestra ausencia de otros fallos.|Borrador=Propuesta pendiente de revisión;Fuente=Material que permite contrastar un dato;Supervisión=Revisión apropiada al impacto del uso
project-management|Un proyecto tiene doce entregables. Cinco se aceptaron según los criterios y los otros siete siguen pendientes. No se considera completado un entregable solo por haber enviado un archivo.|Definir alcance y criterios>Planificar dependencias y responsables>Revisar entregables con evidencia>Registrar aceptación y pendientes|¿Cuántos entregables siguen pendientes de aceptación?|7|Doce menos cinco equivale a siete pendientes de aceptación.|Alcance=Delimita el trabajo comprometido;Dependencia=Condición entre actividades;Aceptación=Confirmación del cumplimiento del criterio
human-resources|Una vacante recibió veinte candidaturas. Ocho se revisaron con los criterios del cargo y doce siguen por revisar. Abrir una ficha no representa una decisión de contratación.|Definir criterios pertinentes al cargo>Revisar evidencias de cada candidatura>Registrar evaluación con los criterios>Comunicar el siguiente estado confirmado|¿Cuántas candidaturas quedan por revisar?|12|Veinte menos ocho equivale a doce candidaturas pendientes de revisión.|Criterio=Condición pertinente usada para revisar;Evidencia=Información que respalda una valoración;Feedback=Comunicación concreta sobre el resultado o siguiente paso
digital-marketing|Una campaña produjo mil impresiones y veinte clics en el mismo periodo. La compra es una conversión distinta; no se debe atribuir una compra a cada clic.|Definir objetivo y métrica>Preparar campaña y seguimiento>Comprobar datos del mismo periodo>Interpretar resultados con sus límites|¿Qué porcentaje de clics sobre impresiones se observó?|2|Veinte dividido entre mil por cien equivale a dos por ciento.|Impresión=Exposición registrada del anuncio;Clic=Interacción de acceso registrada;Conversión=Acción objetivo definida para la campaña
crm|Un equipo tiene treinta seguimientos abiertos y completa doce con su soporte. Los dieciocho restantes necesitan responsable y siguiente acción; no se borrará el historial.|Identificar contactos y casos>Comprobar historial y preferencias>Registrar la acción y responsable>Actualizar estado y próximo paso|¿Cuántos seguimientos quedan abiertos?|18|Treinta menos doce equivale a dieciocho seguimientos pendientes.|Contacto=Registro de una relación identificada;Oportunidad=Posible acuerdo con etapa y contexto;Seguimiento=Acción para continuar una relación o solicitud
entrepreneurship|Un piloto vende veinte unidades a treinta cada una. El coste variable por unidad es dieciocho. Se compara la contribución antes de costes fijos, sin tratarla como utilidad final.|Definir necesidad y supuesto>Preparar un experimento y criterio>Registrar ingresos y costes comparables>Evaluar evidencia y siguiente decisión|¿Qué contribución total antes de costes fijos obtiene el piloto?|240|Veinte por la diferencia entre treinta y dieciocho equivale a doscientos cuarenta.|Propuesta de valor=Beneficio relevante para un destinatario;Supuesto=Condición que necesita contrastarse;Contribución=Ingreso menos coste variable en el alcance indicado
cost-accounting|Un producto se vende a cincuenta y su coste variable unitario es treinta y dos. En el caso se venden diez unidades; no se incluyen aún costes fijos.|Definir periodo y partidas>Contrastar soportes y clasificación>Calcular sobre bases comparables>Conciliar e interpretar el resultado|¿Qué contribución total antes de costes fijos resulta?|180|Diez por la diferencia entre cincuenta y treinta y dos equivale a ciento ochenta.|Coste variable=Varía con la actividad en el alcance definido;Coste fijo=No varía directamente con el volumen dentro del rango relevante;Contribución=Ayuda a cubrir costes fijos antes de obtener resultado
procurement|Se piden cien unidades. Se reciben ochenta, pero cinco de esas ochenta se rechazan por condición. Se necesitan cien unidades aceptadas y el rechazo no se cuenta como recepción conforme.|Definir especificación y criterios>Comparar y autorizar el pedido>Revisar cantidad y condición al recibir>Registrar aceptación y gestionar diferencias|¿Cuántas unidades aceptadas faltan para cumplir el pedido?|25|Se aceptan setenta y cinco de las ochenta recibidas; cien menos setenta y cinco equivale a veinticinco.|Especificación=Define lo que debe entregarse;Recepción=Comprobación de lo recibido;Pendiente=Parte del compromiso aún no aceptada
quality|Una inspección revisa doscientas unidades y encuentra seis no conformes con el criterio definido. El dato describe lo observado en esa revisión, sin garantizar el estado de otras unidades.|Definir criterio y alcance>Inspeccionar y registrar evidencia>Tratar las diferencias observadas>Comprobar acciones y conservar trazabilidad|¿Qué porcentaje de unidades revisadas fue no conforme?|3|Seis dividido entre doscientas por cien equivale a tres por ciento.|Criterio=Requisito que permite comprobar conformidad;Corrección=Trata una diferencia detectada;Causa=Condición investigada que explica el origen del problema
workplace-safety|Una inspección registra doce condiciones que requieren tratamiento. Cuatro tienen corrección verificada y ocho siguen pendientes. El conteo no determina por sí solo la prioridad de riesgo.|Identificar condiciones y contexto>Reportar por el canal autorizado>Asignar tratamiento al personal competente>Verificar acciones y seguimiento|¿Cuántas condiciones siguen pendientes según el registro?|8|Doce menos cuatro equivale a ocho pendientes, cuya prioridad requiere valoración competente.|Peligro=Fuente potencial de daño;Riesgo=Valoración de posibilidad y efecto según el método;Control=Medida cuya eficacia debe comprobarse
hospitality|Un alojamiento tiene veinte habitaciones. Quince están reservadas y dos habitaciones distintas están bloqueadas por mantenimiento. No se deben confirmar reservas sobre los bloqueos.|Comprobar disponibilidad vigente>Confirmar condiciones con la persona>Registrar la reserva de forma consistente>Comunicar acceso y próximos pasos|¿Cuántas habitaciones quedan disponibles esa noche?|3|Veinte menos quince menos dos equivale a tres habitaciones disponibles.|Reserva=Compromiso registrado para unas fechas;Bloqueo=Capacidad que no puede ofrecerse;Confirmación=Comunicación de las condiciones acordadas
farm-records|Se planifican ocho visitas de registro a lotes. Tres siguen pendientes y cinco tienen soporte completo. Los datos se usarán para seguimiento administrativo, sin prescribir tratamientos.|Identificar lotes y actividades>Planificar responsables y recursos>Registrar ejecución y unidades>Conciliar avances y transferir pendientes|¿Cuántas visitas tienen soporte completo?|5|Ocho menos tres equivale a cinco visitas registradas como completas.|Lote=Unidad identificada para conservar trazabilidad;Movimiento=Registro de una entrada o salida con soporte;Plan=Actividades y compromisos previstos
construction-control|Un frente tiene dos actividades sucesivas de cinco y cuatro días, sin solapamiento ni otros tiempos. El control registra dependencias y versiones, sin aprobar decisiones de ingeniería.|Comprobar documentos vigentes>Registrar alcance y dependencias>Medir avance con soportes>Conciliar cambios y pendientes autorizados|¿Qué duración mínima suman las actividades del caso?|9|Cinco más cuatro equivale a nueve días bajo las condiciones indicadas.|Versión=Identifica una edición de un documento;Medición=Cuantificación con unidad y alcance;Dependencia=Condición necesaria entre actividades
workplace-english|The team planned eight meetings. Three were cancelled and the other five are still scheduled. Use the updated schedule, not the original total.|Read the updated schedule>Identify the confirmed change>Check the remaining meetings>Communicate the current arrangement|How many meetings are still scheduled?|5|Eight minus three equals five meetings that remain scheduled.|Deadline=Latest time to complete a task;Reschedule=Arrange another time;Attached=Included as a file with the message
instructional-design|Un módulo tiene diez objetivos observables. Cuatro carecen de actividad o evaluación alineada y los otros seis sí la tienen. Se revisará la cobertura antes de publicar.|Definir objetivos y público>Diseñar actividades y acceso>Relacionar evaluación y criterios>Probar el recorrido y revisar evidencia|¿Cuántos objetivos tienen actividad y evaluación alineadas?|6|Diez menos cuatro equivale a seis objetivos cubiertos según la revisión.|Objetivo=Capacidad observable prevista;Actividad=Tarea para practicar o demostrar;Criterio=Condición usada para valorar la evidencia
appointments|La agenda ofrece doce espacios. Tres están bloqueados y otros dos ya están reservados. Los bloques son distintos y no hay solapamientos.|Comprobar disponibilidad vigente>Confirmar datos administrativos necesarios>Registrar la cita y sus condiciones>Comunicar y verificar cambios pertinentes|¿Cuántos espacios quedan libres?|7|Doce menos tres menos dos equivale a siete espacios disponibles.|Disponibilidad=Capacidad que puede reservarse;Confirmación=Comunicación de la reserva vigente;Reprogramación=Cambio de una cita con actualización y aviso
"""


def banks(tracks=TRACKS, content=CONTENT, case_data=CASE_DATA):
    from app.domain.services.challenge_tracks import LEVELS, decisions

    cases = {}
    for line in case_data.strip().splitlines():
        slug, context, steps, prompt, answer, explanation, pairs = line.split("|")
        sequence = steps.split(">")
        terms, meanings = zip(*(pair.split("=", 1) for pair in pairs.split(";")), strict=True)
        cases[slug] = [
            {"id": "case-sequence", "type": "order", "prompt": "Ordena el procedimiento del caso.", "choices": sequence[1:] + sequence[:1], "answer": [3, 0, 1, 2], "feedback": " → ".join(sequence)},
            {"id": "case-number", "type": "number", "prompt": prompt, "choices": [], "answer": float(answer), "feedback": explanation},
            {"id": "case-meaning", "type": "matching", "prompt": "Relaciona los conceptos con su función en el caso.", "terms": list(terms), "choices": list(meanings[1:] + meanings[:1]), "answer": [2, 0, 1], "feedback": "; ".join(f"{term}: {meaning}" for term, meaning in zip(terms, meanings, strict=True))},
        ]
        for item in cases[slug]:
            item.update(context=context, topic="Caso y comprobación")
    result = {}
    for slug, area, skill, aliases, scope in tracks:
        authored = decisions(content[slug], "Aplicación de la habilidad", "item")
        foundation, application = authored[:5], authored[5:]
        for item in foundation:
            item["topic"] = "Conceptos y criterios"
        for level in ("beginner", "intermediate"):
            label, count, minutes = LEVELS[level]
            sections = [foundation, [*application, *cases[slug]]] if level == "beginner" else [foundation, application, cases[slug]]
            quotas = [5, 5] if level == "beginner" else [2, 10, 3]
            questions = deepcopy([item for section in sections for item in section])
            result[f"{slug}-{level}-v1"] = {"title": f"{skill.capitalize()} · {label.lower()}", "skill": skill,
                "related_skills": aliases, "category": area, "level": level, "version": "1", "minutes": minutes,
                "question_count": count, "questions": questions, "selection": [{"ids": [item["id"] for item in section], "count": quota} for section, quota in zip(sections, quotas, strict=True)],
                "context": scope, "source_ids": [0], "scope": "Evalúa las tareas descritas; no acredita una profesión, experiencia ni habilitación técnica."}
    return result
