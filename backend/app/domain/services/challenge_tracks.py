"""Versioned TalentSync question banks. Original cases; external sources guide coverage only.

Levels describe task complexity, not professional certification or job seniority.
Published items and attempt snapshots remain immutable; revisions receive new IDs.
"""
from copy import deepcopy

from app.domain.services.learning_activities import CASES, activities_for
from app.domain.services.skills import skill_set

LEVELS = {"beginner": ("Básico", 10, 20), "intermediate": ("Intermedio", 15, 35), "advanced": ("Avanzado", 20, 50)}
SOURCES = [
    {"title": "Future of Jobs 2025 · habilidades", "url": "https://www.weforum.org/publications/the-future-of-jobs-report-2025/3-skills-outlook/", "scope": "Internacional · expectativas de empleadores, no ranking colombiano", "reviewed_on": "2026-10-23"},
    {"title": "Encuesta de demanda laboral 2025 · Bogotá", "url": "https://desarrolloeconomico.gov.co/asi-estan-contratando-las-empresas-en-bogota-perfiles-tecnicos-y-baja-experiencia-marcan-la-tendencia/", "scope": "Bogotá · publicada en abril de 2026", "reviewed_on": "2026-10-23"},
]

SPECIAL_CASES = {
    "excel": ("Una tabla tiene 20 ventas: 2 filas duplicadas y 3 filas distintas sin fecha. El informe exige ventas únicas con fecha válida.", ["Definir columnas y clave de la venta", "Revisar tipos y registros inválidos", "Calcular sobre las filas válidas", "Conciliar los totales del informe"], "De esas 20 filas, ¿cuántas ventas únicas con fecha válida quedan?", 15, ["Referencia absoluta", "Tabla dinámica", "Validación de datos"], ["Fija fila y columna al copiar", "Resume datos por categorías", "Restringe entradas según un criterio"]),
    "web": ("Un formulario de inscripción debe funcionar a 360 px, con teclado y texto ampliado. Sus errores deben conservar los datos introducidos.", ["Definir etiquetas y estructura semántica", "Diseñar una distribución adaptable", "Comprobar teclado y mensajes de error", "Probar móvil y texto ampliado"], "Hay 8 campos y 3 no tienen etiqueta asociada. ¿Cuántos campos sí la tienen?", 5, ["Etiqueta", "Foco", "Diseño adaptable"], ["Identifica la finalidad del campo", "Indica el control operable con teclado", "Redistribuye contenido según el espacio"]),
}

# slug, seed bank, simulation, area, assessed skill, related course skills, scope
TRACKS = [
    ("communication", "general-foundations-v1", "general", "general", "comunicacion", ["comunicacion asertiva", "trabajo en equipo"], "Acuerdos, prioridades y comunicación de riesgos"),
    ("service", "service-foundations-v1", "service", "service", "servicio al cliente", ["atencion al cliente", "orientacion al servicio"], "Verificación de solicitudes, escalamiento y seguimiento"),
    ("sales", "sales-foundations-v1", "sales", "sales", "ventas", ["venta consultiva", "negociacion", "crm"], "Necesidades, propuestas, conversión y seguimiento comercial"),
    ("documents", "administration-foundations-v1", "administration", "administration", "gestion documental", ["administracion", "organizacion documental"], "Versiones, permisos, trazabilidad y recuperación"),
    ("finance", "finance-foundations-v1", "finance", "finance", "conciliacion bancaria", ["contabilidad", "tesoreria"], "Cortes, soportes, diferencias y conciliación"),
    ("inventory", "logistics-foundations-v1", "logistics", "logistics", "inventarios", ["logistica", "gestion de inventarios", "control de inventarios"], "Existencias, reservas, rotación y trazabilidad"),
    ("education", "education-foundations-v1", "education", "education", "evaluacion del aprendizaje", ["pedagogia", "educacion", "formacion"], "Objetivos observables, evidencias y ajustes accesibles"),
    ("design", "design-foundations-v1", "design", "design", "diseno visual", ["diseno grafico", "comunicacion visual", "accesibilidad"], "Jerarquía, formatos, licencias y accesibilidad"),
    ("care", "care-foundations-v1", "care", "care", "atencion administrativa en salud", ["atencion al usuario", "gestion de citas"], "Trámites y confidencialidad; no evalúa decisiones clínicas"),
    ("sql", "sql-foundations-v1", "project-sql", "technology", "sql", ["postgresql", "bases de datos"], "Consultas, uniones, agregación y calidad del resultado"),
    ("python", "python-foundations-v1", "technology", "technology", "python", ["programacion en python"], "Colecciones, validación, excepciones y pruebas"),
    ("security", "application-security-foundations-v1", "project-security", "technology", "seguridad de aplicaciones", ["ciberseguridad", "seguridad informatica"], "Autorización, sesiones y protección de datos"),
    ("excel", None, "administration", "administration", "excel", ["hojas de calculo", "microsoft excel"], "Fórmulas, referencias, limpieza y análisis de tablas"),
    ("web", None, "design", "technology", "diseno web adaptable", ["html", "css", "html5", "css3", "responsive design", "diseno web"], "HTML semántico, CSS adaptable y accesibilidad web"),
]

# prompt | correct option | distractor | distractor | explanation.
# Concrete numerical and procedural activities supplement these decisions.
CONTENT = {
"communication": """
Un informe vence el viernes y faltan datos de otra área. ¿Qué acuerdo permite anticipar el riesgo?|Responsable, entrega parcial y fecha de confirmación|Esperar al viernes|Prometer la entrega sin consultar|Un acuerdo verificable permite detectar el retraso antes del vencimiento.
Dos equipos interpretan distinto «terminado». ¿Qué defines?|Criterios de aceptación observables|Una etiqueta de color|Solo el nombre de la tarea|Los criterios compartidos permiten comprobar el mismo resultado.
Un mensaje dice «eso está mal» sin indicar dónde. ¿Qué respuesta ayuda?|Pedir el dato y el criterio concreto que no se cumple|Responder con otra acusación|Aceptar todos los cambios sin revisar|La evidencia y el criterio convierten una queja en una corrección comprobable.
Debes informar un retraso de dos días. ¿Qué incluyes?|Impacto, alternativas y próximo compromiso|Solo una disculpa|Una fecha que no has contrastado|Explica qué cambia y qué decisión se puede tomar con esa información.
En una reunión quedan cinco acciones sin responsables. ¿Cómo cierras?|Asignar responsable y plazo y confirmar acuerdos|Enviar solo la grabación|Marcar todo como resuelto|Un acta útil identifica qué hará cada persona y cuándo.
Una instrucción urgente contradice una política. ¿Cómo procedes?|Escalar la contradicción por el canal autorizado|Incumplir en silencio|Ignorar ambas instrucciones|La urgencia no elimina la necesidad de resolver el conflicto de forma explícita.
El destinatario no comprende una explicación técnica. ¿Qué haces?|Adaptar el lenguaje y comprobar su comprensión|Copiar más términos técnicos|Repetir el mismo texto sin cambios|La comprensión se comprueba con una reformulación o una acción observable.
Tres áreas comparten una tarea bloqueada. ¿Qué seguimiento sirve?|Dependencia, persona que desbloquea y fecha de revisión|Tres listas contradictorias|Solo un porcentaje global|El bloqueo requiere identificar la dependencia y su siguiente resolución.
Dos entregas tienen el mismo plazo y no caben en la capacidad. ¿Qué haces?|Acordar prioridad y alcance con quienes deciden|Comprometer ambas completas|Elegir la más fácil sin avisar|Un límite de capacidad requiere una decisión informada sobre alcance o prioridad.
Una decisión cambió después de la reunión. ¿Qué debes actualizar?|Registro de la decisión y personas afectadas|Solo tu agenda|Nada hasta que alguien pregunte|La trazabilidad necesita reflejar el acuerdo vigente y comunicar el impacto.
""",
"service": """
Una persona reclama dos cargos con igual importe. ¿Qué verificas?|Identificadores, fechas y soportes de ambos movimientos|Solo que está molesta|Que el importe sea pequeño|El mismo importe no demuestra por sí solo un cobro duplicado.
Un caso se deriva a otra área. ¿Qué debe conservar?|Resumen, evidencia mínima y responsable de seguimiento|La contraseña de la persona|Una nota sin identificador|La derivación debe permitir continuar el caso sin repetir la información necesaria.
Hay 40 casos y 30 resueltos. ¿Qué indica una resolución del 75%?|30 de los 40 casos del mismo grupo fueron resueltos|Que todos quedaron satisfechos|Que cada agente resolvió el 75%|La tasa describe resolución del grupo; no mide satisfacción ni desempeño individual por sí sola.
Una devolución sigue en revisión. ¿Qué comunicas?|Estado confirmado y fecha del siguiente aviso|Que ya fue aprobada|Que no podrás responder nunca|No prometas una decisión que todavía no se ha autorizado.
Dos agentes responden el mismo caso con soluciones diferentes. ¿Qué procede?|Unificar el historial y confirmar la solución autorizada|Cerrar ambos registros|Pedir otra vez todos los datos al usuario|Un historial compartido evita respuestas contradictorias.
El cliente solicita datos de otra persona. ¿Cómo respondes?|Verificar autorización y limitar la información compartida|Entregarlos por cortesía|Pedir que los publique en redes|La atención debe respetar los permisos sobre datos personales.
Un caso reabierto figuraba como resuelto. ¿Qué revisas?|Si el cierre cumplió los criterios y cómo contar la reapertura|Eliminar la reclamación|Cambiar la fecha de llegada|La reapertura aporta información sobre la calidad del cierre.
Tres casos vencen hoy; uno bloquea un servicio esencial. ¿Cómo priorizas?|Impacto y urgencia según la política de atención|Solo orden alfabético|Solo quien más mensajes envía|La prioridad debe responder a criterios explícitos de impacto y plazo.
Una respuesta automática no resuelve la solicitud. ¿Qué haces?|Ofrecer revisión humana con contexto conservado|Repetirla indefinidamente|Cerrar por falta de respuesta del robot|La automatización debe permitir continuar cuando no resuelve el caso.
Una mejora bajó el tiempo medio pero subieron las reaperturas. ¿Qué concluyes?|Revisar ambas métricas antes de afirmar que mejoró la atención|La atención mejoró necesariamente|Las reaperturas no importan|Rapidez y resolución efectiva son dimensiones diferentes.
""",
"sales": """
Un comprador busca reducir faltantes y tiene presupuesto limitado. ¿Qué preguntas?|Frecuencia del problema, impacto y restricciones|Solo cuánto descuento quiere|Su contraseña del inventario|La propuesta necesita entender la necesidad y sus límites.
Un producto requiere conexión y la sede no tiene internet estable. ¿Qué corresponde?|Explicar la limitación y evaluar alternativas viables|Ocultarlo hasta la compra|Prometer funcionamiento sin conexión|Las restricciones esenciales deben explicarse antes de comprometer una solución.
Se cerraron 12 ventas de 60 oportunidades del mismo periodo. ¿Qué tasa es correcta?|20%|12%|60%|12 dividido entre 60 y multiplicado por 100 equivale a 20%.
Una promoción añade cargos obligatorios. ¿Qué precio comunicas?|El total y sus condiciones antes de aceptar|Solo el precio reducido|Los cargos después del pago|La decisión informada requiere conocer el coste completo.
Un prospecto dice «lo revisamos luego». ¿Qué seguimiento propones?|Fecha y decisión siguiente acordadas|Llamadas cada hora|Marcar la venta como cerrada|El seguimiento debe permitir avanzar sin presión ni estados ficticios.
Una campaña duplica contactos repetidos en el CRM. ¿Qué revisas?|Criterio de deduplicación antes de medir conversión|Solo aumentar el total|Borrar clientes sin soporte|Los duplicados alteran la base de cálculo y el seguimiento.
Ingresos suben pero el margen baja. ¿Qué debes analizar?|Costes, descuentos y mezcla de ventas|Solo cantidad de llamadas|Solo el total facturado|Más ingresos no garantizan una mayor rentabilidad.
El cliente compara dos propuestas de alcance distinto. ¿Qué haces?|Homologar alcance y condiciones antes de comparar precios|Comparar solo el número final|Afirmar que la tuya siempre gana|Una comparación útil necesita prestaciones y condiciones equivalentes.
Una promesa comercial depende del equipo de entrega. ¿Qué necesitas?|Confirmar capacidad y plazo antes de comprometerlos|Asignar una fecha al azar|Cerrar y avisar después|La promesa debe ser compatible con la capacidad de cumplimiento.
Un contacto retira su autorización de comunicaciones. ¿Qué procede?|Aplicar la preferencia y registrar el cambio|Continuar por otro canal sin permiso|Duplicar su ficha|El seguimiento debe respetar las preferencias y la autorización aplicable.
""",
"documents": """
Recibes «contrato-final» y «contrato-final2» sin aprobación. ¿Qué haces?|Comprobar versión vigente y responsable de aprobación|Elegir el archivo más grande|Usar el primero que aparece|El nombre no demuestra vigencia ni aprobación.
Una carpeta de nómina quedó pública. ¿Qué acción es prioritaria?|Restringir el acceso y registrar la incidencia|Cambiar solo el color|Enviar el enlace al equipo completo|Primero se contiene la exposición y se conserva la trazabilidad necesaria.
Un documento aprobado necesita una corrección. ¿Cómo procedes?|Nueva versión con motivo, revisión y aprobación|Sobrescribir sin registro|Borrar la versión anterior sin política|La revisión debe permitir reconstruir qué cambió y quién lo aprobó.
Un expediente debe localizarse por cliente y fecha. ¿Qué ayuda?|Índice y metadatos consistentes con acceso autorizado|Duplicarlo en todas las carpetas|Solo recordar su nombre|Los metadatos facilitan recuperación sin multiplicar copias descontroladas.
Un archivo perdió su responsable. ¿Qué haces?|Asignar custodia y revisar permisos según la política|Dejarlo abierto a todos|Eliminarlo inmediatamente|La custodia y los permisos deben quedar definidos.
Una solicitud exige conservar un soporte bajo revisión. ¿Qué haces?|Aplicar la retención correspondiente y documentar la restricción|Eliminarlo por rutina|Cambiar la fecha para ocultarlo|La eliminación debe considerar obligaciones de conservación y revisiones pendientes.
Una persona sale del equipo. ¿Qué revisas?|Accesos, custodia y transferencia de documentos|Solo quitar su foto|Compartir su contraseña|La salida requiere retirar permisos y asegurar continuidad sin compartir credenciales.
Hay copias con diferentes datos personales. ¿Qué necesitas?|Identificar fuente autorizada y corregir con trazabilidad|Fusionar todo sin revisar|Publicar las copias para decidir|Las discrepancias requieren una fuente y un proceso de corrección verificables.
Un enlace a un expediente caducó. ¿Qué alternativa usas?|Renovar acceso autorizado con alcance y duración adecuados|Hacer toda la biblioteca pública|Enviar las credenciales del propietario|La disponibilidad no justifica ampliar el acceso innecesariamente.
Se solicita demostrar quién aprobó un cambio. ¿Qué evidencia sirve?|Registro de versión, aprobación y fecha|La fecha del último acceso únicamente|Un comentario sin autor|La aprobación debe vincularse con una identidad y una versión concreta.
""",
"finance": """
Banco y libro tienen cortes diferentes. ¿Qué haces primero?|Alinear el periodo y obtener soportes comparables|Registrar la diferencia como gasto|Modificar el saldo inicial|La conciliación necesita comparar el mismo periodo.
Un depósito figura en libros y no en el banco al corte. ¿Qué verificas?|Fecha y soporte para determinar si está en tránsito|Que sea necesariamente fraude|Que deba eliminarse del libro|Una diferencia temporal requiere evidencia antes de ajustar.
Una comisión bancaria no está registrada en libros. ¿Qué corresponde?|Validar el soporte y tramitar el ajuste autorizado|Eliminar la comisión del extracto|Sumarla al ingreso|El ajuste contable necesita soporte y autorización.
Los saldos coinciden después de ajustes sin soporte. ¿Es suficiente?|No; la coincidencia no reemplaza justificar los ajustes|Sí; basta con que den igual|Solo si el importe es pequeño|Una conciliación correcta debe ser trazable, no solo coincidir numéricamente.
Un movimiento aparece dos veces en el libro. ¿Qué revisas?|Documento origen y posible duplicidad antes de corregir|Borrar ambos registros|Cambiar el extracto bancario|La corrección debe preservar el soporte y el registro del cambio.
El banco registra un cargo desconocido. ¿Qué haces?|Investigar y registrar una diferencia pendiente|Inventar una categoría de gasto|Dar por conciliado el importe|Un cargo sin identificar permanece como diferencia hasta verificarlo.
Una misma persona prepara y aprueba todos los ajustes. ¿Qué control falta?|Revisión independiente según la política|Cambiar el formato del archivo|Más decimales en el saldo|Separar preparación y aprobación reduce el riesgo de errores no detectados.
Un cheque emitido sigue sin cobrar al corte. ¿Cómo lo tratas?|Como partida pendiente documentada según su estado|Como nuevo ingreso|Como comisión automática|Las partidas pendientes deben identificarse y seguirse sin duplicar registros.
Un ajuste del mes anterior se repite este mes. ¿Qué verificas?|Si ya fue contabilizado y conciliado|Aplicarlo siempre de nuevo|Eliminar todo el historial|Repetir ajustes ya registrados puede crear una diferencia nueva.
Una conciliación tiene partidas antiguas sin resolver. ¿Qué seguimiento requiere?|Antigüedad, responsable y acción de investigación|Ocultarlas para cerrar|Trasladarlas sin registro|El cierre necesita seguimiento de diferencias persistentes.
""",
"inventory": """
Se cuentan 112 unidades y 5 están dañadas. ¿Qué representa disponibilidad física apta?|107 unidades|112 unidades|117 unidades|Las dañadas se excluyen de las existencias aptas para despacho.
El sistema indica 120 y el conteo 112; existe una salida de 8 sin registrar. ¿Qué procede?|Validar el soporte y registrar la salida pendiente|Descontar otras 8 del conteo físico|Sumar 8 dañadas|El movimiento explica la diferencia; no se descuenta dos veces del conteo.
Un producto vence antes que otro del mismo tipo. ¿Qué criterio reduce vencimientos?|Despachar primero el que vence antes si está apto|Siempre el de mayor precio|Elegir al azar|FEFO prioriza vencimiento, conservando las condiciones de aptitud.
Hay 90 unidades aptas y 30 reservadas. ¿Cuántas quedan libres?|60|90|120|La disponibilidad libre excluye reservas vigentes.
Un lote carece de identificador. ¿Qué riesgo introduce?|No poder rastrear recepción y destino del lote|Solo cambia la presentación|Aumenta necesariamente las ventas|La identificación del lote permite reconstruir sus movimientos.
Un pedido entra dos veces con el mismo identificador. ¿Qué control necesitas?|Detectar duplicidad antes de reservar o despachar|Despachar ambos siempre|Cambiar el identificador sin revisar|Una repetición no debe duplicar el efecto sobre existencias.
La demanda media es 10 unidades al día y el plazo 4 días. Sin seguridad, ¿qué punto de pedido resulta?|40 unidades|14 unidades|4 unidades|Demanda durante el plazo: 10 por 4 equivale a 40 unidades.
Suben faltantes aunque el inventario total aumenta. ¿Qué analizas?|Distribución por referencia, demanda y reposición|Solo el total de unidades|Solo tamaño del almacén|El exceso de una referencia no compensa la falta de otra.
Un conteo encuentra una diferencia. ¿Qué haces antes de ajustar?|Recontar y revisar movimientos del mismo corte|Cambiar el saldo sin soporte|Culpar a una persona automáticamente|El ajuste requiere confirmar la diferencia y su contexto.
Una devolución vuelve al almacén. ¿Cómo la incorporas?|Verificar condición y destino antes de liberarla|Marcarla siempre como disponible|Borrarla del historial|La devolución necesita trazabilidad y comprobación de aptitud.
""",
"education": """
El objetivo dice «comprender inventarios». ¿Cómo lo haces observable?|Resolver un caso y justificar su cálculo con criterios|Mirar un video completo|Marcar asistencia|Una acción observable permite recoger evidencia del aprendizaje esperado.
Un alumno no puede acceder al video. ¿Qué haces?|Ofrecer una alternativa equivalente accesible|Ponerle cero por no verlo|Eliminar el objetivo|Se adapta el acceso manteniendo el objetivo de aprendizaje.
Se evalúa análisis, pero el examen solo pide memorizar términos. ¿Qué revisas?|Alineación entre objetivo, actividad y evidencia|Solo el color del examen|Solo el número de alumnos|La evaluación debe pedir la capacidad que pretende comprobar.
Doce de veinte participantes fallan el mismo concepto. ¿Qué respuesta ayuda?|Revisar la explicación y proponer otra práctica del concepto|Repetir el examen idéntico sin ayuda|Dar el tema por aprendido|El patrón orienta una intervención específica y una nueva evidencia.
Una rúbrica usa «bien» y «mal» sin descriptores. ¿Qué falta?|Criterios observables para distinguir niveles|Un logotipo|Más categorías sin definición|Los descriptores permiten aplicar un criterio de manera consistente.
Dos evaluadores califican distinto la misma evidencia. ¿Qué haces?|Contrastar criterios y calibrar con muestras|Promediar sin revisar siempre|Elegir la nota más alta por defecto|La discrepancia requiere revisar cómo se interpreta la rúbrica.
Una actividad tiene buena asistencia pero poco logro. ¿Qué concluyes?|Participación y aprendizaje requieren evidencias distintas|La asistencia demuestra dominio|El objetivo ya se cumplió|Asistir no demuestra haber adquirido la capacidad.
El feedback dice solo «incorrecto». ¿Cómo lo mejoras?|Explicar el criterio y un próximo paso concreto|Añadir una sanción|Repetir la nota|La retroalimentación debe ayudar a corregir una dificultad identificable.
Se cambia el objetivo después de entregar. ¿Qué debes evitar?|Calificar con criterios nuevos no comunicados|Mantener trazabilidad|Explicar la revisión|Los criterios de evaluación deben conocerse antes de la entrega.
Un estudiante mejora en un segundo caso diferente. ¿Qué evidencia aporta?|Aplicación de lo aprendido en otra situación comparable|Certificación profesional automática|Dominio de toda la disciplina|La transferencia observada tiene un alcance específico y limitado.
""",
"design": """
Un cartel se lee en escritorio pero no en móvil. ¿Qué revisas?|Tamaño real de uso, jerarquía y legibilidad|Solo peso del archivo original|Solo el nombre del diseñador|El diseño debe comprobarse en el contexto y tamaño de uso.
Una imagen aparece en internet sin licencia identificada. ¿Qué haces?|Verificar permisos o usar un recurso autorizado|Usarla porque es pública|Quitar la marca de autor|Acceso público no equivale a permiso de reutilización.
Dos mensajes compiten por atención. ¿Qué defines?|Prioridad de información según la tarea|Mismo tamaño para todo|Más colores sin criterio|La jerarquía permite reconocer la información principal.
Una alerta se distingue solo por rojo y verde. ¿Qué mejoras?|Añadir texto o icono con significado además del color|Usar tonos más parecidos|Eliminar el mensaje|La información no debe depender únicamente de distinguir colores.
Se pide un cartel impreso y una pieza móvil. ¿Qué entregas?|Formatos y dimensiones adecuados a cada uso|El mismo archivo sin comprobar|Solo una miniatura|Los medios requieren comprobar resolución, dimensiones y lectura.
Un botón usa un icono sin significado claro. ¿Qué ayuda?|Etiqueta comprensible y estado visible|Un icono más pequeño|Ocultar la acción|Una etiqueta reduce la necesidad de adivinar la función.
Un cambio estético reduce la tasa de tareas completadas. ¿Qué investigas?|Usabilidad y contexto antes de declararlo una mejora|Solo opiniones del diseñador|Solo número de colores|El éxito depende de que la audiencia pueda completar su tarea.
Una maqueta no incluye errores ni carga. ¿Qué falta?|Estados de interacción y recuperación|Solo otra portada|Más animación decorativa|Un flujo necesita explicar qué sucede cuando espera o falla.
El texto principal queda sobre una fotografía variable. ¿Qué verificas?|Contraste en las distintas zonas y tamaños de uso|Solo contraste en un punto favorable|Solo el marco de la imagen|La legibilidad debe mantenerse donde el texto pueda aparecer.
Varias pantallas representan la misma acción de forma diferente. ¿Qué haces?|Unificar patrones conservando contexto y jerarquía|Añadir un diseño distinto a cada una|Cambiar todos los textos por iconos|Los patrones consistentes facilitan aprender y reconocer acciones.
""",
"care": """
Un familiar pide resultados clínicos en recepción. ¿Qué compruebas?|Identidad, autorización y canal correspondiente|Solo que conoce el nombre|Su insistencia|El vínculo declarado no basta para autorizar acceso a datos clínicos.
Una persona describe síntomas y pide un medicamento. ¿Qué haces desde recepción?|Derivar al personal clínico según el protocolo|Recomendar el más vendido|Elegir una dosis por internet|La función administrativa no incluye decisiones clínicas.
Una pantalla de turnos muestra diagnósticos. ¿Qué debe revisarse?|Minimización de datos visibles|Solo tamaño de letra|Solo orden alfabético|Un turno no necesita divulgar información clínica a la sala.
Una cita requiere preparación clínica no documentada. ¿Qué haces?|Solicitar instrucciones al personal competente|Inventar la preparación|Copiar una de otro procedimiento|La orientación clínica debe proceder de quien está autorizado.
Se necesita corregir un dato administrativo. ¿Cómo procedes?|Verificar identidad y registrar la corrección autorizada|Cambiarlo sin soporte|Crear otra identidad|La calidad de datos necesita verificación y trazabilidad.
Un listado para confirmar citas incluye historias completas. ¿Qué reduces?|Los datos a los necesarios para la confirmación|La protección del archivo|El registro de accesos|La finalidad administrativa no justifica compartir toda la historia.
Una persona no comprende el trámite. ¿Qué ayuda?|Explicación clara y comprobación de comprensión|Más siglas sin explicación|Negar toda orientación|El acceso al trámite mejora con lenguaje comprensible.
Una cancelación libera un cupo. ¿Cómo lo reasignas?|Según reglas de agenda y prioridad autorizadas|Al contacto personal del agente|Sin registrar el cambio|La reasignación debe seguir criterios y conservar trazabilidad.
Un correo de recordatorio revela datos a un destinatario equivocado. ¿Qué haces?|Contener el incidente y seguir el protocolo de reporte|Ignorarlo porque fue automático|Reenviarlo a todo el equipo|La automatización no elimina la responsabilidad de tratar una exposición.
Un caso urgente excede la atención administrativa. ¿Qué haces?|Activar la derivación prevista en el protocolo|Dar un diagnóstico|Esperar siempre al final del turno|Debes reconocer el límite del rol y usar el canal competente.
""",
"sql": """
Una tabla tiene valores NULL en email. ¿Qué filtro los encuentra?|email IS NULL|email = NULL|email = 'NULL'|NULL se comprueba con IS NULL, no mediante igualdad.
Cada pedido tiene varios artículos. Un JOIN duplica el total del pedido. ¿Qué revisas?|La granularidad y agregación antes de sumar|Agregar DISTINCT a cualquier columna sin analizar|Multiplicar el total por los artículos|Combinar filas a distinta granularidad puede duplicar importes.
Se requieren clientes sin pedidos. ¿Qué consulta los conserva?|LEFT JOIN desde clientes y filtro pedidos.id IS NULL|INNER JOIN desde pedidos|CROSS JOIN sin condición|La unión izquierda conserva clientes y permite identificar los sin coincidencias.
¿Dónde filtras grupos cuya suma supera 100?|HAVING SUM(total) > 100|WHERE SUM(total) > 100|ORDER BY SUM(total) > 100|HAVING filtra resultados agrupados.
Un informe mensual usa timestamps. ¿Qué rango evita perder fracciones del último día?|Inicio incluido y comienzo del mes siguiente excluido|Hasta las 23:59 exactas del último día|Solo comparar el número del mes|El intervalo semiabierto incluye todo el periodo sin asumir precisión del timestamp.
COUNT(*) tras LEFT JOIN devuelve 1 para un cliente sin pedidos. ¿Qué cuenta pedidos reales?|COUNT(pedidos.id)|COUNT(*) otra vez|SUM(clientes.id)|La columna no nula del pedido omite la fila sin coincidencia.
Una consulta funciona solo con los datos de ejemplo. ¿Qué pruebas añades?|Clientes sin pedidos, duplicados y valores límite|Solo más nombres iguales|Solo el mismo resultado fijo|Los casos límite verifican la lógica, no una salida memorizada.
Una entrada del usuario llega a SQL. ¿Cómo la incorporas?|Parámetros enlazados|Concatenación de texto|Quitar espacios|Los parámetros separan datos e instrucciones.
Se pide el último movimiento por cuenta con empates de fecha. ¿Qué necesitas?|Un criterio adicional de desempate estable|ORDER BY fecha sin desempate siempre|Elegir cualquier fila y ocultarlo|El resultado debe definir qué sucede cuando hay empates.
Promediar promedios de grupos de tamaños distintos produce un sesgo. ¿Qué usas?|Suma total dividida entre cantidad total|Promedio simple de los promedios siempre|El promedio del grupo más grande|El promedio global pondera por el número de observaciones.
""",
"python": """
Una función usa items=[] como valor predeterminado y conserva cambios. ¿Cómo lo evitas?|Usar None y crear la lista dentro|Reiniciar el intérprete cada vez|Usar la misma lista global|Los valores predeterminados se crean al definir la función.
Una conversión a entero puede fallar. ¿Qué captura evita ocultar errores ajenos?|ValueError en el bloque mínimo necesario|BaseException en toda la aplicación|Un except vacío global|La captura específica conserva visibles los fallos no previstos.
Debes deduplicar registros por ID y conservar el primero. ¿Qué defines?|Una clave y una política explícita antes de descartar|Convertir todas las filas a texto|Eliminar todo ID repetido sin criterio|La deduplicación necesita identidad y regla de conservación.
Un archivo grande no cabe en memoria. ¿Qué estrategia evalúas?|Procesar por iteración o bloques|Leerlo completo varias veces|Duplicar su contenido en listas|El procesamiento incremental limita el consumo de memoria.
Una función recibe dinero como texto decimal. ¿Qué consideras?|Decimal y reglas explícitas de redondeo|float garantiza exactitud decimal siempre|Redondear sin política en cada paso|Los importes requieren controlar precisión y redondeo.
Copias una lista de diccionarios con list.copy y cambias un diccionario. ¿Qué ocurre?|Los diccionarios internos siguen compartidos|Todo se copia profundamente|La lista original se vuelve inmutable|Una copia superficial conserva referencias a los objetos internos.
Una prueba usa fecha actual y falla a medianoche. ¿Qué mejora?|Inyectar un reloj o fijar el tiempo en la prueba|Reintentar hasta que pase|Eliminar la comprobación|Controlar el tiempo permite reproducir el caso límite.
Un proceso reintenta una petición de pago. ¿Qué necesitas además de capturar errores?|Idempotencia y límites de reintento|Reintentos infinitos|Una pausa sin identificador|Los reintentos deben evitar efectos duplicados y recursos ilimitados.
Un registro tiene total=None. ¿Qué haces antes de sumarlo?|Aplicar la política de dato ausente y validar|Convertirlo silenciosamente en venta real de cero|Ignorar todos los errores|Ausencia y cero tienen significados diferentes.
Una operación modifica la colección que está iterando. ¿Qué revisas?|Iterar una copia o construir una salida según el caso|Asumir que no afecta al recorrido|Reiniciar el bucle infinitamente|Cambiar la colección durante el recorrido puede omitir elementos o invalidarlo.
""",
"security": """
Una URL permite cambiar el ID de un documento. ¿Qué comprobación protege su acceso?|Permiso del usuario sobre ese documento en el servidor|Solo que haya iniciado sesión|Ocultar el ID en CSS|Estar autenticado no autoriza consultar cualquier recurso.
Un secreto apareció en un repositorio público. ¿Qué haces primero sobre la credencial?|Revocarla o rotarla|Renombrar el archivo solamente|Borrar solo el último comentario|Eliminar un texto no revoca las copias de la credencial.
Una cookie de sesión viaja por HTTP en producción. ¿Qué falta?|HTTPS y configuración segura de la cookie|Un nombre más largo|Guardar la contraseña en la cookie|La sesión debe protegerse durante el transporte.
La aplicación usa cookies para mutaciones. ¿Qué defensa evalúas frente a CSRF?|Token ligado a sesión y validación del origen según el flujo|Solo ocultar botones|CORS como única defensa universal|La protección debe validar la legitimidad de la petición con credenciales de sesión.
Un PDF subido declara un tipo pero contiene otro. ¿Qué validas?|Contenido, tamaño y procesamiento restringido|Solo extensión|Solo nombre del usuario|Los metadatos declarados no garantizan el contenido.
Los logs incluyen tokens del proveedor. ¿Qué cambias?|Redacción de secretos y contexto diagnóstico mínimo|Hacerlos públicos para depurar|Guardar también las contraseñas|Los registros no deben convertirse en un almacén de credenciales.
Un usuario pierde acceso al equipo. ¿Qué revisas?|Revocación de sesiones y autorización vigente|Solo su nombre visible|Que conserve acceso hasta reiniciar el servidor|Los permisos deben reflejar el estado actual del miembro.
La recuperación de contraseña revela si existe un correo. ¿Qué respuesta prefieres?|Respuesta genérica y controles contra abuso|Lista completa de usuarios|Contraseña actual por correo|La recuperación debe limitar enumeración y no divulgar contraseñas.
Una dependencia tiene una vulnerabilidad publicada. ¿Qué haces?|Evaluar exposición, actualizar y comprobar el comportamiento|Ignorarla por ser externa|Desactivar todos los logs|La gestión requiere conocer impacto y verificar la corrección.
Un rol entrevistador puede enviar una decisión de contratación por API. ¿Qué falla?|Autorización de la operación en el servidor|Solo diseño del botón|Orden de las tarjetas|La interfaz no reemplaza la comprobación de permisos del endpoint.
""",
"excel": """
Copias una fórmula que usa siempre la tasa en B1. ¿Qué referencia fija fila y columna?|$B$1|B1|B$2|Los signos $ fijan la columna B y la fila 1.
Un total incluye filas de cabecera repetidas. ¿Qué revisas?|Limpieza y tipo de datos antes de sumar|Solo el color del total|Aumentar decimales|La estructura de entrada afecta al cálculo.
Se necesita sumar ventas solo de la región Norte. ¿Qué herramienta corresponde?|SUMAR.SI con el criterio y rango adecuados|CONTAR las celdas de texto|Ordenar por color únicamente|SUMAR.SI agrega valores que cumplen un criterio.
Una búsqueda no encuentra un identificador que parece igual. ¿Qué compruebas?|Tipos de dato, espacios y normalización de la clave|Solo el ancho de columna|Solo el zoom|Texto y número o espacios ocultos pueden impedir la coincidencia.
La tabla crece cada semana. ¿Qué reduce rangos incompletos?|Usar una tabla estructurada y comprobar el origen|Rangos fijos sin revisión|Copiar el primer total siempre|Una tabla facilita extender referencias al agregar filas.
Un porcentaje de variación divide entre un periodo anterior de cero. ¿Qué haces?|Definir y mostrar el caso no calculable|Ocultarlo con cero sin explicación|Dividir siempre entre uno|Una base cero requiere una regla explícita y no representa variación cero.
Una tabla dinámica no refleja ventas nuevas. ¿Qué verificas?|Origen y actualización de la tabla dinámica|Solo formato de moneda|Solo orden alfabético|Es necesario incluir los datos y actualizar el resumen.
Hay dos clientes con igual nombre. ¿Qué clave usas para relacionarlos?|Identificador único verificado|Nombre sin revisar|La posición de la fila|Un nombre compartido no identifica de manera unívoca.
SI.ERROR convierte cualquier fallo en vacío. ¿Qué riesgo tiene?|Ocultar errores de datos o de fórmula que deben investigarse|Mejorar siempre la precisión|Validar los datos automáticamente|Controlar un error no debe esconder su causa.
Una hoja compartida permite editar fórmulas críticas. ¿Qué medida ayuda?|Permisos y protección de rangos con revisión de cambios|Compartir una contraseña por chat|Ocultar la hoja como única protección|La integridad necesita controlar quién puede editar y comprobar las modificaciones.
""",
"web": """
¿Qué elemento corresponde a una acción dentro de la página?|button con nombre accesible|Un div sin comportamiento de teclado|Una imagen sin texto alternativo|Un botón nativo aporta semántica y comportamiento de teclado.
Un formulario tiene un placeholder pero no etiqueta. ¿Qué agregas?|label asociado al campo|Solo otro placeholder|Un icono decorativo|La etiqueta permanece disponible cuando el usuario escribe.
Un contenedor fijo de 1200px desborda el móvil. ¿Qué revisas?|Ancho flexible, límites y redistribución del contenido|Ocultar todo el desbordamiento del documento|Reducir toda la fuente a 8px|El diseño debe adaptarse conservando lectura y controles.
Una imagen informativa no carga. ¿Qué permite conocer su contenido?|Texto alternativo que describe su función|Nombre aleatorio del archivo|Un fondo de color|El texto alternativo comunica la información pertinente.
Un enlace abre una página y un botón envía un formulario. ¿Qué eliges?|Elementos según navegación o acción|Usar siempre div|Usar siempre imágenes|La semántica permite anticipar y operar el comportamiento.
Un menú modal permite tabular al fondo. ¿Qué revisas?|Gestión de foco, cierre y retorno al disparador|Solo z-index|Solo color del fondo|Un modal necesita controlar la interacción por teclado.
El texto al 200% queda cortado por una altura fija. ¿Qué cambias?|Altura adaptable y redistribución sin recortar contenido|Impedir ampliar el texto|Ocultar las etiquetas|La ampliación debe conservar contenido y operación.
Una cuadrícula de tres columnas comprime los controles. ¿Qué haces?|Reducir columnas según el espacio disponible|Mantener tres columnas a cualquier ancho|Ocultar botones sin alternativa|Los puntos de adaptación deben responder al contenido y espacio.
Un formulario falla y borra lo escrito. ¿Qué mejora el flujo?|Conservar datos y explicar cómo corregir el error|Recargar sin explicación|Mostrar solo un color rojo|La recuperación debe permitir reintentar sin repetir trabajo.
Una tarjeta usa enlace externo para una acción interna. ¿Qué revisas?|Semántica, destino y etiqueta de la acción|Solo sombra|Solo radio del borde|La etiqueta y el comportamiento deben coincidir.
""",
}

ADVANCED = {
"sql": """
Una suma de ventas se duplica al unir dos tablas de detalle. ¿Qué estrategia conserva la granularidad?|Preagregar cada detalle a la clave adecuada antes de unir|Aplicar DISTINCT al importe siempre|Dividir el resultado entre dos|Dos relaciones uno-a-muchos pueden multiplicar filas; hay que definir la granularidad.
Un ranking pide incluir todos los empates en el tercer puesto. ¿Qué necesitas definir?|RANK o DENSE_RANK según el significado del puesto|ROW_NUMBER sin criterio|Un LIMIT 3 siempre|Los empates y los saltos entre posiciones deben formar parte del contrato.
Una paginación usa OFFSET mientras llegan filas nuevas. ¿Qué alternativa reduce saltos?|Cursor sobre un orden estable con clave única|Quitar ORDER BY|Cambiar el tamaño al azar|Un cursor estable evita depender de posiciones que cambian con nuevas filas.
NOT IN recibe una subconsulta con NULL. ¿Qué revisas?|Su lógica de tres valores y una alternativa NOT EXISTS|Que NULL equivale a cero|Que siempre devuelve todos los registros|NULL puede hacer desconocida la comparación; NOT EXISTS expresa ausencia de coincidencias.
Se requieren acumulados por cuenta y fecha. ¿Qué define el cálculo?|PARTITION BY, orden y marco de la ventana|Solo GROUP BY global|Solo DISTINCT|La partición y el marco determinan qué filas contribuyen a cada acumulado.
Una consulta lenta filtra una fecha transformada por una función. ¿Qué compruebas?|Plan de ejecución e intervalo sobre la columna cuando sea equivalente|Crear índices sobre toda columna sin medir|Eliminar el filtro|La forma del predicado puede influir en el uso del índice; se verifica con el plan.
Dos descuentos se aplican sucesivamente sobre 100: 10% y luego 20%. ¿Cuál es el total final?|72|70|80|100 por 0,9 por 0,8 equivale a 72; los descuentos sucesivos no se suman.
Una operación de transferencia necesita debitar y acreditar juntas. ¿Qué propiedad buscas?|Atomicidad de la transacción|Dos commits independientes siempre|Solo una columna con el total|Ambas operaciones deben confirmarse juntas o revertirse.
Un JOIN usa una dimensión con dos versiones vigentes por error. ¿Qué verificas?|Unicidad y vigencia de la clave antes de atribuir importes|Sumar ambas versiones|Elegir una al azar sin registro|La dimensión debe cumplir su regla temporal y de unicidad.
Se calcula conversión: 18 compras de 120 visitas únicas válidas. ¿Qué base conservas?|Visitas del mismo periodo y definición de usuario|Cualquier total de visitas histórico|Solo compradores|Numerador y denominador deben corresponder a la misma población y periodo.
""",
"excel": """
Se combinan ventas por factura con devoluciones por artículo. ¿Qué defines antes de unir?|Granularidad y clave para evitar multiplicar importes|Solo formato de las columnas|La suma final esperada escrita a mano|La unión debe respetar qué representa cada fila.
Dos categorías tienen medias 10 y 20 con 2 y 8 registros. ¿Cuál es la media global?|18|15|30|La media ponderada es (10 por 2 más 20 por 8) dividido entre 10: 18.
Un archivo mensual cambia el orden de columnas. ¿Qué hace más robusta la transformación?|Usar nombres y validar esquema y tipos|Seleccionar siempre posiciones sin verificar|Copiar el total anterior|El proceso debe detectar cambios del origen en lugar de asignar datos a columnas equivocadas.
El origen contiene números con separadores regionales distintos. ¿Qué revisas?|Configuración regional y conversión con validación|Sustituir todos los puntos por vacío siempre|Cambiar solo el símbolo de moneda|Los separadores afectan la interpretación del valor y requieren validación.
Una búsqueda devuelve la primera coincidencia de claves duplicadas. ¿Qué necesitas?|Validar unicidad o definir cómo agregar las coincidencias|Suponer que la primera es correcta|Ocultar duplicados visualmente|La búsqueda no resuelve por sí sola una clave ambigua.
Una proyección aumenta ingresos 20% y costes 30%. ¿Cómo evalúas el margen?|Recalcular ambos importes sobre sus bases y comparar|Restar porcentajes sin conocer bases|Asumir mayor margen por mayores ingresos|Los porcentajes de bases distintas no se restan para obtener el margen.
Se añaden filas fuera de la tabla usada por un informe. ¿Qué control detecta la omisión?|Conciliar cantidad y totales del origen frente al modelo|Cambiar el color de la pestaña|Congelar paneles|La conciliación permite detectar registros que no llegaron al informe.
Un error de referencia está oculto como cero. ¿Qué haces?|Distinguir errores técnicos de valores reales antes de publicar|Aceptar el total porque no muestra errores|Sumar manualmente una cifra para compensar|Cero es un dato; un error requiere investigar la causa.
Una hoja contiene supuestos mezclados con resultados. ¿Qué mejora la revisión?|Separar entradas, cálculos y salidas con referencias trazables|Duplicar todas las fórmulas|Proteger todo sin documentar|La separación permite revisar de dónde procede un resultado.
Un indicador pasa de 40% a 50%. ¿Qué cambio en puntos porcentuales hay?|10 puntos porcentuales|25 puntos porcentuales|90 puntos porcentuales|La diferencia es 50 menos 40: 10 puntos; el aumento relativo sería 25%.
""",
"inventory": """
Demanda diaria 12, plazo 5 días y seguridad 20. ¿Qué punto de pedido corresponde?|80 unidades|60 unidades|37 unidades|12 por 5 más 20 equivale a 80 unidades.
Hay 200 aptas, 70 reservadas y 30 bloqueadas no incluidas en aptas. ¿Cuántas aptas están libres?|130|100|160|Las 30 bloqueadas ya están fuera de las aptas; no se descuentan dos veces.
Dos almacenes registran la misma transferencia como entrada sin salida. ¿Qué control necesitas?|Conciliar origen, tránsito y recepción con el mismo identificador|Sumar ambas entradas|Borrar la recepción|La transferencia debe conservar el balance entre ubicaciones.
Una clasificación ABC prioriza valor anual consumido. ¿Qué calculas?|Demanda anual por coste unitario para cada referencia|Solo volumen físico|Solo precio de venta máximo|El valor anual combina consumo y coste de la referencia.
Un producto intermitente tiene media diaria poco representativa. ¿Qué revisas?|Distribución de demanda y variabilidad del plazo|Usar la media como garantía|Eliminar los días sin consumo|La variabilidad y la intermitencia afectan el riesgo de faltantes.
Se reciben 100 unidades, 8 rechazadas y 12 aptas reservadas. ¿Cuántas quedan aptas libres?|80|92|100|100 menos 8 rechazadas menos 12 reservadas equivale a 80.
Un ajuste de conteo coincide con movimientos aún abiertos. ¿Qué haces?|Fijar corte y reconciliar movimientos antes del ajuste|Aplicar ambos ajustes sin revisar|Ignorar las salidas|Sin un corte coherente puede corregirse dos veces la misma diferencia.
Un lote retirado fue despachado a varias sedes. ¿Qué dato permite actuar?|Trazabilidad de lotes, destinos y cantidades|Solo precio promedio|Solo nombre del transportador|La retirada necesita localizar qué cantidad llegó a cada destino.
Sube la rotación y aumentan faltantes. ¿Qué concluyes?|Evaluar servicio, disponibilidad y coste conjuntamente|La política mejoró necesariamente|Solo importa reducir existencias|La rotación no demuestra por sí sola que se cumple el servicio.
Se quiere reducir seguridad a cero sin cambiar proveedores. ¿Qué evalúas?|Variabilidad de demanda, plazo y nivel de servicio buscado|Solo espacio de estantería|Solo el último pedido|La seguridad responde al riesgo y al compromiso de servicio.
""",
}


def decisions(text, topic, prefix):
    result = []
    for index, line in enumerate(text.strip().splitlines()):
        prompt, correct, wrong1, wrong2, explanation = line.strip().split("|")
        # Correct positions vary in the stored bank as well as per attempt.
        choices = [correct, wrong1, wrong2]
        shift = index % 3
        choices = choices[shift:] + choices[:shift]
        result.append({"id": f"{prefix}-{index + 1}", "type": "choice", "topic": topic, "prompt": prompt,
                       "choices": choices, "answer": choices.index(correct), "feedback": explanation})
    return result


def expanded_banks(legacy):
    result = {}
    for slug, seed, simulation, category, skill, related, scope in TRACKS:
        authored = decisions(CONTENT[slug], "Aplicación y análisis", "application")
        foundation = deepcopy(legacy[seed]["questions"]) if seed else deepcopy(authored[:5])
        for item in foundation:
            item["id"] = f"concept-{item['id']}"
            item["topic"] = "Conceptos y criterios"
        case = deepcopy(activities_for(simulation))
        context = CASES[simulation][1]
        if slug in SPECIAL_CASES:
            context, steps, prompt, answer, terms, meanings = SPECIAL_CASES[slug]
            case = [{"id": "sequence", "type": "order", "prompt": "Ordena el procedimiento para resolver el caso.", "choices": steps[1:] + steps[:1], "answer": [3, 0, 1, 2], "feedback": " → ".join(steps)},
                    {"id": "calculation", "type": "number", "prompt": prompt, "choices": [], "answer": answer, "feedback": f"Se restan los registros o campos que no cumplen el criterio: el resultado es {answer}."},
                    {"id": "connections", "type": "matching", "prompt": "Relaciona cada concepto con su función.", "terms": terms, "choices": meanings[1:] + meanings[:1], "answer": [2, 0, 1], "feedback": "; ".join(f"{term}: {meaning}" for term, meaning in zip(terms, meanings, strict=True))}]
        for item in case:
            item["id"] = f"case-{item['id']}"
            item["topic"] = "Caso y comprobación"
            item["context"] = context
        first = authored[0]; second = authored[1]
        authored.append({"id": "application-multiple", "type": "multi_select", "topic": "Aplicación y análisis", "prompt": f"Selecciona las dos acciones correctas al trabajar con {skill}.", "choices": [first["choices"][first["answer"]], first["choices"][(first["answer"] + 1) % 3], second["choices"][second["answer"]], second["choices"][(second["answer"] + 1) % 3]], "answer": [0, 2], "feedback": f"{first['feedback']} {second['feedback']}"})
        for level, (label, count, minutes) in LEVELS.items():
            if level == "advanced" and slug not in ADVANCED:
                continue
            # Basic draws five decisions + five application tasks; intermediate
            # adds the complete application case. Advanced excludes basic items.
            sections = [foundation, [*(authored if seed else authored[5:]), *case]] if level == "beginner" else [foundation, authored, case]
            quotas = [5, 5] if level == "beginner" else [2, 10, 3]
            if level == "advanced":
                sections = [authored, decisions(ADVANCED[slug], "Análisis de restricciones", "advanced")]
                quotas = [10, 10]
            for section in sections:
                # IDs are unique within a bank even when a foundation is reused.
                for item in section:
                    item.setdefault("type", "choice")
            questions = [item for section in sections for item in section]
            result[f"{slug}-{level}-v2"] = {"title": f"{skill.capitalize()} · {label.lower()}", "skill": skill,
                "related_skills": list(dict.fromkeys([*related, *([legacy[seed]["skill"]] if seed else [])])), "category": category, "level": level, "version": "2", "minutes": minutes,
                "question_count": count, "questions": questions, "selection": [{"ids": [item["id"] for item in section], "count": quota} for section, quota in zip(sections, quotas, strict=True)],
                "context": scope, "source_ids": [0, 1] if category in {"service", "sales", "administration", "general"} else [0],
                "scope": "Evaluación de tareas concretas de TalentSync; no certifica una profesión ni experiencia laboral."}
    return result


def related_assessments(resource, banks):
    skills = skill_set(resource.get("skills", []))
    return [key for key, bank in banks.items() if not bank.get("retired") and skills & skill_set([bank["skill"], *bank.get("related_skills", [])])]
