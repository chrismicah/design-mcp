"""Source-level design findings with locations. Geometry requires a rendered DOM."""

from colorsys import rgb_to_hsv
from dataclasses import dataclass, field
from html.parser import HTMLParser
import re


@dataclass
class Element:
    tag: str
    line: int
    attrs: dict[str, str]
    children: list["Element"] = field(default_factory=list)
    text: list[str] = field(default_factory=list)

    @property
    def content(self) -> str:
        return " ".join([*self.text, *(child.content for child in self.children)]).strip()


class _Markup(HTMLParser):
    _void = frozenset("area base br col embed hr img input link meta param source track wbr".split())

    def __init__(self, code: str):
        super().__init__()
        self.stack = []
        self.nodes = []
        self.feed(code)
        self.close()

    def handle_starttag(self, tag, attrs):
        node = Element(tag, self.getpos()[0], {key: value or "" for key, value in attrs})
        self.nodes.append(node)
        if self.stack:
            self.stack[-1].children.append(node)
        if tag not in self._void:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self._void:
            self.stack.pop()

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                break

    def handle_data(self, data):
        if self.stack:
            self.stack[-1].text.append(data)


_FAMILIES = {"inter", "roboto", "space grotesk", "system-ui"}
_FONT_DECLARATION = re.compile(r"(?<![\w-])font-family\s*:\s*([^;{}\n]+)", re.I)
_FONT_SHORTHAND = re.compile(r"(?<![\w-])font\s*:\s*[^;{}\n]*?\d+(?:\.\d+)?(?:px|rem|em|pt|%)(?:/[^\s;]+)?\s+([^;{}\n]+)", re.I)
_TAILWIND_FONT = re.compile(r"\bfont-\[([^\]]+)\]", re.I)
_JSX_FONT = re.compile(r"""\bfontFamily\s*:\s*(['"])([^'"]+)\1""", re.I)
_PROMO = re.compile(r"\b(get started|elevate your|seamless|supercharge|unlock (?:your|the))\b", re.I)
_RISKY_BLUE = re.compile(r"^(?:#3b82f6|#2563eb)$", re.I)
_COLOR = re.compile(r"#[a-f0-9]{3,8}\b|rgba?\([^()]+\)|hsla?\([^()]+\)|\b(?:purple|violet|indigo|blue)\b", re.I)
_VAR = re.compile(r"^var\(\s*(--[\w-]+)")
_EMOJI = re.compile(r"^[\U0001F300-\U0001FAFF\u2600-\u27bf]")
_CSS_COMMENT = re.compile(r"/\*.*?\*/|<!--.*?-->", re.S)
_HERO_EYEBROW = re.compile(r"\b(?:eyebrow|uppercase)\b")


def _blank_match(match):
    return "".join("\n" if char == "\n" else " " for char in match.group())


def _primary_family(value, variables):
    seen = set()
    while (variable := _VAR.match(value.strip())) is not None:
        name = variable[1]
        if name in seen or name not in variables:
            return ""
        seen.add(name)
        value = variables[name]
    return value.split(",", 1)[0].strip(" \'\"").replace("_", " ").casefold()


def _gradient_hues(value):
    named = {"purple": 280, "violet": 280, "indigo": 270, "blue": 240}
    for token in _COLOR.findall(value):
        token = token.lower()
        if token in named:
            yield named[token]
        elif token.startswith("hsl"):
            number = re.search(r"-?\d+(?:\.\d+)?", token)
            if number:
                yield float(number[0]) % 360
        else:
            if token.startswith("#"):
                digits = token[1:]
                if len(digits) in (3, 4):
                    digits = "".join(char * 2 for char in digits)
                if len(digits) not in (6, 8):
                    continue
                rgb = [int(digits[index:index + 2], 16) / 255 for index in (0, 2, 4)]
            else:
                components = re.findall(r"([\d.]+)(%?)", token)[:3]
                if len(components) != 3:
                    continue
                rgb = [float(number) / (100 if percent else 255) for number, percent in components]
            hue, saturation, brightness = rgb_to_hsv(*rgb)
            if saturation > .22 and brightness > .2:
                yield hue * 360


def inspect_design(code: str) -> list[dict]:
    """Find recognizable source patterns. An empty list does not certify rendered design."""
    source = _CSS_COMMENT.sub(_blank_match, code)
    markup = _Markup(source)
    findings = {}

    def flag(rule, line, detail):
        findings.setdefault((line, rule), {"rule": rule, "line": line, "detail": detail})

    styles = [node for node in markup.nodes if node.tag == "style"]
    style_text = "\n".join("".join(node.text) for node in styles) if styles else source
    variables = {key: val for key, val in re.findall(r"(--[\w-]+)\s*:\s*([^;{}\n]+)", style_text)}

    def font_flag(value, line):
        family = _primary_family(value, variables)
        if family in _FAMILIES:
            display = {"inter": "Inter", "roboto": "Roboto", "space grotesk": "Space Grotesk"}.get(family, family)
            flag("brand-font", line, f"Primary font uses {display}.")

    def css_flags(css, line):
        for expression in (_FONT_DECLARATION, _FONT_SHORTHAND, _TAILWIND_FONT):
            for match in expression.finditer(css):
                font_flag(match[1], line + css.count("\n", 0, match.start()))
        for gradient in re.finditer(r"[^;{}\n]*gradient[^;{}\n]*", css, re.I):
            hues = tuple(_gradient_hues(gradient[0]))
            if any(248 < hue <= 320 for hue in hues) and any(190 <= hue <= 248 for hue in hues):
                flag("purple-blue-gradient", line + css.count("\n", 0, gradient.start()), "Purple and blue are paired in one gradient.")
        for match in re.finditer(r"\b(?:nav|\.navbar)\b[^{}]*\{[^{}]*(?:backdrop-filter\s*:\s*blur|backdrop-blur)", css, re.I):
            flag("glass-nav", line + css.count("\n", 0, match.start()), "Navigation uses a blurred background.")
        for rule in re.finditer(r"(?:^|(?<=[{}]))([^{}]*)\{([^{}]+)\}", css):
            body = rule[2]
            if re.search(r"border-radius\s*:\s*(?:16px|1rem)\b", body) and re.search(r"box-shadow\s*:\s*(?!none\b)\S", body):
                flag("rounded-shadow", line + css.count("\n", 0, rule.start(2)), "One selector pairs a 16 px rounding with a shadow.")
            if re.search(r"background(?:-color)?\s*:\s*#(?:3b82f6|2563eb)\b", body, re.I) and re.search(r"\b(?:button|btn|cta)\b", rule[1], re.I):
                flag("startup-blue", line + css.count("\n", 0, rule.start(2)), "A button or CTA selector uses a default saturated blue.")
            if re.search(r"animation(?:-name)?\s*:[^;]*(?:fade[_-]?up|fade[_-]?in[_-]?up)", body, re.I) and re.search(r"(?:\*|section|\.fade)", rule[1], re.I):
                flag("default-fade-up", line + css.count("\n", 0, rule.start(2)), "A broad selector applies reusable fade-up motion.")

    if not markup.nodes:
        css_flags(source, 1)
    for style in styles:
        css_flags("".join(style.text), style.line)
    for match in _JSX_FONT.finditer(source):
        font_flag(match[2], 1 + source.count("\n", 0, match.start()))
    for node in markup.nodes:
        attrs = node.attrs
        classes = attrs.get("class", attrs.get("classname", ""))
        style = attrs.get("style", "")
        if classes or style:
            css_flags(classes + " " + style, node.line)
        if node.tag in ("button", "a") or attrs.get("role") == "button":
            if _PROMO.search(node.content):
                flag("generic-cta", node.line, "An action label uses generic promotional copy.")
            if node.content.endswith("!"):
                flag("exclamation-cta", node.line, "An action label ends with an exclamation mark.")
            if re.search(r"\bbg-blue-(?:500|600)\b", classes) or _RISKY_BLUE.match(style.partition(":")[-1].strip(" ;")):
                flag("startup-blue", node.line, "A CTA uses a default saturated blue.")
        if node.tag in ("h1", "h2", "h3", "p") and _PROMO.search(node.content) and node.content.lower() != "get started":
            flag("generic-copy", node.line, "Visible copy opens with a generic promotional phrase.")
        if node.tag == "li" and _EMOJI.match(node.content):
            flag("emoji-bullet", node.line, "List text starts with a decorative emoji.")
        if node.tag == "nav" and re.search(r"backdrop-(?:filter|blur)|backdrop-filter\s*:\s*blur", classes + " " + style, re.I):
            flag("glass-nav", node.line, "Navigation uses a blurred background.")
        if re.search(r"(?:^|\s)rounded-2xl\b", classes) and re.search(r"\bshadow(?:-(?:sm|md|lg|xl|2xl))?\b", classes):
            flag("rounded-shadow", node.line, "A 16 px rounded surface includes a shadow.")
        if re.search(r"\bgrid-cols-[346]\b", classes) and len(node.children) in (3, 4, 6):
            peers = [(child.tag, child.attrs.get("class", "")) for child in node.children]
            if len(set(peers)) == 1 and re.search(r"\b(?:card|rounded)\b", peers[0][1], re.I):
                flag("symmetric-cards", node.line, "Repeated same-style card wrappers form a static grid candidate.")
        if (node.tag in ("header", "section", "div") and ("text-center" in classes or "text-align:center" in style.replace(" ", ""))):
            children = node.children
            eyebrow = any(_HERO_EYEBROW.search(child.attrs.get("class", "")) or
                          (2 <= len(child.content) <= 45 and child.content.isupper())
                          for child in children if child.tag in ("span", "p", "small", "div"))
            headings = any(child.tag == "h1" for child in children)
            buttons = sum(child.tag in ("a", "button") for child in children)
            buttons += sum(grandchild.tag in ("a", "button") for child in children if child.tag == "div" for grandchild in child.children)
            if eyebrow and headings and buttons >= 2 and any(child.tag == "p" for child in children):
                flag("centered-hero", node.line, "Centered hero combines an eyebrow, heading, copy, and two actions.")
    return [findings[key] for key in sorted(findings)]
