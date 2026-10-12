from PIL import Image, ImageDraw, ImageOps
import random
import math


class ImageGenerator:
    """Renders stylised plant illustrations for each growth stage.

    Images are drawn at 2x and downsampled, which gives smooth anti-aliased edges.
    """

    SUPERSAMPLE = 2

    def __init__(self):
        self.image_size = (400, 300)
        self.plant_colors = {
            'tomato': {'stem': '#3f7d3a', 'leaf': '#4caf50', 'fruit': '#e5533d'},
            'basil': {'stem': '#3f7d3a', 'leaf': '#7cc96b', 'fruit': None},
            'mint': {'stem': '#3f7d3a', 'leaf': '#8fd694', 'fruit': None},
            'lettuce': {'stem': '#5b9a3c', 'leaf': '#a5d65a', 'fruit': None},
            'rosemary': {'stem': '#7a5a3a', 'leaf': '#5f7f4f', 'fruit': None},
            'strawberry': {'stem': '#3f7d3a', 'leaf': '#4caf50', 'fruit': '#e0245e'}
        }
        self.sky_top = (226, 242, 234)
        self.sky_bottom = (247, 250, 248)

    def generate_evolution(self, plant_type, prediction, stages=5):
        """Return a list of dicts {image, day, height} sampled across the growth curve"""
        growth = prediction['growth_stages']
        if not growth:
            return []

        max_height = prediction.get('max_height', 150)
        last = len(growth) - 1
        days = [round(i * last / (stages - 1)) for i in range(stages)]

        frames = []
        for i, day in enumerate(days):
            height = growth[day]
            image = self.generate_plant_image(plant_type, height, prediction['health_score'],
                                              i + 1, max_height=max_height, seed=day)
            frames.append({'image': image, 'day': day + 1, 'height': height})
        return frames

    def generate_plant_image(self, plant_type, height, health_score, stage,
                             max_height=150, seed=0):
        """Generate a single plant image. Stage 0 is a freshly sprouted seed."""
        rng = random.Random(seed)
        s = self.SUPERSAMPLE
        w, h = self.image_size[0] * s, self.image_size[1] * s

        img = self._background(w, h)
        draw = ImageDraw.Draw(img)

        colors = self.plant_colors.get(plant_type, self.plant_colors['tomato'])
        health = max(0.0, min(1.0, health_score / 100.0))
        stem_color = self._health_tint(colors['stem'], health)
        leaf_color = self._health_tint(colors['leaf'], health)

        cx = w // 2
        pot_top = h - 84 * s
        soil_y = pot_top + 6 * s

        if stage == 0:
            self._draw_sprout(draw, cx, soil_y, leaf_color, s)
        else:
            available = pot_top - 24 * s
            plant_h = max(34 * s, available * min(1.0, height / max_height))
            top_y = soil_y - plant_h
            self._draw_stem(draw, cx, soil_y, top_y, stem_color, plant_h, s)
            self._draw_leaves(draw, plant_type, cx, soil_y, top_y, plant_h, leaf_color, stage, s)
            if colors['fruit'] and stage >= 4:
                self._draw_fruits(draw, plant_type, cx, soil_y, top_y, plant_h,
                                  colors['fruit'], stage, rng, s)

        self._draw_pot(draw, cx, pot_top, h, s)
        return img.resize(self.image_size, Image.Resampling.LANCZOS)

    def photo_thumbnail(self, path):
        """Load a user photo and crop it to the standard image size"""
        with Image.open(path) as photo:
            photo = ImageOps.exif_transpose(photo).convert('RGB')
            return ImageOps.fit(photo, self.image_size, Image.Resampling.LANCZOS)

    # Drawing helpers

    def _background(self, w, h):
        img = Image.new('RGB', (w, h))
        draw = ImageDraw.Draw(img)
        for y in range(h):
            t = y / h
            color = tuple(int(a + (b - a) * t) for a, b in zip(self.sky_top, self.sky_bottom))
            draw.line([(0, y), (w, y)], fill=color)
        return img

    def _draw_pot(self, draw, cx, top, h, s):
        rim_w, base_w = 72 * s, 54 * s
        bottom = h - 14 * s
        # Ground shadow
        draw.ellipse([cx - base_w - 10 * s, bottom - 4 * s, cx + base_w + 10 * s, bottom + 8 * s],
                     fill='#dfe7e2')
        draw.polygon([(cx - rim_w + 8 * s, top + 14 * s), (cx + rim_w - 8 * s, top + 14 * s),
                      (cx + base_w, bottom), (cx - base_w, bottom)], fill='#c8694a')
        draw.rounded_rectangle([cx - rim_w, top, cx + rim_w, top + 18 * s],
                               radius=6 * s, fill='#d97a58')
        # Soil
        draw.ellipse([cx - rim_w + 6 * s, top - 4 * s, cx + rim_w - 6 * s, top + 10 * s],
                     fill='#5a3d2b')

    def _draw_sprout(self, draw, x, y, color, s):
        draw.ellipse([x - 9 * s, y - 6 * s, x + 9 * s, y + 4 * s], fill='#8a5a3b')
        draw.line([x, y - 2 * s, x, y - 26 * s], fill='#4f8a3f', width=3 * s)
        self._leaf(draw, x - 11 * s, y - 28 * s, 22 * s, 9 * s, -25, color)
        self._leaf(draw, x + 11 * s, y - 28 * s, 22 * s, 9 * s, 25, color)

    def _stem_x(self, cx, t, plant_h):
        """Gentle S-curve for the stem; t is 0 at the soil and 1 at the tip"""
        return cx + math.sin(t * math.pi * 1.5) * plant_h * 0.04

    def _draw_stem(self, draw, cx, base_y, top_y, color, plant_h, s):
        width = max(3 * s, int(plant_h * 0.035))
        points = []
        for i in range(21):
            t = i / 20
            points.append((self._stem_x(cx, t, plant_h), base_y - t * (base_y - top_y)))
        draw.line(points, fill=color, width=width, joint='curve')

    def _draw_leaves(self, draw, plant_type, cx, base_y, top_y, plant_h, color, stage, s):
        num_leaves = min(2 + stage * 2, 12)
        for i in range(num_leaves):
            t = (i + 1) / (num_leaves + 1)
            y = base_y - t * plant_h
            x = self._stem_x(cx, t, plant_h)
            side = 1 if i % 2 == 0 else -1
            # Lower leaves are larger
            size = max(14 * s, plant_h * 0.22 * (1.15 - t * 0.5))
            if plant_type == 'rosemary':
                self._leaf(draw, x + side * size * 0.35, y, size * 0.7, size * 0.12, side * 35, color)
            elif plant_type == 'lettuce':
                self._leaf(draw, x + side * size * 0.4, y, size, size * 0.6, side * 20, color)
            else:
                self._leaf(draw, x + side * size * 0.45, y, size, size * 0.38, side * 22, color)
        # Crown at the tip
        tip_x = self._stem_x(cx, 1.0, plant_h)
        crown = max(10 * s, plant_h * 0.08)
        self._leaf(draw, tip_x - crown * 0.4, top_y + 2 * s, crown, crown * 0.45, -40, color)
        self._leaf(draw, tip_x + crown * 0.4, top_y + 2 * s, crown, crown * 0.45, 40, color)

    def _leaf(self, draw, x, y, length, width, angle_deg, color):
        """Draw a rotated pointed-ellipse leaf centred on (x, y)"""
        a = math.radians(angle_deg)
        pts = []
        for i in range(24):
            th = 2 * math.pi * i / 24
            px = math.cos(th) * length / 2
            py = math.sin(th) * width / 2 * (1 - 0.35 * abs(math.cos(th)))
            pts.append((x + px * math.cos(a) - py * math.sin(a),
                        y + px * math.sin(a) + py * math.cos(a)))
        draw.polygon(pts, fill=color)
        vein = self._shade(color, 0.8)
        draw.line([(x - length / 2 * math.cos(a) * 0.8, y - length / 2 * math.sin(a) * 0.8),
                   (x + length / 2 * math.cos(a) * 0.8, y + length / 2 * math.sin(a) * 0.8)],
                  fill=vein, width=max(1, int(width / 10)))

    def _draw_fruits(self, draw, plant_type, cx, base_y, top_y, plant_h, color, stage, rng, s):
        count = 2 if stage == 4 else 4
        for _ in range(count):
            t = rng.uniform(0.25, 0.7)
            x = self._stem_x(cx, t, plant_h) + rng.choice((-1, 1)) * rng.uniform(10, 28) * s
            y = base_y - t * plant_h
            r = (7 + stage) * s if plant_type == 'tomato' else 6 * s
            if plant_type == 'strawberry':
                draw.polygon([(x - r, y - r * 0.4), (x + r, y - r * 0.4), (x, y + r * 1.3)], fill=color)
                draw.ellipse([x - r, y - r, x + r, y + r * 0.3], fill=color)
            else:
                draw.ellipse([x - r, y - r, x + r, y + r], fill=color)
                draw.ellipse([x - r * 0.5, y - r * 0.6, x - r * 0.1, y - r * 0.2], fill='#f59a86')
            draw.polygon([(x - r * 0.5, y - r * 0.9), (x, y - r * 1.25), (x + r * 0.5, y - r * 0.9)],
                         fill='#3f7d3a')

    def _health_tint(self, color_hex, health):
        """Blend toward a dry yellow-brown as health drops"""
        r, g, b = self._rgb(color_hex)
        dry = (176, 150, 80)
        k = (1 - health) * 0.85
        return '#%02x%02x%02x' % tuple(int(c + (d - c) * k) for c, d in zip((r, g, b), dry))

    def _shade(self, color_hex, factor):
        return '#%02x%02x%02x' % tuple(int(c * factor) for c in self._rgb(color_hex))

    @staticmethod
    def _rgb(color_hex):
        color_hex = color_hex.lstrip('#')
        return tuple(int(color_hex[i:i + 2], 16) for i in (0, 2, 4))

    def save_evolution_sequence(self, images, filename):
        """Save evolution images as separate files"""
        if images:
            try:
                base_name = filename.rsplit('.', 1)[0]
                for i, image in enumerate(images):
                    image.save(f"{base_name}_stage_{i+1}.png")
                return True
            except Exception as e:
                print(f"Error saving images: {e}")
                return False
        return False
