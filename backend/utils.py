import html
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit

from werkzeug.security import generate_password_hash, check_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return check_password_hash(password_hash, password)


ALLOWED_DOCUMENT_TAGS = {
    "a", "b", "blockquote", "br", "code", "div", "em", "font", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "li", "ol", "p", "pre", "s", "span", "strike",
    "strong", "sub", "sup", "table", "tbody", "td", "th", "thead", "tr", "u", "ul",
}
VOID_DOCUMENT_TAGS = {"br", "hr"}
DROP_CONTENT_TAGS = {"iframe", "object", "script", "style", "svg", "math"}
FONT_SIZES = {"1": "8pt", "2": "10pt", "3": "12pt", "4": "14pt", "5": "18pt", "6": "24pt", "7": "36pt"}


def _safe_document_style(style):
    safe = []
    allowed_names = {"arial", "calibri", "cambria", "georgia", "times new roman", "verdana", "courier new", "monospace", "serif", "sans-serif"}
    colors = {"black", "white", "red", "blue", "green", "yellow", "orange", "purple", "pink", "gray", "grey", "teal", "navy", "maroon"}

    for declaration in (style or "").split(";"):
        if ":" not in declaration:
            continue
        name, value = (part.strip().lower() for part in declaration.split(":", 1))
        if not value or any(token in value for token in ("url(", "expression", "javascript", "@import")):
            continue
        if name in {"color", "background-color"}:
            if re.fullmatch(r"#[0-9a-f]{3,8}", value) or value in colors:
                safe.append(f"{name}:{value}")
        elif name == "font-family":
            family_names = [family.strip().strip("'\"") for family in value.split(",")]
            if family_names and all(family.lower() in allowed_names for family in family_names):
                css_families = [f"'{family}'" if " " in family else family for family in family_names]
                safe.append(f"{name}:{','.join(css_families)}")
        elif name == "font-size" and re.fullmatch(r"(?:[1-9]\d?|1\d\d)(?:pt|px|em|rem|%)", value):
            safe.append(f"{name}:{value}")
        elif name == "font-weight" and value in {"normal", "bold", "400", "500", "600", "700", "800", "900"}:
            safe.append(f"{name}:{value}")
        elif name == "font-style" and value in {"normal", "italic"}:
            safe.append(f"{name}:{value}")
        elif name == "text-align" and value in {"left", "right", "center", "justify"}:
            safe.append(f"{name}:{value}")
        elif name == "text-decoration" and value in {"underline", "line-through", "none"}:
            safe.append(f"{name}:{value}")
        elif name == "vertical-align" and value in {"sub", "super", "baseline"}:
            safe.append(f"{name}:{value}")
        elif name == "line-height" and re.fullmatch(r"[1-3](?:\.\d{1,2})?", value):
            safe.append(f"{name}:{value}")
    return ";".join(safe)


def _safe_document_url(value):
    value = (value or "").strip()
    if not value or any(ord(character) < 32 for character in value):
        return ""
    parsed = urlsplit(value)
    if parsed.scheme.lower() in {"http", "https", "mailto"}:
        return value
    if not parsed.scheme and not value.startswith("//") and (value.startswith(("/", "#", "?")) or not parsed.netloc):
        return value
    return ""


class _DocumentHTMLSanitizer(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.output = []
        self.stack = []
        self.dropped_tag = None
        self.dropped_depth = 0

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if self.dropped_tag:
            if tag == self.dropped_tag:
                self.dropped_depth += 1
            return
        if tag in DROP_CONTENT_TAGS:
            self.dropped_tag = tag
            self.dropped_depth = 1
            return
        if tag not in ALLOWED_DOCUMENT_TAGS:
            return

        output_tag = "span" if tag == "font" else tag
        safe_attrs = []
        styles = []
        for name, value in attrs:
            name = (name or "").lower()
            value = value or ""
            if name == "style":
                styles.append(_safe_document_style(value))
            elif tag == "a" and name == "href":
                safe_url = _safe_document_url(value)
                if safe_url:
                    safe_attrs.append(("href", safe_url))
            elif name == "title":
                safe_attrs.append(("title", value[:200]))
            elif tag in {"td", "th"} and name in {"colspan", "rowspan"} and value.isdigit() and 1 <= int(value) <= 20:
                safe_attrs.append((name, value))
            elif tag == "font" and name == "color" and (re.fullmatch(r"#[0-9a-fA-F]{3,8}", value) or value.lower() in {"black", "white", "red", "blue", "green", "yellow", "orange", "purple", "pink", "gray", "grey"}):
                styles.append(f"color:{value}")
            elif tag == "font" and name == "face":
                family = value.strip().strip("'\"")
                if family.lower() in {"arial", "calibri", "cambria", "georgia", "times new roman", "verdana", "courier new"}:
                    styles.append(f"font-family:{family}")
            elif tag == "font" and name == "size" and value in FONT_SIZES:
                styles.append(f"font-size:{FONT_SIZES[value]}")

        safe_style = _safe_document_style(";".join(style for style in styles if style))
        if safe_style:
            safe_attrs.append(("style", safe_style))
        attributes = "".join(f' {name}="{html.escape(value, quote=True)}"' for name, value in safe_attrs)
        self.output.append(f"<{output_tag}{attributes}>")
        if tag not in VOID_DOCUMENT_TAGS:
            self.stack.append((tag, output_tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag.lower() not in VOID_DOCUMENT_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.dropped_tag:
            if tag == self.dropped_tag:
                self.dropped_depth -= 1
                if self.dropped_depth <= 0:
                    self.dropped_tag = None
                    self.dropped_depth = 0
            return
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                while len(self.stack) > index:
                    _, output_tag = self.stack.pop()
                    self.output.append(f"</{output_tag}>")
                break

    def handle_data(self, data):
        if not self.dropped_tag:
            self.output.append(html.escape(data, quote=False).replace("\n", "<br>"))

    def handle_comment(self, _data):
        return

    def finish(self):
        while self.stack:
            _, output_tag = self.stack.pop()
            self.output.append(f"</{output_tag}>")
        return "".join(self.output)


def sanitize_document_html(content: str) -> str:
    """Keep safe rich-text markup while stripping scripts and unsafe attributes."""
    if not isinstance(content, str):
        raise TypeError("Document content must be text.")
    parser = _DocumentHTMLSanitizer()
    parser.feed(content)
    parser.close()
    return parser.finish()
