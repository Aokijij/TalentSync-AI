# ruff: noqa: F811
from textwrap import dedent

import pytest
from pydantic import ValidationError
from test_api_flows import client, register  # noqa: F401

from app.api.schemas.profile import ProfileUpdate
from app.domain.services.career_writing import responsibility_parts, rewrite_experience
from app.infrastructure.nlp import resumes
from app.infrastructure.nlp.text_processor import text_processor

EDUCATION = dedent('''
FORMACIÓN ACADÉMICA
Pregrado: Construcciones Civiles – Décimo semestre (En curso)
Tecnóloga: Construcción de Edificaciones - 2019
Técnica: Construcción y Diseño de Edificaciones - 2015
Bachiller: I.E. Colegio de Ejemplo - 2015
Cursos y diplomados:
Curso de AutoCAD
Diplomado en gestión de proyectos
EXPERIENCIA LABORAL
''')


def test_import_keeps_explicit_education_level_and_training_type():
    _, studies, training = text_processor.extract_resume_items(EDUCATION)
    assert [row['level'] for row in studies] == ['university', 'technologist', 'technical', 'secondary']
    assert [row['kind'] for row in training] == ['course', 'diploma']
    assert ProfileUpdate(educations=studies).educations[0]['is_current']
    _, unknown, _ = text_processor.extract_resume_items('FORMACIÓN ACADÉMICA\nConocimientos en construcción\nEXPERIENCIA LABORAL')
    assert not unknown or all(not row.get('level') for row in unknown)


def test_reimport_fills_level_without_overwriting_manual_education(client, monkeypatch, tmp_path):
    from app.core.config import settings
    monkeypatch.setattr(settings, 'upload_dir', str(tmp_path))
    _, headers = register(client, 'education-level-import')
    monkeypatch.setattr(resumes, 'extract_pdf_text', lambda _: EDUCATION)
    for _ in range(2):
        response = client.post('/api/v1/profiles/me/cv', headers=headers, files={'file': ('cv.pdf', b'%PDF-test', 'application/pdf')})
        assert response.status_code == 200, response.text
        assert [row['level'] for row in response.json()['educations']] == ['university', 'technologist', 'technical', 'secondary']
    profile = response.json()
    profile['educations'][0]['level'] = 'technical'
    assert client.put('/api/v1/profiles/me', headers=headers, json=profile).status_code == 200
    response = client.post('/api/v1/profiles/me/cv', headers=headers, files={'file': ('cv.pdf', b'%PDF-test', 'application/pdf')})
    assert response.json()['educations'][0]['level'] == 'technical'


def test_training_types_accept_legacy_and_validate_new_records():
    assert ProfileUpdate(certifications=[{'name': 'Formación anterior'}]).certifications[0].get('kind') is None
    assert ProfileUpdate(certifications=[{'name': 'Gestión', 'kind': 'diploma'}]).certifications[0]['kind'] == 'diploma'
    with pytest.raises(ValidationError):
        ProfileUpdate(certifications=[{'kind': 'invalid'}])


def test_concatenated_infinitives_become_separate_complete_bullets():
    actions = ['Controlar documentación (contratos, actas, informes)', 'Llevar seguimiento de costos y presupuesto', 'Gestionar compras y proveedores', 'Controlar personal (asistencia, nómina, pagos)', 'Apoyar cronograma y avance de obra', 'Manejar facturación y cuentas de cobro', 'Verificar cumplimiento legal y contractual', 'Apoyo en diseño y modificaciones en planos']
    description = ' '.join(actions)
    assert responsibility_parts(description) == actions
    proposal = rewrite_experience({'description': description}, style='bullets')['text']
    assert len(proposal.splitlines()) == len(actions)
    for action in actions[:-1]:
        assert action in proposal
    assert responsibility_parts('Gestionar y controlar compras para Verificar entregas') == ['Gestionar y controlar compras para Verificar entregas']
