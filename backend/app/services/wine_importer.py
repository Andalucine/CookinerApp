"""Read a wine from a shop or winery page (session 8): the schema.org Product data the page
carries for Google, plus what the name and description say about type, grapes, D.O. and
vintage. Nothing is saved: the app shows the preview and the person saves it with the link."""

import re
from dataclasses import dataclass, field

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

__all__ = ["fetch_html", "read_wine", "WinePreview"]


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
    (r"\bcream\b|\bmedium\b|\bpale cream\b", "cream-medium"),
    (r"\boporto\b|\bport\b|\btawny\b|\bruby\b", "oporto"),
    (r"\bmadeira\b|\bmarsala\b", "madeira-marsala"),
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

_SWEETNESS = [
    (r"\bbrut nature\b", "brut_nature"),
    (r"\bextra brut\b", "extra_brut"),
    (r"\bbrut\b", "brut"),
    (r"\bsemidulce\b|\bsemi-dulce\b", "semi_sweet"),
    (r"\bsemiseco\b|\bsemi-seco\b", "off_dry"),
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
    if preview.name:
        # Shops append the site to the title: "Viña Tondonia Reserva 2012 - Delatierra"
        preview.name = re.split(r"\s+[-|–]\s+", preview.name)[0].strip()
    if preview.tasting_notes and len(preview.tasting_notes) > 600:
        preview.tasting_notes = preview.tasting_notes[:597].rsplit(" ", 1)[0] + "…"

    clues = " ".join(x for x in (preview.name, preview.tasting_notes, reader.title) if x)
    preview.category_slug = _first(_TYPE_PATTERNS, preview.name or "") or _first(
        _TYPE_PATTERNS, clues
    )
    preview.ageing = _first(_AGEING, preview.name or "") or _first(_AGEING, clues)
    preview.sweetness = _first(_SWEETNESS, clues)
    preview.vintage = _vintage(preview.name, preview.tasting_notes)
    preview.grapes = _grapes(clues)
    preview.appellation = _appellation(clues)
    preview.country = _country(preview.appellation, clues)

    if not preview.name:
        preview.warnings.append("no_name")
    if not preview.category_slug:
        preview.warnings.append("no_type")
    if not preview.winery:
        preview.warnings.append("no_winery")
    return preview
