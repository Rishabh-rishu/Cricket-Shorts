"""
Cricket Raaz - Countdown Graphics Engine
Generates brand-aligned, broadcast-quality 1080x1920 transparent overlays:
- Brand Palette: Midnight Navy (#101B32), Gold (#E8B84A), White (#FFFFFF), Accent Red (#E63946)
- Massive animated countdown numbers (5, 4, 3, 2, 1)
- Clean lower-third player/stat cards (y=1300..1460, leaving center 100% transparent for moving footage)
- Flawless Devanagari typography using PIL with RAQM layout engine
"""

import os
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from visuals.player_asset_provider import PlayerAssetProvider


class CountdownGraphicsEngine:
    W = 1080
    H = 1920

    # Official Brand Palette
    COLOR_NAVY_SOLID = (16, 27, 50)
    COLOR_NAVY_GLASS = (16, 27, 50, 215) # 84% opacity frosted glass
    COLOR_NAVY_LIGHT = (26, 42, 74, 230)
    COLOR_GOLD = (232, 184, 74)
    COLOR_WHITE = (255, 255, 255)
    COLOR_RED = (230, 57, 70)
    COLOR_MUTED_GOLD = (200, 155, 50)

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        return PlayerAssetProvider.get_font(size, "bold" if bold else "regular")

    @classmethod
    def _draw_vignette(cls, draw: ImageDraw.ImageDraw):
        """Draws top and bottom subtle contrast gradients so overlays and subtitles pop."""
        for y in range(0, 220):
            alpha = int(140 * (1.0 - y / 220.0))
            draw.line([(0, y), (cls.W, y)], fill=(10, 16, 30, alpha))
        for y in range(cls.H - 280, cls.H):
            alpha = int(170 * ((y - (cls.H - 280)) / 280.0))
            draw.line([(0, y), (cls.W, y)], fill=(10, 16, 30, alpha))

    @classmethod
    def _draw_header_badge(cls, draw: ImageDraw.ImageDraw, tag: str = "CRICKET RAAZ"):
        """Draws the official Cricket Raaz top floating badge."""
        f_badge = cls.get_font(24, bold=True)
        text = f"🏏  {tag.upper()}"
        bbox = draw.textbbox((0, 0), text, font=f_badge)
        tw = (bbox[2] - bbox[0]) + 48
        th = 48
        tx1 = (cls.W - tw) // 2
        ty1 = 80
        draw.rounded_rectangle(
            [tx1, ty1, tx1 + tw, ty1 + th],
            radius=14,
            fill=cls.COLOR_NAVY_GLASS,
            outline=cls.COLOR_GOLD,
            width=2
        )
        draw.text((tx1 + 24, ty1 + 10), text, font=f_badge, fill=cls.COLOR_GOLD)

    @classmethod
    def render_hook_overlay(
        cls,
        title: str,
        subtitle: str,
        output_path: str
    ) -> str:
        """
        Creates dramatic opening hook overlay with bold gold typography.
        Center remains transparent for moving stadium/cricket footage.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cls._draw_vignette(draw)
        cls._draw_header_badge(draw, "CRICKET RAAZ EXCLUSIVE")

        # Hook Hero Card (y = 200 to 450)
        card_w = 940
        card_h = 240
        cx1 = (cls.W - card_w) // 2
        cy1 = 200
        draw.rounded_rectangle(
            [cx1, cy1, cx1 + card_w, cy1 + card_h],
            radius=24,
            fill=cls.COLOR_NAVY_GLASS,
            outline=cls.COLOR_GOLD,
            width=3
        )
        # Left red accent border
        draw.rounded_rectangle([cx1, cy1, cx1 + 12, cy1 + card_h], radius=6, fill=cls.COLOR_RED)

        # Main Title (Top 5 Rarest Records)
        f_top5 = cls.get_font(32, bold=True)
        f_main = cls.get_font(52, bold=True)
        f_sub = cls.get_font(30, bold=False)

        draw.text((cx1 + 45, cy1 + 25), "TOP 5 COUNTDOWN", font=f_top5, fill=cls.COLOR_RED)
        draw.text((cx1 + 45, cy1 + 75), title, font=f_main, fill=cls.COLOR_GOLD)
        draw.text((cx1 + 45, cy1 + 155), subtitle, font=f_sub, fill=cls.COLOR_WHITE)

        img.save(output_path, "PNG")
        return output_path

    @classmethod
    def render_countdown_overlay(
        cls,
        number: int,
        player_or_team: str,
        record_title: str,
        key_stat: str,
        output_path: str
    ) -> str:
        """
        Renders countdown segment overlay:
        - Massive animated Gold metallic number (5, 4, 3, 2, 1) in top left
        - Semi-transparent lower third card with player name and key statistic
        - 100% transparent middle so moving cricket footage is showcased
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cls._draw_vignette(draw)
        cls._draw_header_badge(draw, "CRICKET RAAZ")

        # 1. Massive Countdown Number Badge (y = 170 to 380)
        num_str = str(number)
        num_box_w = 340
        num_box_h = 160
        nx1 = 60
        ny1 = 170

        # Badge container
        draw.rounded_rectangle(
            [nx1, ny1, nx1 + num_box_w, ny1 + num_box_h],
            radius=20,
            fill=cls.COLOR_NAVY_GLASS,
            outline=cls.COLOR_GOLD,
            width=3
        )
        # Gold accent bar on left
        draw.rounded_rectangle([nx1, ny1, nx1 + 10, ny1 + num_box_h], radius=5, fill=cls.COLOR_RED if number == 1 else cls.COLOR_GOLD)

        # Big Gold Number
        f_num = cls.get_font(120, bold=True)
        # Shadow
        draw.text((nx1 + 35, ny1 + 5), num_str, font=f_num, fill=(10, 15, 25, 240))
        # Gold number
        draw.text((nx1 + 30, ny1), num_str, font=f_num, fill=cls.COLOR_GOLD)

        # Label next to number: "NUMBER 5" / "NUMBER 1"
        f_lbl_small = cls.get_font(20, bold=True)
        f_lbl_big = cls.get_font(32, bold=True)
        lx = nx1 + 140
        draw.text((lx, ny1 + 35), "COUNTDOWN", font=f_lbl_small, fill=cls.COLOR_RED if number == 1 else cls.COLOR_WHITE)
        draw.text((lx, ny1 + 65), f"NUMBER {number}", font=f_lbl_big, fill=cls.COLOR_GOLD)

        # Special badge for Number 1 (Suspense Climax)
        if number == 1:
            pill_w = 280
            px1 = cls.W - pill_w - 60
            py1 = 190
            draw.rounded_rectangle([px1, py1, px1 + pill_w, py1 + 45], radius=12, fill=cls.COLOR_RED, outline=cls.COLOR_GOLD, width=2)
            f_climax = cls.get_font(20, bold=True)
            draw.text((px1 + 25, py1 + 11), "🔥 ULTIMATE RECORD", font=f_climax, fill=cls.COLOR_WHITE)

        # 2. Lower-Third Player & Record Card (y = 1260 to 1440)
        card_w = 960
        card_h = 180
        cx1 = (cls.W - card_w) // 2
        cy1 = 1260

        draw.rounded_rectangle(
            [cx1, cy1, cx1 + card_w, cy1 + card_h],
            radius=20,
            fill=cls.COLOR_NAVY_GLASS,
            outline=cls.COLOR_NAVY_LIGHT,
            width=2
        )
        # Left accent vertical strip (Red for #1, Gold for others)
        draw.rounded_rectangle([cx1, cy1, cx1 + 10, cy1 + card_h], radius=5, fill=cls.COLOR_RED if number == 1 else cls.COLOR_GOLD)

        # Player / Team Name (Line 1)
        f_player = cls.get_font(34, bold=True)
        draw.text((cx1 + 35, cy1 + 22), player_or_team.upper(), font=f_player, fill=cls.COLOR_WHITE)

        # Record Description (Line 2)
        f_rec = cls.get_font(26, bold=False)
        draw.text((cx1 + 35, cy1 + 72), record_title, font=f_rec, fill=(220, 230, 245))

        # Stat Metric Pill (Line 3, Gold Pill)
        stat_text = f"★  {key_stat.upper()}"
        f_stat = cls.get_font(22, bold=True)
        s_bbox = draw.textbbox((0, 0), stat_text, font=f_stat)
        sw = (s_bbox[2] - s_bbox[0]) + 36
        sh = 38
        sx1 = cx1 + 35
        sy1 = cy1 + 118
        draw.rounded_rectangle([sx1, sy1, sx1 + sw, sy1 + sh], radius=8, fill=(26, 42, 74, 255), outline=cls.COLOR_GOLD, width=1)
        draw.text((sx1 + 18, sy1 + 8), stat_text, font=f_stat, fill=cls.COLOR_GOLD)

        img.save(output_path, "PNG")
        return output_path

    @classmethod
    def render_outro_overlay(cls, output_path: str) -> str:
        """
        Creates clean YouTube Shorts outro CTA card:
        - Question prompt
        - Brand identity: Cricket Raaz – Beyond The Boundary
        - LIKE | SHARE | SUBSCRIBE
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        cls._draw_vignette(draw)
        cls._draw_header_badge(draw, "CRICKET RAAZ")

        # CTA Center Card (y = 550 to 900)
        card_w = 960
        card_h = 360
        cx1 = (cls.W - card_w) // 2
        cy1 = 600

        draw.rounded_rectangle(
            [cx1, cy1, cx1 + card_w, cy1 + card_h],
            radius=26,
            fill=cls.COLOR_NAVY_GLASS,
            outline=cls.COLOR_GOLD,
            width=3
        )
        draw.rounded_rectangle([cx1, cy1, cx1 + 12, cy1 + card_h], radius=6, fill=cls.COLOR_RED)

        f_q = cls.get_font(34, bold=True)
        f_brand = cls.get_font(42, bold=True)
        f_sub = cls.get_font(26, bold=False)
        f_cta = cls.get_font(32, bold=True)

        draw.text((cx1 + 45, cy1 + 35), "आपकी क्या राय है? कमेंट्स में बताएं!", font=f_q, fill=cls.COLOR_WHITE)
        draw.text((cx1 + 45, cy1 + 105), "CRICKET RAAZ", font=f_brand, fill=cls.COLOR_GOLD)
        draw.text((cx1 + 45, cy1 + 165), "Beyond The Boundary 🏏", font=f_sub, fill=(200, 215, 235))

        # Like Share Subscribe Pill
        pill_w = 600
        pill_h = 58
        px1 = cx1 + 45
        py1 = cy1 + 245
        draw.rounded_rectangle([px1, py1, px1 + pill_w, py1 + pill_h], radius=14, fill=cls.COLOR_RED, outline=cls.COLOR_GOLD, width=2)
        draw.text((px1 + 40, py1 + 11), "👍 LIKE  |  🔗 SHARE  |  🔔 SUBSCRIBE", font=f_cta, fill=cls.COLOR_WHITE)

        img.save(output_path, "PNG")
        return output_path
