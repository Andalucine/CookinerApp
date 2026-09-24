"""Read a wine page of Vinoselección (session 9: the app's cellar is the shop's catalogue).

The general wine reader (`wine_importer`) takes the schema.org data (name, price, photo). What
it cannot guess on this shop is done here, from how its pages are built:

- Its menus carry filters with the same labels as a data sheet ("Tipo de vino: Tinto",
  "País: Francia"...), so the general sheet reader took them for the wine's. The real sheet
  comes after the "Añadir al carrito" button, under "Características generales", as label and
  value lines: Tipo de vino, Región, Variedad de uva... "Características de consumo" brings
  Maridaje and the serving temperature; "Notas de cata" and "La bodega → Bodega" follow.
- The schema.org offer says InStock even for pages of wines sold years ago. What tells if a wine
  can be bought is the shop's own analytics data ("view_item" with "is_in_stock": "Yes"):
  old pages and country selections carry it empty.
"""

import re
from html import unescape

from app.models.wine import SHOP_NAMES, SHOP_VINOSELECCION
from app.services.wine_importer import WinePreview, read_wine

# Labels of the data sheet, as the shop writes them
_SHEET_LABELS = {
    "Tipo de vino": "type",
    "Región": "appellation",
    "Variedad de uva": "grapes",
    "Tipo de barrica": None,
    "Tipo de botella": None,
    "Permanencia en barrica": "barrel",
    "Capacidad (cl)": None,
    "Graduación (% vol.)": None,
    "Añada": "vintage",
    "Embotellado": None,
    "Acidez total (g/l)": None,
    "Acidez volatil (g/l)": None,
    "Azúcar": None,
    "PH": None,
    "Maridaje": "pairing",
    "Servicio": None,
    "Temperatura servicio": None,
}
# Headings where a block ends
_HEADINGS = {
    "Características generales",
    "Características de consumo",
    "Información general",
    "Proceso de elaboración",
    "Notas de cata",
    "La bodega",
    "Compra con total confianza",
}


def page_lines(html: str) -> list[str]:
    """The visible text of the page, one line per text piece (scripts, styles and comments out)."""
    html = re.sub(r"<(script|style)\b.*?</\1>", "\n", html, flags=re.S | re.I)
    html = re.sub(r"<!--.*?-->", "\n", html, flags=re.S)
    text = unescape(re.sub(r"<[^>]+>", "\n", html))
    return [line.strip() for line in text.split("\n") if line.strip()]


def _join(parts: list[str]) -> str:
    """Pieces of one value back into a sentence ("La", "Vicalanda", "Reserva" → one line)."""
    text = " ".join(parts)
    text = re.sub(r"\s+([,.;:)])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()


def _grapes(parts: list[str]) -> str | None:
    """["15%", "Garnacha tinta", ", 85%", "Tempranillo"] → "garnacha tinta, tempranillo"."""
    names = []
    for part in parts:
        clean = re.sub(r"[,;]?\s*\d+(?:[.,]\d+)?\s*%", "", part).strip(" ,;")
        if clean:
            names.append(clean.lower())
    return ", ".join(dict.fromkeys(names)) or None


def read_sheet(html: str) -> dict[str, str]:
    """The wine's data sheet: type, appellation, grapes, winery, vintage, pairing and tasting
    notes, read from the part of the page after the "Añadir al carrito" button."""
    lines = page_lines(html)
    start = lines.index("Añadir al carrito") + 1 if "Añadir al carrito" in lines else 0
    lines = lines[start:]
    sheet: dict[str, str] = {}
    values: dict[str, list[str]] = {}
    current: str | None = None
    block: str | None = None
    for position, line in enumerate(lines):
        if line in _HEADINGS:
            block, current = line, None
            if line == "Compra con total confianza":
                break
            continue
        if block in ("Características generales", "Características de consumo") and (
            line in _SHEET_LABELS
        ):
            current = _SHEET_LABELS[line] or "_ignored"
            values.setdefault(current, [])
            continue
        if block == "Notas de cata":
            values.setdefault("tasting", []).append(line)
        elif block == "La bodega":
            if line == "Bodega" and position + 1 < len(lines):
                values.setdefault("winery", []).append(lines[position + 1])
                block = None
        elif current:
            values[current].append(line)
    for key, parts in values.items():
        if key == "_ignored" or not parts:
            continue
        sheet[key] = _grapes(parts) if key == "grapes" else _join(parts)
    if "tasting" in sheet:
        sheet["description"] = sheet.pop("tasting")
    if "barrel" in sheet:
        # "Permanencia en barrica: 14 meses" says it is aged, not how (crianza, reserva...)
        sheet["ageing"] = sheet.pop("barrel")
    return sheet


def in_stock(html: str) -> bool:
    """What the shop's analytics say about this page: on sale only with "is_in_stock": "Yes"."""
    text = unescape(html)
    match = re.search(r'"view_item".{0,4000}?"is_in_stock"\s*:\s*"(\w+)"', text, re.S)
    return bool(match) and match.group(1).lower() in ("yes", "true", "1")


def read(html: str, url: str) -> WinePreview:
    """A Vinoselección page as a wine preview: the general reader with this shop's data sheet,
    the stock from its analytics, its own tasting notes and pairing."""
    sheet = read_sheet(html)
    preview = read_wine(html, url, sheet=sheet)
    preview.in_stock = in_stock(html)
    preview.source_name = SHOP_NAMES[SHOP_VINOSELECCION]
    if sheet.get("description"):
        preview.tasting_notes = sheet["description"][:600]
    preview.pairing_notes = sheet.get("pairing")
    return preview
