from app.application.use_cases.job_imports import listing_fingerprint


def test_listing_fingerprint_ignores_case_accents_and_provider_ids():
    first = listing_fingerprint(
        "Compañía de Datos S.A.S.", "Analista de Información", "Bogotá", "Bogotá D.C."
    )
    second = listing_fingerprint(
        "COMPANIA DE DATOS SAS", "analista de informacion", "bogota", "Bogotá D.C."
    )

    assert first == second
    assert first != listing_fingerprint(
        "Compañía de Datos S.A.S.", "Ingeniero de datos", "Bogotá", "Bogotá D.C."
    )
