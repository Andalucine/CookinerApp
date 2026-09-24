"""Minimal i18n helper: t(key, lang) returns the user-facing text."""

from app.i18n import de, en, es, fr, nl

LANGUAGES = ("es", "en", "fr", "nl", "de")
LANGUAGE_PATTERN = "^(es|en|fr|nl|de)$"

_CATALOGS = {"es": es.TEXTS, "en": en.TEXTS, "fr": fr.TEXTS, "nl": nl.TEXTS, "de": de.TEXTS}


def t(key: str, lang: str = "es") -> str:
    catalog = _CATALOGS.get(lang, _CATALOGS["es"])
    return catalog.get(key, _CATALOGS["es"].get(key, key))
