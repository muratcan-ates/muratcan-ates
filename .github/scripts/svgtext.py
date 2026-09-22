"""Turn text into SVG path data with the vendored Geist font.

GitHub serves README images through its image proxy, so an SVG cannot load
web fonts. Outlining the text keeps the cards identical on every platform.
"""

from functools import lru_cache
from pathlib import Path

from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

FONT_PATH = Path(__file__).resolve().parent.parent / "fonts" / "Geist-Regular.ttf"


def _num(value):
    text = f"{value:.1f}"
    return text[:-2] if text.endswith(".0") else text


class Font:
    def __init__(self, path=FONT_PATH):
        self.font = TTFont(path)
        self.glyphs = self.font.getGlyphSet()
        self.cmap = self.font.getBestCmap()
        self.upm = self.font["head"].unitsPerEm
        self.cap_height = self.font["OS/2"].sCapHeight
        self._pairs = self._read_kerning()

    def _read_kerning(self):
        """Collect pair adjustments from the GPOS 'kern' feature."""
        pairs = {}
        if "GPOS" not in self.font:
            return pairs
        table = self.font["GPOS"].table
        lookup_ids = set()
        for record in table.FeatureList.FeatureRecord:
            if record.FeatureTag == "kern":
                lookup_ids.update(record.Feature.LookupListIndex)
        for index in sorted(lookup_ids):
            lookup = table.LookupList.Lookup[index]
            for sub in lookup.SubTable:
                if lookup.LookupType == 9:
                    sub = sub.ExtSubTable
                if getattr(sub, "LookupType", 2) != 2:
                    continue
                if sub.Format == 1:
                    for first, pair_set in zip(sub.Coverage.glyphs, sub.PairSet):
                        for rec in pair_set.PairValueRecord:
                            value = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                            if value:
                                pairs.setdefault((first, rec.SecondGlyph), value)
                elif sub.Format == 2:
                    class1 = sub.ClassDef1.classDefs
                    class2 = sub.ClassDef2.classDefs
                    firsts = sub.Coverage.glyphs
                    seconds = {}
                    for glyph, cls in class2.items():
                        seconds.setdefault(cls, []).append(glyph)
                    for first in firsts:
                        row = sub.Class1Record[class1.get(first, 0)]
                        for cls, rec in enumerate(row.Class2Record):
                            value = getattr(rec.Value1, "XAdvance", 0) if rec.Value1 else 0
                            if not value:
                                continue
                            for second in seconds.get(cls, []):
                                pairs.setdefault((first, second), value)
        return pairs

    def glyph_name(self, char):
        return self.cmap.get(ord(char)) or self.cmap.get(ord("?"))

    def width(self, text, size, tracking=0.0):
        return self._layout(text, size, tracking)[1]

    def _layout(self, text, size, tracking):
        scale = size / self.upm
        placed = []
        cursor = 0.0
        previous = None
        for char in text:
            name = self.glyph_name(char)
            if previous is not None:
                cursor += self._pairs.get((previous, name), 0) * scale + tracking
            placed.append((name, cursor))
            cursor += self.glyphs[name].width * scale
            previous = name
        return placed, cursor

    def path(self, text, x, y, size, tracking=0.0, anchor="start"):
        """Return SVG path data for text whose baseline starts at (x, y)."""
        placed, total = self._layout(text, size, tracking)
        if anchor == "middle":
            x -= total / 2
        elif anchor == "end":
            x -= total
        scale = size / self.upm
        pen = SVGPathPen(self.glyphs, ntos=_num)
        for name, offset in placed:
            glyph = self.glyphs[name]
            glyph.draw(TransformPen(pen, (scale, 0, 0, -scale, x + offset, y)))
        return pen.getCommands()


@lru_cache(maxsize=1)
def geist():
    return Font()


def text(content, x, y, size, fill, tracking=0.0, anchor="start", opacity=None, extra=""):
    """Outlined text as a <path> element."""
    d = geist().path(content, x, y, size, tracking, anchor)
    if not d:
        return ""
    attrs = f' fill-opacity="{opacity}"' if opacity is not None else ""
    return f'<path d="{d}" fill="{fill}"{attrs}{extra}/>'


def label(content, x, y, size, fill, tracking=None, anchor="start", opacity=None):
    """Small uppercase label with wide tracking."""
    spacing = size * 0.14 if tracking is None else tracking
    return text(content.upper(), x, y, size, fill, spacing, anchor, opacity)


def text_width(content, size, tracking=0.0):
    return geist().width(content, size, tracking)
