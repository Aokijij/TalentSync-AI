"""Rich source evidence for import tests; deliberately separate from real jobs."""


def clear_description(text):
    return ("Funciones: " + text + " Analizar solicitudes, preparar reportes de resultados y coordinar su revisión con el equipo responsable.\n"
            "Requisitos: Profesional en Administración de Empresas. Experiencia mínima de 1 año en análisis y atención de solicitudes. Manejo de Excel, SQL y Python.\n"
            "Condiciones: Salario por convenir. Horario de lunes a viernes de 8 a 17 horas.")


def clear_content():
    from app.domain.services.external_job_content import extract_content
    return extract_content("Analista", clear_description("Analizar información con SQL, Excel y Python."))[0]
