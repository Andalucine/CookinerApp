from app.services import importer
from scripts import check_import
from tests.services.test_importer import page


def test_summary_of_a_page(monkeypatch):
    monkeypatch.setattr(importer, "fetch_html", lambda url: (url, page()))
    text = check_import.summary("https://ejemplo.test/lentejas")
    assert text.startswith("✓ https://ejemplo.test/lentejas")
    assert "Ingredientes: 4" in text and "Tiempo: 75 min" in text
    assert "300 g de lentejas pardinas  →  300.0 | g | lentejas pardinas" in text


def test_summary_of_a_failure(monkeypatch):
    def fail(url):
        raise importer.FetchFailed

    monkeypatch.setattr(importer, "fetch_html", fail)
    assert "No se pudo abrir" in check_import.summary("https://ejemplo.test/x")
    assert check_import.main([]) == 1
