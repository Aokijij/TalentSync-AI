import pytest

from app.domain.services.offer_skills import infer_offer_skills


@pytest.mark.parametrize(
    "text,detected,expected",
    [
        (
            "Trabajarás con Excel y SAP.",
            ["excel", "sap"],
            [("excel", False, "basic"), ("sap", False, "basic")],
        ),
        (
            "Excel avanzado obligatorio y SAP deseable.",
            ["excel", "sap"],
            [("excel", True, "advanced"), ("sap", False, "basic")],
        ),
        (
            "Se requiere dominio avanzado de Excel y SAP.",
            ["excel", "sap"],
            [("excel", True, "advanced"), ("sap", True, "advanced")],
        ),
        (
            "Esenciales:\nExcel intermedio\nDeseables:\nSAP",
            ["excel", "sap"],
            [("excel", True, "intermediate"), ("sap", False, "basic")],
        ),
        ("No se requiere SQL.", ["sql"], [("sql", False, "basic")]),
        (
            "Esencial al ingresar (nivel intermedio):\nExcel\nSAP\nDeseables:\nSQL",
            ["excel", "sap", "sql"],
            [
                ("excel", True, "intermediate"),
                ("sap", True, "intermediate"),
                ("sql", False, "basic"),
            ],
        ),
        (
            "Excel avanzado, SAP básico.",
            ["excel", "excel avanzado", "sap"],
            [("excel", False, "advanced"), ("sap", False, "basic")],
        ),
        (
            "SQL intermedio indispensable; Python básico deseable.",
            ["sql", "python"],
            [("sql", True, "intermediate"), ("python", False, "basic")],
        ),
    ],
)
def test_explicit_context_and_conservative_defaults(text, detected, expected):
    rows = infer_offer_skills(text, detected)
    assert [(row["skill"], row["essential"], row["level"]) for row in rows] == expected
    assert all(row["weight"] == 1 for row in rows)
