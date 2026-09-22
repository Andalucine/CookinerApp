"""Minimal i18n helper: t(key, lang) returns the user-facing text."""

from app.i18n import en, es

_CATALOGS = {"es": es.TEXTS, "en": en.TEXTS}


def t(key: str, lang: str = "es") -> str:
    catalog = _CATALOGS.get(lang, _CATALOGS["es"])
    return catalog.get(key, _CATALOGS["es"].get(key, key))
