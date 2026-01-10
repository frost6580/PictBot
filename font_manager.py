from fontTools.ttLib import TTFont
from fontTools.pens.basePen import BasePen


class FontGlyphManager:
    def __init__(self, font_path):
        self.font = TTFont(font_path)
        self.cmap = self.font["cmap"].getBestCmap()
        self.glyph_set = self.font.getGlyphSet()
        self.units_per_em = self.font["head"].unitsPerEm
        self.ascent = self.font["hhea"].ascent
        self.descent = self.font["hhea"].descent

    class _ListPen(BasePen):
        def __init__(self, glyphSet=None):
            super().__init__(glyphSet)
            self.strokes = []
            self.current_stroke = []

        def _moveTo(self, pt):
            self._start_new_stroke()
            self.current_stroke.append(list(pt))

        def _lineTo(self, pt):
            self.current_stroke.append(list(pt))

        def _qCurveToOne(self, pt1, pt2):
            self.current_stroke.extend([list(pt1), list(pt2)])

        def _closePath(self):
            self._start_new_stroke()

        def _start_new_stroke(self):
            if self.current_stroke:
                self.strokes.append(self.current_stroke)
                self.current_stroke = []

        def get_paths(self):
            self._start_new_stroke()
            return self.strokes

    def get_glyph_vector(self, char, font_size=100):
        glyph_name = self.cmap.get(ord(char))
        if not glyph_name or glyph_name not in self.glyph_set:
            return []

        glyph = self.glyph_set[glyph_name]
        pen = self._ListPen(self.glyph_set)
        glyph.draw(pen)
        paths = pen.get_paths()

        if not paths:
            return []

        scale = font_size / self.units_per_em
        shift_y = self.ascent

        scaled_paths = []
        for path in paths:
            scaled_path = []
            for x, y in path:
                x_scaled = x * scale
                y_scaled = (shift_y - y) * scale
                scaled_path.append([x_scaled, y_scaled])
            scaled_paths.append(scaled_path)

        return scaled_paths
