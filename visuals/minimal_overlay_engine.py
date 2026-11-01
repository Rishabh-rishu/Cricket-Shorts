"""
Minimal Documentary Overlay Engine
Renders sleek, semi-transparent 1080x1920 broadcast graphics:
- Transparent floating header pill
- Elegant lower-third metric badge (positioned above subtitles)
- Subtle cinematic vignette
- 100% transparent center canvas so moving footage remains fully visible
"""

import os
from typing import Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

from visuals.player_asset_provider import PlayerAssetProvider


class MinimalOverlayEngine:
    W = 1080
    H = 1920

    COLOR_GOLD = (255, 204, 0)
    COLOR_CYAN = (0, 212, 255)
    COLOR_RED = (235, 45, 45)
    COLOR_WHITE = (255, 255, 255)
    COLOR_GLASS = (10, 14, 24, 195) # 75% opacity frosted glass

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        return PlayerAssetProvider.get_font(size, "bold" if bold else "regular")

    @classmethod
    def create_scene_overlay(
        cls,
        top_badge: str,
        headline: str,
        metric: str,
        output_path: str,
        badge_color: Tuple[int, int, int] = COLOR_GOLD
    ) -> str:
        """
        Creates a high-end transparent RGBA overlay for a scene.
        Center remains 100% transparent for moving cricket video footage.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Subtle top & bottom cinematic gradient vignette (enhances contrast)
        for y in range(0, 180):
            alpha = int(140 * (1.0 - y / 180.0))
            draw.line([(0, y), (cls.W, y)], fill=(5, 8, 14, alpha))
        for y in range(cls.H - 250, cls.H):
            alpha = int(160 * ((y - (cls.H - 250)) / 250.0))
            draw.line([(0, y), (cls.W, y)], fill=(5, 8, 14, alpha))

        # 2. Sleek Floating Header Pill (y = 120)
        f_top = cls.get_font(26, bold=True)
        t_text = f"🏏 {top_badge.upper()}"
        bbox = draw.textbbox((0, 0), t_text, font=f_top)
        tw = (bbox[2] - bbox[0]) + 50
        tx1 = (cls.W - tw) // 2
        ty1 = 120
        draw.rounded_rectangle([tx1, ty1, tx1 + tw, ty1 + 48], radius=14, fill=cls.COLOR_GLASS, outline=badge_color, width=2)
        draw.text((tx1 + 25, ty1 + 8), t_text, font=f_top, fill=badge_color)

        # 3. Minimal Lower-Third Card (y = 1380, safely positioned above subtitles zone y=1520)
        if headline or metric:
            card_w = 900
            card_h = 110
            cx1 = (cls.W - card_w) // 2
            cy1 = 1380
            draw.rounded_rectangle([cx1, cy1, cx1 + card_w, cy1 + card_h], radius=18, fill=cls.COLOR_GLASS, outline=(40, 55, 80, 220), width=2)

            # Left accent highlight strip
            draw.rounded_rectangle([cx1, cy1, cx1 + 10, cy1 + card_h], radius=4, fill=badge_color)

            # Headline
            f_head = cls.get_font(32, bold=True)
            draw.text((cx1 + 32, cy1 + 18), headline, font=f_head, fill=cls.COLOR_WHITE)

            # Metric Pill on the right side
            f_met = cls.get_font(24, bold=True)
            m_text = f"★ {metric}"
            m_bbox = draw.textbbox((0, 0), m_text, font=f_met)
            mw = (m_bbox[2] - m_bbox[0]) + 30
            mx2 = cx1 + card_w - 25
            mx1 = mx2 - mw
            my1 = cy1 + 35
            draw.rounded_rectangle([mx1, my1, mx2, my1 + 38], radius=10, fill=(20, 32, 54, 230), outline=badge_color, width=1)
            draw.text((mx1 + 15, my1 + 6), m_text, font=f_met, fill=badge_color)

        img.save(output_path, "PNG")
        return output_path
