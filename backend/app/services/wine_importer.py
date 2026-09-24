"""Read a wine from a shop or winery page (session 8): the schema.org Product data the page
carries for Google, plus what the name and description say about type, grapes, D.O. and
vintage. Nothing is saved: the app shows the preview and the person saves it with the link."""

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser

from app.models.wine import price_range_for
from app.services.importer import (
    _find,
    _image,
    _name,
    _PageReader,
    _site_name,
    _text,
    fetch_html,
    nice_site_name,
)

__all__ = ["fetch_html", "read_sheet", "read_wine", "WinePreview"]


@dataclass
class WinePreview:
    name: str | None = None
    winery: str | None = None
    category_slug: str | None = None  # a subtype slug of the wine tree, when it can be told
    sweetness: str | None = None
    ageing: str | None = None
    country: str | None = None
    appellation: str | None = None
    grapes: str | None = None
    vintage: int | None = None
    price_range: str | None = None
    source_name: str | None = None  # the shop, as people know it ("Delatierra")
    source_price: float | None = None  # its price at that moment, in euros
    tasting_notes: str | None = None
    image_url: str | None = None
    warnings: list[str] = field(default_factory=list)


# Order matters: the first pattern that matches wins (more specific first)
_TYPE_PATTERNS: list[tuple[str, str]] = [
    (r"\bpalo cortado\b", "palo-cortado"),
    (r"\bmanzanilla\b|\bfino\b", "fino-manzanilla"),
    (r"\bamontillado\b", "amontillado"),
    (r"\boloroso\b", "oloroso"),
    (r"\bpedro xim[eé]nez\b|\bpx\b", "pedro-ximenez"),
    (r"\bmadeira\b|\bmarsala\b|\brainwater\b", "madeira-marsala"),
    # "medium dry" / "medium sweet" say how sweet a wine is, not that it is a cream (session 9)
    (r"\bcream\b|\bpale cream\b|\bmedium\b(?!\s+(?:dry|sweet|rich|seco|dulce))", "cream-medium"),
    (r"\boporto\b|\bport\b|\btawny\b|\bruby\b", "oporto"),
    (r"\bvermut\b|\bvermouth\b", "vermut"),
    (r"\bmoscatel\b|\bmoscato\b", "moscatel"),
    (r"\bfondill[oó]n\b|\brancio\b", "rancios-fondillon"),
    (r"\bvendimia tard[ií]a\b|\bsauternes\b|\btokaji\b|\blate harvest\b", "vendimia-tardia"),
    (r"\bvino de hielo\b|\beiswein\b|\bicewine\b", "vino-hielo"),
    (r"\bmistela\b|\bvino de licor\b", "mistelas"),
    (r"\bcava\b", "cava"),
    (r"\bchamp[aá]n\b|\bchampagne\b", "champan"),
    (r"\bprosecco\b|\bfranciacorta\b|\basti\b", "prosecco"),
    (r"\btxakoli\b|\bchacol[ií]\b|\bvinho verde\b|\blambrusco\b|\baguja\b|\bfrizzante\b", "aguja"),
    (r"\bespumoso\b|\bsparkling\b|\bcr[eé]mant\b|\bsekt\b", "otros-espumosos"),
    (r"\bsidra\b|\bcider\b", "sidra"),
    (r"\bsake\b", "sake"),
    (r"\bsin alcohol\b|\bdesalcoholizado\b|\b0,0\b", "sin-alcohol"),
    (r"\brosado\b|\bros[eé]\b|\bclarete\b", "rosado-fruta"),
    (r"\bblanco\b.*\b(barrica|crianza|fermentado)\b|\bfermentado en barrica\b", "blanco-crianza"),
    (r"\bnaranja\b|\borange wine\b|\bmaceraci[oó]n\b", "blanco-naranja"),
    (
        r"\balbari[nñ]o\b|\bverdejo\b|\bgodello\b|\briesling\b|\bgew[uü]rztraminer\b"
        r"|\bsauvignon blanc\b",
        "blanco-aromatico",
    ),
    (r"\bblanco\b|\bwhite\b", "blanco-joven"),
    (r"\bgran reserva\b|\breserva\b|\bcon cuerpo\b", "tinto-cuerpo-crianza"),
    (r"\bcrianza\b|\broble\b", "tinto-medio"),
    (r"\bjoven\b|\bmaceraci[oó]n carb[oó]nica\b|\bcosechero\b", "tinto-joven"),
    (r"\btinto\b|\bred\b", "tinto-medio"),
]

_AGEING = [
    (r"\bgran reserva\b", "gran_reserva"),
    (r"\breserva\b", "reserva"),
    (r"\bcrianza\b", "crianza"),
    (r"\broble\b|\bbarrica\b", "oak"),
    (r"\bsolera\b", "solera"),
    (r"\bjoven\b", "young"),
]

# Order matters: "medium dry" is off-dry, not dry (session 9: Barbeito Rainwater medium dry)
_SWEETNESS = [
    (r"\bbrut nature\b", "brut_nature"),
    (r"\bextra brut\b", "extra_brut"),
    (r"\bbrut\b", "brut"),
    (r"\bextra dry\b", "extra_dry"),
    (r"\bdemi[- ]sec\b", "demi_sec"),
    (r"\bsemi[- ]?dulce\b|\bmedium sweet\b|\bmedium rich\b|\bsemi[- ]sweet\b", "semi_sweet"),
    (r"\bsemi[- ]?seco\b|\bmedium dry\b|\boff[- ]dry\b", "off_dry"),
    (r"\bdulce\b|\bsweet\b", "sweet"),
    (r"\bseco\b|\bdry\b", "dry"),
]

_GRAPES = [
    "tempranillo", "garnacha", "monastrell", "bobal", "mencía", "mencia", "cariñena", "graciano",
    "mazuelo", "tinta de toro", "tinto fino", "cabernet sauvignon", "merlot", "syrah", "pinot noir",
    "petit verdot", "albariño", "albarino", "verdejo", "godello", "viura", "macabeo", "xarel·lo",
    "xarel.lo", "xarello", "parellada", "palomino", "pedro ximénez", "pedro ximenez", "moscatel",
    "airén", "airen", "chardonnay", "sauvignon blanc", "riesling", "gewürztraminer", "treixadura",
    "loureiro", "hondarrabi zuri", "listán", "malvasía", "malvasia", "zalema", "touriga nacional",
    "tinta negra", "sercial", "verdelho", "boal", "bual", "terrantez", "touriga franca",
    "tinta roriz", "tinta barroca", "garnacha tintorera", "prieto picudo", "listán negro",
    "listán blanco", "sumoll", "trepat", "callet", "manto negro", "juan garcía", "rufete",
    "merseguera", "moscatel de alejandría", "pansa blanca", "xarel·lo vermell", "garnacha blanca",
    "cabernet franc", "nebbiolo", "sangiovese", "tempranillo blanco", "maturana",
]  # fmt: skip

_APPELLATION = re.compile(
    r"\b(D\.?\s?O\.?\s?(?:Ca\.?|P\.?)?|DOCa|DOP|I\.?G\.?P\.?|V\.?T\.?)\s+"
    r"([A-ZÁÉÍÓÚÑ][\w\-\.'’ ]{2,40}?)(?=[,.;:()\n]|\s-\s|\s\||$)"
)
_KNOWN_APPELLATIONS = [
    "Rioja", "Ribera del Duero", "Rías Baixas", "Rueda", "Priorat", "Toro", "Jerez",
    "Montilla-Moriles",
    "Jumilla", "Bierzo", "Ribeira Sacra", "Valdeorras", "Penedès", "Cava", "Navarra", "Somontano",
    "Utiel-Requena", "Valencia", "Alicante", "Yecla", "Cigales", "Txakoli", "Condado de Huelva",
    "Málaga", "Manchuela", "La Mancha", "Valdepeñas", "Campo de Borja", "Calatayud", "Cariñena",
    "Montsant", "Empordà", "Costers del Segre", "Terra Alta", "Tarragona", "Ribeiro", "Monterrei",
    "Lanzarote", "Champagne", "Douro", "Vinho Verde", "Chianti", "Barolo", "Bordeaux", "Borgoña",
]  # fmt: skip


# What a shop's "Tipo de vino" usually says (Blanco, Tinto, Rosado): a family, not a subtype.
# The name and the description may refine it within that family ("albariño" → aromatic white).
_GENERIC_TYPES = {"blanco-joven": "blanco-", "tinto-medio": "tinto-", "rosado-fruta": "rosado-"}


def _pick_type(from_sheet: str | None, from_words: str | None) -> str | None:
    if from_sheet is None:
        return from_words
    family = _GENERIC_TYPES.get(from_sheet)
    if family and from_words and from_words.startswith(family):
        return from_words
    return from_sheet


def _first(patterns: list[tuple[str, str]], text: str) -> str | None:
    for pattern, code in patterns:
        if re.search(pattern, text, re.I):
            return code
    return None


def _price(offer) -> float | None:
    if isinstance(offer, list):
        offer = offer[0] if offer else None
    if not isinstance(offer, dict):
        return None
    raw = offer.get("price") or offer.get("lowPrice")
    try:
        price = float(str(raw).replace(",", "."))
    except (TypeError, ValueError):
        return None
    return price if price > 0 else None


def _vintage(*texts: str | None) -> int | None:
    for text in texts:
        if not text:
            continue
        for match in re.findall(r"\b(19[5-9]\d|20[0-4]\d)\b", text):
            return int(match)
    return None


def _grapes(text: str) -> str | None:
    low = text.lower()
    found = []
    for grape in _GRAPES:
        if grape in low and grape not in found:
            # keep one spelling of each (with accents when we know it)
            if grape in (
                "mencia",
                "albarino",
                "xarel.lo",
                "xarello",
                "pedro ximenez",
                "airen",
                "malvasia",
            ):
                continue
            found.append(grape)
    return ", ".join(found) or None


def _mentions_any(grapes: str, text: str) -> bool:
    low = text.lower()
    return any(g.strip() and g.strip().lower() in low for g in re.split(r"[,;/]| y ", grapes))


def _appellation(text: str) -> str | None:
    match = _APPELLATION.search(text)
    if match:
        return " ".join(match.group(0).split())
    for name in _KNOWN_APPELLATIONS:
        if re.search(rf"\b{re.escape(name)}\b", text, re.I):
            return name
    return None


def _country(appellation: str | None, text: str) -> str | None:
    low = text.lower()
    if appellation and any(
        a.lower() in appellation.lower()
        for a in _KNOWN_APPELLATIONS[: _KNOWN_APPELLATIONS.index("Champagne")]
    ):
        return "España"
    for word, country in (
        ("francia", "Francia"), ("france", "Francia"), ("italia", "Italia"), ("italy", "Italia"),
        ("portugal", "Portugal"), ("alemania", "Alemania"), ("germany", "Alemania"),
        ("argentina", "Argentina"), ("chile", "Chile"), ("españa", "España"), ("spain", "España"),
    ):  # fmt: skip
        if word in low:
            return country
    return None


# --- The data sheet of the page --------------------------------------------------------------
# Shops print the facts as label + value pairs ("Bodega: Zarate", "Origen: D.O. Rías Baixas"),
# often inside the purchase form, which the recipe reader skips. This small reader keeps every
# short text of the page in order and pairs each known label with the text that follows it.

_SHEET_LABELS: dict[str, str] = {
    "bodega": "winery", "productor": "winery", "elaborador": "winery",
    "winery": "winery", "producer": "winery",
    "origen": "appellation", "denominación": "appellation", "denominacion": "appellation",
    "denominación de origen": "appellation", "d.o.": "appellation", "región": "appellation",
    "region": "appellation", "zona": "appellation", "appellation": "appellation",
    "país": "country", "pais": "country", "country": "country",
    "uva": "grapes", "uvas": "grapes", "variedad": "grapes", "variedades": "grapes",
    "variedad de uva": "grapes", "grape": "grapes", "grapes": "grapes", "varietal": "grapes",
    "añada": "vintage", "cosecha": "vintage", "vintage": "vintage",
    "tipo de vino": "type", "type": "type",
    "crianza": "ageing", "envejecimiento": "ageing", "ageing": "ageing", "aging": "ageing",
}  # fmt: skip
_COUNTRIES = {
    "españa", "spain", "francia", "france", "italia", "italy", "portugal", "alemania", "germany",
    "argentina", "chile", "austria", "hungría", "hungria", "hungary", "estados unidos", "usa",
    "australia", "nueva zelanda", "new zealand", "sudáfrica", "south africa",
}  # fmt: skip


class _SheetReader(HTMLParser):
    """Every leaf text of the page, in order, plus the paragraphs (for the description)."""

    _LEAVES = {"h1", "h2", "h3", "h4", "h5", "h6", "dt", "dd", "th", "td", "a", "span", "p",
               "li", "strong", "b", "label", "div"}  # fmt: skip
    _SKIP = {"script", "style", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.texts: list[str] = []
        self.paragraphs: list[str] = []
        self._skip = 0
        self._stack: list[list[str]] = []

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP:
            self._skip += 1
        if tag in self._LEAVES:
            self._stack.append([])
        elif tag == "br" and self._stack:
            self._stack[-1].append(" ")

    def handle_endtag(self, tag):
        if tag in self._SKIP and self._skip:
            self._skip -= 1
        if tag in self._LEAVES and self._stack:
            text = " ".join("".join(self._stack.pop()).split())
            if text:
                if tag == "p":
                    self.paragraphs.append(text)
                self.texts.append(text)

    def handle_data(self, data):
        if not self._skip and self._stack:
            self._stack[-1].append(data)
            # the same text belongs to the enclosing leaves too (a <p> around <a>s)
            for open_leaf in self._stack[:-1]:
                open_leaf.append(data)


def _is_grape(text: str) -> bool:
    low = text.lower().strip()
    return any(low == g or low.startswith(g + " ") for g in _GRAPES)


def _looks_like_grape_menu(following: list[str]) -> bool:
    """The value and the texts after it are all grape names: a shop filter, not a data sheet."""
    short = [t for t in following if t and len(t) <= 40]
    return len(short) >= 2 and all(_is_grape(t) for t in short[:2]) and len(following) >= 3


def read_sheet(html: str) -> dict[str, str]:
    """{"winery": "Bodegas Zarate", "appellation": "D.O. Rías Baixas", "country": "España"...}
    from the label + value pairs of the page. Values are the text right after a label; a
    country printed next to the origin is kept apart."""
    reader = _SheetReader()
    reader.feed(html)
    reader.close()
    sheet: dict[str, str] = {}
    texts = reader.texts
    for i, text in enumerate(texts[:-1]):
        key = _SHEET_LABELS.get(text.lower().rstrip(":").strip())
        if not key or key in sheet:
            continue
        value = texts[i + 1].strip()
        if not value or len(value) > 120 or _SHEET_LABELS.get(value.lower().rstrip(":")):
            continue
        if key == "grapes" and _looks_like_grape_menu(texts[i + 1 : i + 4]):
            continue  # a filter of the shop ("Uva: Albariño · Garnacha · Mencía…"), session 9
        if key == "appellation":
            for country in _COUNTRIES:
                if value.lower().endswith(" " + country):
                    value = value[: -len(country) - 1].strip()
                    sheet.setdefault("country", country.title())
        sheet[key] = value
        if key == "appellation" and i + 2 < len(texts) and texts[i + 2].lower() in _COUNTRIES:
            sheet.setdefault("country", texts[i + 2])
    if "country" in sheet:
        sheet["country"] = _COUNTRY_NAMES.get(sheet["country"].lower(), sheet["country"])
    long = [p for p in reader.paragraphs if 80 <= len(p) <= 2000]
    if long:
        sheet["description"] = max(long, key=len)
    return sheet


_COUNTRY_NAMES = {
    "spain": "España", "france": "Francia", "italy": "Italia", "germany": "Alemania",
    "hungary": "Hungría", "hungria": "Hungría", "usa": "Estados Unidos",
    "new zealand": "Nueva Zelanda", "south africa": "Sudáfrica",
}  # fmt: skip


def read_wine(html: str, url: str) -> WinePreview:
    reader = _PageReader()
    reader.feed(html)
    reader.close()
    product = _find(reader.json_ld, "product")
    preview = WinePreview()

    if product:
        preview.name = _text(product.get("name"))
        preview.winery = _name(product.get("brand")) or _name(product.get("manufacturer"))
        preview.tasting_notes = _text(product.get("description"))
        preview.image_url = _image(product.get("image"))
        preview.source_price = _price(product.get("offers"))
        preview.price_range = price_range_for(preview.source_price)
    else:
        preview.warnings.append("no_product_data")
        preview.name = _text(reader.meta.get("og:title")) or _text(reader.title)
        preview.tasting_notes = _text(reader.meta.get("og:description")) or _text(
            reader.meta.get("description")
        )
        preview.image_url = reader.meta.get("og:image")

    preview.source_name = nice_site_name(_site_name(reader, None, url))
    if preview.source_name and "." in preview.source_name:
        preview.source_name = preview.source_name.split(".")[0].capitalize()  # delatierra.com
    # Shops put themselves as the "brand" and the name as the "description": not wine facts
    if (
        preview.winery
        and preview.source_name
        and preview.winery.lower() == preview.source_name.lower()
    ):
        preview.winery = None
    if (
        preview.tasting_notes
        and preview.name
        and preview.tasting_notes.strip() == preview.name.strip()
    ):
        preview.tasting_notes = None

    sheet = read_sheet(html)
    preview.winery = preview.winery or sheet.get("winery")
    preview.appellation = sheet.get("appellation")
    preview.country = sheet.get("country")
    preview.grapes = sheet.get("grapes")
    if sheet.get("vintage") and re.fullmatch(r"(19|20)\d\d", sheet["vintage"]):
        preview.vintage = int(sheet["vintage"])
    if not preview.tasting_notes and sheet.get("description"):
        preview.tasting_notes = sheet["description"]
    if preview.name:
        # Shops append the site to the title: "Viña Tondonia Reserva 2012 - Delatierra"
        preview.name = re.split(r"\s+[-|–]\s+", preview.name)[0].strip()
    if preview.tasting_notes and len(preview.tasting_notes) > 600:
        preview.tasting_notes = preview.tasting_notes[:597].rsplit(" ", 1)[0] + "…"

    # The sheet's own words about type and ageing count first ("Tipo de vino: Blanco")
    typed = " ".join(x for x in (sheet.get("type"), sheet.get("ageing")) if x)
    clues = " ".join(x for x in (preview.name, preview.tasting_notes, reader.title) if x)
    # The sheet's "Tipo de vino" first, then the name, then the description (session 9:
    # "Barbeito rainwater medium dry" is a madeira, whatever "medium" suggests)
    preview.category_slug = _pick_type(
        _first(_TYPE_PATTERNS, sheet.get("type") or ""),
        _first(_TYPE_PATTERNS, preview.name or "") or _first(_TYPE_PATTERNS, f"{typed} {clues}"),
    )
    preview.ageing = (
        _first(_AGEING, preview.name or "") or _first(_AGEING, typed) or _first(_AGEING, clues)
    )
    preview.sweetness = _first(_SWEETNESS, f"{typed} {clues}")
    preview.vintage = preview.vintage or _vintage(preview.name, preview.tasting_notes)
    # The sheet's grape is kept when the page mentions it; if the page names other grapes and
    # not that one, the page wins (session 9: a Madeira came out with "Mencía" from a menu)
    from_text = _grapes(clues)
    if preview.grapes and from_text and not _mentions_any(preview.grapes, clues):
        preview.grapes = from_text
    preview.grapes = preview.grapes or from_text
    preview.appellation = preview.appellation or _appellation(clues)
    preview.country = preview.country or _country(preview.appellation, clues)

    if not preview.name:
        preview.warnings.append("no_name")
    if not preview.category_slug:
        preview.warnings.append("no_type")
    if not preview.winery:
        preview.warnings.append("no_winery")
    return preview
