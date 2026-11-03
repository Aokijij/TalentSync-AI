from app.application.use_cases.profiles import _refresh_imported


def test_refresh_removes_obsolete_unedited_import_and_preserves_manual_work():
    old = {"role": "Wrong role", "company": "Wrong employer", "description": "Mixed columns"}
    manual = {"role": "Analista", "company": "Added manually", "description": "Confirmed duties"}
    corrected = {"role": "Developer", "company": "Actual employer", "description": "Interfaces"}
    assert _refresh_imported([old, manual], [corrected], [old], ("role", "company")) == [manual, corrected]


def test_refresh_preserves_manual_edits_and_remains_idempotent():
    imported = {"role": "Analista", "company": "Empresa", "description": "Original"}
    edited = {**imported, "description": "Confirmed by person", "start_date": "2020-03"}
    detected = {**imported, "description": "New extraction"}
    once = _refresh_imported([edited], [detected], [imported], ("role", "company"))
    assert once == [edited]
    assert _refresh_imported(once, [detected], [detected], ("role", "company")) == [edited]


def test_no_provenance_never_removes_existing_records():
    old = {"degree": "Study", "institution": "Institute"}
    assert _refresh_imported([old], [], None, ("degree", "institution")) == [old]
