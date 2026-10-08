"""Original, non-clinical exercises and transparent profile-based catalog routing."""
import re

from app.domain.services.skills import skill_key

AREAS = {
    "general": {"label": "Competencias transversales", "terms": []},
    "technology": {"label": "Tecnología y datos", "terms": ["software", "sistemas", "programador", "developer", "desarrollador", "datos", "python", "java", "sql", "angular", "react", "tecnologia"]},
    "service": {"label": "Servicio al cliente", "terms": ["servicio", "cliente", "call center", "recepcion", "customer"]},
    "sales": {"label": "Ventas y comercio", "terms": ["ventas", "comercial", "vendedor", "negociacion", "marketing", "mercadeo"]},
    "administration": {"label": "Administración y talento humano", "terms": ["administracion", "administrativo", "asistente", "secretaria", "recursos humanos", "talento humano"]},
    "finance": {"label": "Contabilidad y finanzas", "terms": ["contabilidad", "contador", "contable", "finanzas", "financiero", "tesoreria"]},
    "logistics": {"label": "Logística y operaciones", "terms": ["logistica", "inventario", "bodega", "almacen", "operaciones", "transporte", "produccion"]},
    "education": {"label": "Educación y formación", "terms": ["docente", "profesor", "educacion", "pedagogia", "formador", "maestro"]},
    "design": {"label": "Diseño y comunicación", "terms": ["diseno", "diseñador", "comunicacion", "publicidad", "editor", "grafico"]},
    "care": {"label": "Salud: atención y procesos", "terms": ["salud", "enfermeria", "enfermero", "medicina", "medico", "hospital", "clinica"]},
}

# Every bank assesses a narrow skill, with five distinct decisions and feedback.
EXERCISES = {
    "general": ("Comunicación y coordinación", "comunicacion", "Coordina una entrega con información incompleta.", [
        ("Te piden una entrega sin fecha. ¿Qué haces primero?", ["Confirmar alcance, destinatario y plazo", "Prometer que estará hoy", "Esperar a que pregunten"], 0, "Acordar alcance y plazo evita expectativas incompatibles."),
        ("Descubres un retraso que afecta a otra persona. ¿Cómo lo comunicas?", ["Ocultarlo hasta terminar", "Avisar pronto con impacto y alternativas", "Enviar solo una disculpa"], 1, "Un aviso temprano con alternativas permite reorganizar el trabajo."),
        ("Recibes dos instrucciones contradictorias. ¿Qué decisión ayuda?", ["Elegir al azar", "Ignorar ambas", "Confirmar prioridad con quienes las solicitaron"], 2, "Resolver la contradicción antes de actuar evita trabajo desperdiciado."),
        ("Una compañera no entiende una explicación. ¿Qué haces?", ["Reformular con un ejemplo y comprobar comprensión", "Repetir más fuerte", "Dar la conversación por terminada"], 0, "Un ejemplo y una comprobación breve permiten ajustar el mensaje."),
        ("¿Qué cierre facilita seguir una reunión?", ["Solo una lista de asistentes", "Acuerdos, responsables y fechas", "Una transcripción sin acuerdos"], 1, "Los compromisos explícitos permiten dar seguimiento."),
    ]),
    "service": ("Atender y resolver solicitudes", "servicio al cliente", "Atiende una reclamación y acuerda un siguiente paso verificable.", [
        ("Una persona reclama un cobro. ¿Qué haces primero?", ["Prometer devolución inmediata", "Escuchar y verificar el caso", "Transferir sin contexto"], 1, "Comprender y verificar el caso evita promesas sin sustento."),
        ("La solución requiere otro equipo. ¿Cómo escalas?", ["Documentar hechos, acciones y responsable de seguimiento", "Pedir que el cliente repita todo", "Cerrar el caso"], 0, "El contexto documentado evita repetir el proceso."),
        ("No puedes cumplir el plazo prometido. ¿Qué comunicas?", ["Nada hasta resolver", "Que no es tu responsabilidad", "Nuevo plazo realista y alternativas"], 2, "Una expectativa actualizada permite decidir con información."),
        ("¿Qué dato compartes en un canal público?", ["Solo información general sin datos personales", "Identificación del cliente", "Historia completa de pagos"], 0, "Limita los datos personales al canal y al personal autorizados."),
        ("Antes de cerrar una solicitud, ¿qué verificas?", ["Que el cliente dejó de escribir", "Que la solución responde a la necesidad y queda registrada", "Que transcurrieron cinco minutos"], 1, "El cierre requiere confirmar solución y trazabilidad."),
    ]),
    "sales": ("Venta consultiva", "ventas", "Construye una propuesta a partir de la necesidad del cliente.", [
        ("Antes de ofrecer un producto, ¿qué preguntas?", ["Necesidad, presupuesto y criterios de decisión", "Solo el nombre", "Cuánto descuento desea"], 0, "La propuesta debe responder a una necesidad concreta."),
        ("El cliente dice que es costoso. ¿Cómo respondes?", ["Descuento sin preguntar", "Explorar su comparación y explicar valor relevante", "Presionar para cerrar"], 1, "Entender la objeción permite responder con datos útiles."),
        ("El producto no cubre una necesidad esencial. ¿Qué haces?", ["Ocultar la limitación", "Prometer una función inexistente", "Explicar la limitación y una alternativa real"], 2, "Una venta informada evita expectativas falsas."),
        ("¿Qué seguimiento es más útil?", ["Acordar fecha y siguiente decisión", "Llamar cada hora", "Enviar el mismo mensaje a diario"], 0, "Un siguiente paso acordado respeta el proceso del cliente."),
        ("¿Qué métrica evalúa conversión?", ["Cantidad de correos solamente", "Ventas cerradas sobre oportunidades comparables", "Número de reuniones internas"], 1, "La conversión relaciona resultados con oportunidades del mismo periodo."),
    ]),
    "administration": ("Organización documental", "gestion documental", "Organiza solicitudes y documentos con control de acceso.", [
        ("Llegan varias solicitudes. ¿Cómo priorizas?", ["Por orden alfabético", "Por urgencia, impacto y plazo acordado", "Solo las más fáciles"], 1, "La prioridad combina plazo e impacto, no únicamente facilidad."),
        ("¿Cómo nombras versiones de un documento?", ["Con convención, fecha y versión", "Todas final-final", "Sin título"], 0, "Una convención consistente permite localizar y distinguir versiones."),
        ("Te piden datos de nómina por un canal no autorizado. ¿Qué haces?", ["Compartir para ser rápido", "Publicarlos en una carpeta abierta", "Verificar autorización y usar el canal aprobado"], 2, "La información personal requiere acceso autorizado."),
        ("¿Qué facilita encontrar un expediente?", ["Índice y clasificación consistentes", "Archivos duplicados sin criterio", "Solo la memoria de una persona"], 0, "Clasificación e índice permiten recuperar documentos."),
        ("Detectas un dato incorrecto en un registro. ¿Qué haces?", ["Borrar sin dejar rastro", "Corregir con soporte y registrar el cambio", "Ignorarlo"], 1, "El soporte y la trazabilidad permiten revisar la corrección."),
    ]),
    "finance": ("Conciliación de movimientos", "conciliacion bancaria", "Revisa diferencias entre registros y soportes sin asumir causas.", [
        ("Un saldo bancario difiere del libro. ¿Qué haces primero?", ["Modificar el libro al saldo del banco", "Comparar movimientos del mismo periodo", "Registrar la diferencia como gasto"], 1, "La comparación debe usar el mismo corte y documentos de soporte."),
        ("Un depósito está en libros pero no en el extracto. ¿Qué verificas?", ["Fecha, soporte y posible movimiento en tránsito", "Que sea un ingreso falso", "Solo el saldo final"], 0, "Una diferencia temporal debe investigarse con soporte."),
        ("Encuentras una comisión no registrada. ¿Cómo procedes?", ["Eliminarla del extracto", "Repartirla entre clientes", "Validar el soporte y tramitar el ajuste autorizado"], 2, "Los ajustes requieren soporte y aprobación según el procedimiento."),
        ("¿Qué reduce errores en la conciliación?", ["Identificadores, fechas e importes por movimiento", "Comparar únicamente totales", "Redondear todas las cifras"], 0, "La comparación individual permite localizar diferencias."),
        ("¿Cómo cierras una conciliación?", ["Con una cifra sin explicación", "Con partidas explicadas, soportes y revisión", "Borrando las partidas pendientes"], 1, "El cierre debe explicar las diferencias y pendientes."),
    ]),
    "logistics": ("Control de inventarios", "inventarios", "Resuelve diferencias de existencias y prepara una reposición.", [
        ("El conteo físico difiere del sistema. ¿Qué haces?", ["Ajustar sin revisar", "Recontar y comprobar movimientos y unidades", "Cambiar la etiqueta"], 1, "Primero confirma conteo, movimientos y unidad de medida."),
        ("¿Qué significa punto de reposición?", ["Nivel que activa una compra según demanda y plazo", "La capacidad máxima del edificio", "El precio más bajo"], 0, "La reposición considera consumo y tiempo de abastecimiento."),
        ("Un lote tiene fecha de vencimiento cercana. ¿Qué criterio ayuda?", ["Despachar el más nuevo primero siempre", "Mezclar fechas sin registro", "Priorizar el vencimiento más próximo si es apto"], 2, "La rotación por vencimiento reduce pérdidas cuando aplica."),
        ("Recibes mercancía dañada. ¿Qué haces?", ["Separar, documentar y notificar según procedimiento", "Ingresarla como disponible", "Ocultarla en la bodega"], 0, "Separar y registrar evita entregar unidades no conformes."),
        ("¿Qué requiere una entrega trazable?", ["Solo una fotografía", "Referencia, cantidad, fecha y receptor", "Solo el nombre del conductor"], 1, "La trazabilidad vincula qué, cuánto, cuándo y a quién."),
    ]),
    "education": ("Evaluación formativa", "evaluacion formativa", "Usa evidencias de aprendizaje para ajustar una actividad.", [
        ("Antes de evaluar una actividad, ¿qué comunicas?", ["Objetivo y criterios observables", "Solo la nota máxima", "Solo el tiempo disponible"], 0, "Los criterios explican qué evidencia demuestra el aprendizaje."),
        ("La mayoría responde mal la misma pregunta. ¿Qué haces?", ["Repetir la misma explicación sin cambios", "Revisar la dificultad y ajustar la enseñanza", "Asumir falta de interés"], 1, "Un patrón de errores invita a revisar actividad y explicación."),
        ("¿Qué retroalimentación ayuda a mejorar?", ["Eres malo para esto", "Una nota sin explicación", "Un logro concreto y un siguiente paso"], 2, "El feedback describe acciones que la persona puede realizar."),
        ("Hay barreras de acceso al material. ¿Qué haces?", ["Ofrecer formatos accesibles manteniendo el objetivo", "Reducir la nota automáticamente", "Excluir a quien no accede"], 0, "Adaptar el acceso permite evaluar el mismo objetivo."),
        ("¿Cómo compruebas que el ajuste funcionó?", ["Solo preguntar si gustó", "Recoger nueva evidencia y compararla con el criterio", "Repetir la nota anterior"], 1, "La nueva evidencia muestra el avance respecto al objetivo."),
    ]),
    "design": ("Interpretación de un brief", "brief creativo", "Transforma una solicitud de comunicación en una entrega revisable.", [
        ("Un cliente pide algo moderno. ¿Qué aclaras?", ["Objetivo, audiencia, canal y restricciones", "Solo el color favorito", "Nada, eliges tu estilo"], 0, "El objetivo y la audiencia orientan las decisiones creativas."),
        ("¿Cómo justificas una propuesta?", ["Es bonita", "Relacionando decisiones con objetivos y audiencia", "Porque la usa la competencia"], 1, "Los criterios del brief permiten evaluar la propuesta."),
        ("Te entregan una imagen sin licencia conocida. ¿Qué haces?", ["Usarla sin preguntar", "Quitar la marca de agua", "Comprobar permiso o elegir un recurso autorizado"], 2, "Verifica derechos y condiciones antes de utilizar el recurso."),
        ("¿Qué revisión mejora la accesibilidad?", ["Contraste, legibilidad y alternativas textuales", "Solo el tamaño del archivo", "Reducir siempre el texto al mínimo"], 0, "La accesibilidad incluye percibir y comprender el contenido."),
        ("El cliente cambia el alcance. ¿Cómo lo manejas?", ["Aceptar sin revisar fecha", "Documentar el cambio y acordar plazo y entregables", "Ignorar el cambio"], 1, "Un cambio de alcance requiere ajustar acuerdos."),
    ]),
    "care": ("Confidencialidad y atención en salud", "confidencialidad", "Gestiona información y orientación administrativa. No evalúa decisiones clínicas.", [
        ("Alguien solicita información de un paciente. ¿Qué verificas?", ["Identidad, autorización y canal permitido", "Solo que conozca su nombre", "Nada si tiene prisa"], 0, "El acceso exige identidad y autorización según el procedimiento."),
        ("Una persona no comprende una indicación administrativa. ¿Qué haces?", ["Entregar el mismo papel sin explicar", "Explicar con lenguaje claro y comprobar comprensión", "Dar recomendaciones médicas por tu cuenta"], 1, "La orientación debe ser clara y respetar las competencias del cargo."),
        ("Detectas datos personales en una pantalla pública. ¿Qué haces?", ["Compartir una foto", "Ignorarlo", "Restringir exposición y reportar por el canal interno"], 2, "Reduce la exposición y activa el procedimiento de incidentes."),
        ("¿Qué información solicitas para un trámite?", ["La mínima necesaria por el canal autorizado", "Toda la historia clínica siempre", "Datos de toda la familia"], 0, "La minimización evita recopilar información innecesaria."),
        ("Una consulta supera tu función administrativa. ¿Qué haces?", ["Inventar una respuesta", "Derivar al profesional competente con contexto mínimo", "Publicarla en redes"], 1, "La derivación respeta funciones y confidencialidad."),
    ]),
}


def profile_areas(profile):
    text = skill_key(" ".join([str(getattr(profile, "profession", "") or ""), str(getattr(profile, "preferred_sector", "") or ""), *(getattr(profile, "skills", []) or [])]))
    return [area for area, row in AREAS.items() if any(re.search(r"\b" + re.escape(term) + r"\w*\b", text) for term in row["terms"])] or ["general"]


def assessment_banks():
    return {f"{area}-foundations-v1": {"title": title, "skill": skill, "category": area, "context": context, "version": "1", "minutes": 10,
            "questions": [{"id": f"decision-{index + 1}", "prompt": prompt, "choices": choices, "answer": answer, "feedback": feedback}
                          for index, (prompt, choices, answer, feedback) in enumerate(questions)]}
            for area, (title, skill, context, questions) in EXERCISES.items()}


def practice_resources():
    return [{"id": f"practice-{area}-v1", "category": area, "title": title + ": práctica guiada", "skills": [skill], "hours": 1,
             "provider": "TalentSync · práctica local", "kind": "project", "sponsored": False,
             "instructions": f"{context} 1. Describe un caso ficticio de tu área. 2. Explica tres decisiones y sus motivos. 3. Define un resultado observable y cómo comprobarlo. 4. Guarda tu trabajo como evidencia y contrasta tus decisiones en la microprueba."}
            for area, (title, skill, context, _) in EXERCISES.items()]
