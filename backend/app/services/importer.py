"""Import a recipe from a web page: download it safely and read the recipe it publishes.

Most recipe sites publish the recipe as schema.org "Recipe" data in JSON-LD (it is what search
engines read), so that is the main source. Pages without it (plain blogs) are read from their
text: the "Ingredientes" heading and its list, and the preparation steps; the preview then asks
the user to check it. With neither, only the title and the photo. Nothing is saved here: the
user sees a preview, edits it and confirms.
"""

import ipaddress
import json
import re
import socket
from dataclasses import dataclass, field
from html import unescape
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

import httpx

MAX_BYTES = 3 * 1024 * 1024
TIMEOUT_SECONDS = 10
MAX_REDIRECTS = 5
USER_AGENT = "CookinerApp/0.4 (+https://cookinerapp.com; cuaderno de cocina personal)"


class InvalidUrl(Exception):
    pass


class FetchFailed(Exception):
    pass


class NoRecipeFound(Exception):
    pass


# --- Download -----------------------------------------------------------------------------


def _check_public_host(url: str) -> None:
    """Only http(s) to public addresses: the server must never be used to reach private
    machines (localhost, the database, the internal network)."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise InvalidUrl
    try:
        infos = socket.getaddrinfo(parsed.hostname, parsed.port or None)
    except socket.gaierror:
        raise FetchFailed from None
    for info in infos:
        address = ipaddress.ip_address(info[4][0])
        if not address.is_global:
            raise InvalidUrl


def fetch_html(url: str) -> tuple[str, str]:
    """Download a page. Returns (final_url, html). Follows redirects checking each hop."""
    current = url
    with httpx.Client(
        timeout=TIMEOUT_SECONDS,
        follow_redirects=False,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
    ) as client:
        for _ in range(MAX_REDIRECTS + 1):
            _check_public_host(current)
            try:
                with client.stream("GET", current) as response:
                    if response.is_redirect:
                        current = urljoin(current, response.headers.get("location", ""))
                        continue
                    if response.status_code != 200:
                        raise FetchFailed
                    body = b""
                    for chunk in response.iter_bytes():
                        body += chunk
                        if len(body) > MAX_BYTES:
                            raise FetchFailed
                    encoding = response.encoding or "utf-8"
                    return current, body.decode(encoding, errors="replace")
            except httpx.HTTPError:
                raise FetchFailed from None
    raise FetchFailed


# --- Reading the page ---------------------------------------------------------------------


_HEADINGS = {"h1", "h2", "h3", "h4", "h5", "h6"}
_BLOCKS = _HEADINGS | {"p", "li"}
_SKIP = {"script", "style", "noscript", "nav", "footer", "form", "button", "select"}


class _PageReader(HTMLParser):
    """Collects JSON-LD blocks, <meta> tags, YouTube iframes and the text blocks of the page
    (headings, paragraphs and list items, in order) for pages without recipe data."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.json_ld: list[str] = []
        self.meta: dict[str, str] = {}
        self.iframes: list[str] = []
        self.title = ""
        # (kind, text, ordered): kind is "h1".."h6", "p" or "li"; ordered for <ol> items
        self.blocks: list[tuple[str, str, bool]] = []
        self._in_json_ld = False
        self._in_title = False
        self._buffer: list[str] = []
        self._skip_depth = 0
        self._block: str | None = None
        self._block_text: list[str] = []
        self._lists: list[bool] = []  # stack of open lists: True for <ol>

    def _close_block(self) -> None:
        if self._block:
            text = " ".join("".join(self._block_text).split())
            if text:
                ordered = self._block == "li" and bool(self._lists) and self._lists[-1]
                self.blocks.append((self._block, text, ordered))
        self._block, self._block_text = None, []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag in _SKIP and not (tag == "script" and "ld+json" in a.get("type", "").lower()):
            self._skip_depth += 1
        if tag in ("ul", "ol"):
            self._lists.append(tag == "ol")
        elif tag in _BLOCKS:
            self._close_block()
            self._block = tag
        elif tag == "br" and self._block:
            self._block_text.append(" ")
        if tag == "script" and a.get("type", "").lower() == "application/ld+json":
            self._in_json_ld, self._buffer = True, []
        elif tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key and "content" in a:
                self.meta.setdefault(key, a["content"])
        elif tag == "iframe" and a.get("src"):
            self.iframes.append(a["src"])
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in _SKIP and self._skip_depth and not (tag == "script" and self._in_json_ld):
            self._skip_depth -= 1
        if tag == "script" and self._in_json_ld:
            self.json_ld.append("".join(self._buffer))
            self._in_json_ld = False
        elif tag == "title":
            self._in_title = False
        elif tag in _BLOCKS and self._block == tag:
            self._close_block()
        elif tag in ("ul", "ol"):
            self._close_block()
            if self._lists:
                self._lists.pop()

    def handle_data(self, data):
        if self._in_json_ld:
            self._buffer.append(data)
        elif self._in_title:
            self.title += data
        elif self._block and not self._skip_depth:
            self._block_text.append(data)

    def close(self):
        super().close()
        self._close_block()


def _types(node: dict) -> set[str]:
    t = node.get("@type", [])
    return {x.lower() for x in (t if isinstance(t, list) else [t]) if isinstance(x, str)}


def _walk(node):
    """Every dict inside a JSON-LD document (handles @graph and lists)."""
    if isinstance(node, dict):
        yield node
        for value in node.values():
            if isinstance(value, (dict, list)):
                yield from _walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from _walk(item)


def _find(blocks: list[str], wanted: str) -> dict | None:
    for raw in blocks:
        try:
            data = json.loads(raw.strip())
        except ValueError:
            continue
        for node in _walk(data):
            if wanted in _types(node):
                return node
    return None


def _text(value) -> str | None:
    """Plain text from a JSON-LD value: strips tags and entities, collapses spaces."""
    if value is None:
        return None
    if isinstance(value, list):
        value = " ".join(str(v) for v in value if v)
    if isinstance(value, dict):
        value = value.get("name") or value.get("text") or ""
    clean = re.sub(r"<[^>]+>", " ", unescape(str(value)))
    clean = " ".join(clean.split())
    return clean or None


def _name(value) -> str | None:
    """Name of an author/publisher: a string, an object or a list of them."""
    if isinstance(value, list):
        names = [_name(v) for v in value]
        return ", ".join(n for n in names if n) or None
    if isinstance(value, dict):
        return _text(value.get("name"))
    return _text(value)


def _image(value) -> str | None:
    if isinstance(value, list):
        return next((i for i in (_image(v) for v in value) if i), None)
    if isinstance(value, dict):
        return value.get("url") or value.get("contentUrl")
    return value if isinstance(value, str) and value else None


_DURATION = re.compile(r"^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?$", re.I)


def iso_minutes(value) -> int | None:
    """'PT1H30M' → 90. Anything else → None."""
    if not isinstance(value, str):
        return None
    m = _DURATION.match(value.strip())
    if not m or not any(m.groups()):
        return None
    days, hours, minutes, seconds = (int(g) if g else 0 for g in m.groups())
    total = days * 1440 + hours * 60 + minutes + (1 if seconds >= 30 else 0)
    return total or None


def _servings(value) -> int | None:
    """'4 personas', ['4', '4 raciones'], 6 → first whole number found."""
    if isinstance(value, list):
        return next((s for s in (_servings(v) for v in value) if s), None)
    if isinstance(value, (int, float)):
        return int(value) or None
    if isinstance(value, str):
        m = re.search(r"\d+", value)
        return int(m.group()) if m and int(m.group()) > 0 else None
    return None


def _instructions(value) -> str | None:
    """A string, a list of HowToStep, or HowToSections with their steps → numbered text."""
    steps: list[str] = []

    def collect(node):
        if isinstance(node, str):
            text = _text(node)
            if text:
                steps.append(text)
        elif isinstance(node, list):
            for item in node:
                collect(item)
        elif isinstance(node, dict):
            if "howtosection" in _types(node):
                title = _text(node.get("name"))
                if title:
                    steps.append(f"## {title}")
                collect(node.get("itemListElement", []))
            else:
                collect(node.get("text") or node.get("name") or "")

    collect(value)
    if not steps:
        return None
    if len(steps) == 1:
        return steps[0]
    out, n = [], 0
    for step in steps:
        if step.startswith("## "):
            out.append(step[3:].upper())
        else:
            n += 1
            out.append(f"{n}. {step}")
    return "\n".join(out)


_YOUTUBE_ID = re.compile(
    r"(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=|shorts/|v/)|youtu\.be/)([\w-]{11})"
)


def youtube_url(*candidates: str | None) -> str | None:
    for text in candidates:
        if text:
            m = _YOUTUBE_ID.search(text)
            if m:
                return f"https://www.youtube.com/watch?v={m.group(1)}"
    return None


# --- Ingredient lines ---------------------------------------------------------------------

_FRACTIONS = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1 / 3, "⅔": 2 / 3, "⅛": 0.125}
# Written forms → the unit we store
_UNITS = {
    "g": "g", "gr": "g", "grs": "g", "gramo": "g", "gramos": "g",
    "kg": "kg", "kilo": "kg", "kilos": "kg", "kilogramo": "kg", "kilogramos": "kg",
    "ml": "ml", "mililitro": "ml", "mililitros": "ml", "cl": "cl", "dl": "dl",
    "l": "l", "litro": "l", "litros": "l",
    "cucharada": "cucharada", "cucharadas": "cucharada", "cda": "cucharada", "cdas": "cucharada",
    "cucharadita": "cucharadita", "cucharaditas": "cucharadita", "cdta": "cucharadita",
    "cdtas": "cucharadita", "cdita": "cucharadita", "cditas": "cucharadita",
    "taza": "taza", "tazas": "taza", "vaso": "vaso", "vasos": "vaso",
    "diente": "diente", "dientes": "diente", "pizca": "pizca", "pizcas": "pizca",
    "unidad": "unidad", "unidades": "unidad", "ud": "unidad", "uds": "unidad",
    "lata": "lata", "latas": "lata", "sobre": "sobre", "sobres": "sobre",
    "manojo": "manojo", "manojos": "manojo", "rama": "rama", "ramas": "rama",
    "ramita": "rama", "ramitas": "rama", "hoja": "hoja", "hojas": "hoja",
    "rebanada": "rebanada", "rebanadas": "rebanada", "loncha": "loncha", "lonchas": "loncha",
    "chorro": "chorro", "chorrito": "chorro", "puñado": "puñado", "puñados": "puñado",
    "filete": "filete", "filetes": "filete", "pieza": "unidad", "piezas": "unidad",
    "count": "unidad", "cup": "taza", "cups": "taza", "tbsp": "cucharada", "tsp": "cucharadita",
}  # fmt: skip
_NUMBER = r"(\d+\s*[½¼¾⅓⅔⅛]|\d+(?:[.,]\d+)?(?:\s*/\s*\d+)?|[½¼¾⅓⅔⅛])"
_LINE = re.compile(rf"^\s*{_NUMBER}(?:\s*(?:-|a|o)\s*{_NUMBER})?\s*(.*)$", re.I)


def _number(text: str) -> float | None:
    text = text.replace(" ", "")
    if text and text[-1] in _FRACTIONS:
        whole = text[:-1]
        return (float(whole) if whole else 0) + _FRACTIONS[text[-1]]
    if "/" in text:
        num, den = text.split("/")
        return float(num) / float(den) if float(den) else None
    return float(text.replace(",", "."))


@dataclass
class IngredientLine:
    name: str
    quantity: float | None = None
    unit: str | None = None
    raw_text: str | None = None


def parse_ingredient(line: str) -> IngredientLine:
    """'2 dientes de ajo picados' → quantity 2, unit 'diente', name 'ajo'.

    Conservative: when in doubt the whole line stays as the name and raw_text keeps it
    untouched, so the user fixes it in the preview.
    """
    raw = " ".join(line.split())
    rest, quantity, unit = raw, None, None
    m = _LINE.match(raw)
    if m:
        quantity = round(_number(m.group(1)), 2)
        rest = m.group(3)
        first, _, after = rest.partition(" ")
        key = first.lower().rstrip(".")
        if key in _UNITS:
            unit, rest = _UNITS[key], after
    rest = re.sub(r"^(?:de|del)\s+", "", rest.strip(), flags=re.I)
    # Drop comments: "(unos 200 g)", ", picado fino"
    name = re.split(r"\s*[,(;]", rest, maxsplit=1)[0].strip(" .:-")
    return IngredientLine(
        name=(name or raw)[:100], quantity=quantity, unit=unit, raw_text=raw[:200]
    )


# --- The preview --------------------------------------------------------------------------


@dataclass
class RecipePreview:
    title: str
    source_url: str
    source_name: str | None = None
    description: str | None = None
    instructions: str | None = None
    prep_time_minutes: int | None = None
    servings: int | None = None
    cook_name: str | None = None
    youtube_url: str | None = None
    image_url: str | None = None
    ingredients: list[IngredientLine] = field(default_factory=list)
    complete: bool = True  # False when the page had no recipe data (only title/photo)
    from_text: bool = False  # read from the page text (no recipe data): the user should check


def _looks_like_domain(name: str | None) -> bool:
    return bool(name) and " " not in name and "." in name


def _json_ld_site_names(reader: _PageReader) -> list[str]:
    """Names of the WebSite / Organization nodes of the page's JSON-LD."""
    names = []
    for raw in reader.json_ld:
        try:
            data = json.loads(raw.strip())
        except ValueError:
            continue
        for node in _walk(data):
            if _types(node) & {"website", "organization", "newsmediaorganization"}:
                name = _text(node.get("name"))
                if name:
                    names.append(name)
    return names


def _site_name(reader: _PageReader, recipe: dict | None, url: str) -> str:
    """The web's name as people know it ("Directo al Paladar"), not its domain when possible:
    recipe publisher, og:site_name, application-name, the site's JSON-LD, and only then the
    domain."""
    candidates = [
        _name(recipe.get("publisher")) if recipe else None,
        (reader.meta.get("og:site_name") or "").strip(),
        (reader.meta.get("application-name") or "").strip(),
        *_json_ld_site_names(reader),
    ]
    candidates = [c for c in candidates if c]
    for name in candidates:
        if not _looks_like_domain(name):
            return name
    if candidates:
        return candidates[0]
    host = urlparse(url).hostname or ""
    return host.removeprefix("www.")


_ING_HEADING = re.compile(r"^\W*ingredientes\b", re.I)
_STEP_HEADING = re.compile(
    r"^\W*(preparaci[oó]n|elaboraci[oó]n|modo de (preparaci[oó]n|hacerlo)|c[oó]mo (se )?"
    r"(hace|prepara)|pasos|instrucciones|procedimiento)",
    re.I,
)
_NUMBERED = re.compile(r"^\s*(\d{1,2})\s*[.)º°\-–]+\s*")
_SHORT = 90  # a paragraph this short can act as a heading ("INGREDIENTES para 4:")
_MAX_LINES = 60


def _is_heading(block: tuple[str, str, bool]) -> bool:
    kind, text, _ = block
    return kind in _HEADINGS or (kind == "p" and len(text) <= _SHORT)


def _from_text(blocks: list[tuple[str, str, bool]]) -> tuple[list[str], list[str], int | None]:
    """(ingredient lines, steps, servings) from the text of a page without recipe data.

    Ingredients: the list after the first "Ingredientes…" heading (short subheadings such as
    "Para la salsa:" are skipped). Steps: the items after a "Preparación / Elaboración / Cómo se
    hace…" heading; without it, the numbered lines that follow the ingredients.
    """
    start = next(
        (i for i, b in enumerate(blocks) if _is_heading(b) and _ING_HEADING.match(b[1])), None
    )
    if start is None:
        return [], [], None
    servings = None
    m = re.search(r"\bpara\s+(\d+)", blocks[start][1], re.I)
    if m:
        servings = int(m.group(1)) or None

    ingredients: list[str] = []
    i = start + 1
    while i < len(blocks) and len(ingredients) < _MAX_LINES:
        kind, text, _ = blocks[i]
        if kind == "li":
            ingredients.append(text)
        elif _STEP_HEADING.match(text) or kind in _HEADINGS:
            break
        elif kind == "p" and ingredients and not text.endswith(":"):
            break  # the text after the list
        i += 1

    steps: list[str] = []
    step_start = next(
        (j for j in range(i, len(blocks)) if _is_heading(blocks[j])
         and _STEP_HEADING.match(blocks[j][1])),
        None,
    )  # fmt: skip
    if step_start is not None:
        for kind, text, _ in blocks[step_start + 1 :]:
            if kind in _HEADINGS and steps:
                break
            if kind in ("li", "p"):
                steps.append(_NUMBERED.sub("", text))
            if len(steps) >= _MAX_LINES:
                break
    else:
        for kind, text, ordered in blocks[i:]:
            if (kind == "li" and ordered) or _NUMBERED.match(text):
                steps.append(_NUMBERED.sub("", text))
            elif steps and kind in _HEADINGS:
                break
            if len(steps) >= _MAX_LINES:
                break
    return ingredients, [s for s in steps if s], servings


def _clean_title(title: str, site: str | None) -> str:
    """'Serranito - Javi Recetas' → 'Serranito' when the site is Javi Recetas."""
    if site:
        for sep in (" - ", " | ", " – ", " — "):
            suffix = f"{sep}{site}"
            if title.lower().endswith(suffix.lower()):
                return title[: -len(suffix)].strip()
    return title


def read_recipe(html: str, url: str) -> RecipePreview:
    reader = _PageReader()
    reader.feed(html)
    reader.close()
    recipe = _find(reader.json_ld, "recipe")
    iframes = " ".join(reader.iframes)
    if recipe is None:
        title = _text(reader.meta.get("og:title") or reader.title)
        if not title:
            raise NoRecipeFound
        site = _site_name(reader, None, url)
        ingredients, steps, servings = _from_text(reader.blocks)
        found = bool(ingredients)
        return RecipePreview(
            title=_clean_title(title, site)[:200],
            source_url=url,
            source_name=site,
            description=_text(reader.meta.get("og:description") or reader.meta.get("description")),
            instructions=_instructions(steps) if found else None,
            servings=servings if found else None,
            image_url=reader.meta.get("og:image"),
            youtube_url=youtube_url(iframes),
            ingredients=[parse_ingredient(line) for line in ingredients],
            complete=found,
            from_text=found,
        )
    video = recipe.get("video")
    video = video[0] if isinstance(video, list) and video else video
    video_urls = (
        [video.get("embedUrl"), video.get("contentUrl"), video.get("url")]
        if isinstance(video, dict)
        else []
    )
    total = iso_minutes(recipe.get("totalTime"))
    if total is None:
        parts = [iso_minutes(recipe.get("prepTime")), iso_minutes(recipe.get("cookTime"))]
        total = sum(p for p in parts if p) or None
    lines = recipe.get("recipeIngredient") or recipe.get("ingredients") or []
    if isinstance(lines, str):
        lines = [lines]
    return RecipePreview(
        title=(_text(recipe.get("name")) or _text(reader.title) or url)[:200],
        source_url=url,
        source_name=_site_name(reader, recipe, url),
        description=_text(recipe.get("description")),
        instructions=_instructions(recipe.get("recipeInstructions")),
        prep_time_minutes=total,
        servings=_servings(recipe.get("recipeYield")),
        cook_name=(_name(recipe.get("author")) or "")[:100] or None,
        youtube_url=youtube_url(*video_urls, iframes),
        image_url=_image(recipe.get("image")) or reader.meta.get("og:image"),
        ingredients=[parse_ingredient(_text(x) or "") for x in lines if _text(x)],
    )
