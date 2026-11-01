"""
Cricket Shorts Engine V3 - Player Visual Asset & Graphic Card Provider
Renders high-production sports documentary player & stat graphics:
- Midnight Navy & Deep Gold broadcast palette
- Custom typography with RAQM Devanagari/Latin layout
- Red stat callout badges
- Designed for dynamic Ken Burns pan/zoom in FFmpeg
"""

import os
import math
from typing import Optional, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter

FONT_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_REG = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"


class PlayerAssetProvider:
    W = 1080
    H = 1920

    COLOR_BG_DARK = (10, 16, 28)
    COLOR_NAVY_GLASS = (16, 27, 50, 220)
    COLOR_GOLD = (234, 179, 8)       # #EAB308
    COLOR_AMBER = (245, 158, 11)     # #F59E0B
    COLOR_RED = (225, 29, 72)        # #E11D48
    COLOR_WHITE = (255, 255, 255)
    COLOR_MUTED = (148, 163, 184)    # #94A3B8

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        path = FONT_BOLD if bold else FONT_REG
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)
            except Exception:
                return ImageFont.truetype(path, size)
        return ImageFont.load_default()

    @classmethod
    def create_cinematic_fact_card(
        cls,
        badge_text: str,
        player_name: str,
        headline: str,
        subheadline: str,
        stat_callout: str,
        output_path: str,
        accent_color: str = "gold"
    ) -> str:
        """
        Creates a 1080x1920 broadcast documentary card with rich gradients,
        lighting aura, large typography, and stat callouts.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (10, 15, 26, 255))
        draw = ImageDraw.Draw(img)

        # 1. Background radial glow / stadium lighting effect
        # Create subtle circular gradient near upper-center
        center_x, center_y = cls.W // 2, 700
        for r in range(500, 50, -30):
            alpha = int(45 * (1.0 - (r / 500.0)))
            fill_col = (25, 45, 80, alpha) if accent_color != "red" else (70, 20, 30, alpha)
            draw.ellipse(
                [center_x - r, center_y - r, center_x + r, center_y + r],
                fill=fill_col
            )

        # 2. Grid lines / sports documentary texture
        for y in range(200, 1600, 120):
            draw.line([(80, y), (cls.W - 80, y)], fill=(255, 255, 255, 6), width=1)
        for x in range(120, cls.W, 140):
            draw.line([(x, 300), (x, 1500)], fill=(255, 255, 255, 5), width=1)

        # 3. Channel branding badge at top (y = 80)
        f_brand = cls.get_font(22, bold=True)
        brand_txt = "🏏  CRICKET RAAZ EXCLUSIVE"
        bbox = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox[2] - bbox[0]) + 40
        bh = 44
        bx1 = (cls.W - bw) // 2
        by1 = 80
        draw.rounded_rectangle([bx1, by1, bx1 + bw, by1 + bh], radius=12, fill=cls.COLOR_NAVY_GLASS, outline=cls.COLOR_GOLD, width=2)
        draw.text((bx1 + 20, by1 + 9), brand_txt, font=f_brand, fill=cls.COLOR_GOLD)

        # 4. Fact number capsule badge (y = 280)
        f_badge = cls.get_font(34, bold=True)
        bbox_b = draw.textbbox((0, 0), badge_text, font=f_badge)
        cw = (bbox_b[2] - bbox_b[0]) + 56
        ch = 64
        cx1 = (cls.W - cw) // 2
        cy1 = 290
        # Pill glow
        draw.rounded_rectangle([cx1 - 3, cy1 - 3, cx1 + cw + 3, cy1 + ch + 3], radius=20, fill=(234, 179, 8, 40))
        draw.rounded_rectangle([cx1, cy1, cx1 + cw, cy1 + ch], radius=18, fill=cls.COLOR_RED if accent_color == "red" else cls.COLOR_AMBER)
        draw.text((cx1 + 28, cy1 + 12), badge_text, font=f_badge, fill=cls.COLOR_WHITE)

        # 5. Massive Player Name / Subject (y = 440)
        f_player = cls.get_font(68, bold=True)
        bbox_p = draw.textbbox((0, 0), player_name.upper(), font=f_player)
        pw = bbox_p[2] - bbox_p[0]
        px = (cls.W - pw) // 2
        draw.text((px, 440), player_name.upper(), font=f_player, fill=cls.COLOR_WHITE)

        # Underline accent
        draw.line([((cls.W - 320) // 2, 530), ((cls.W + 320) // 2, 530)], fill=cls.COLOR_GOLD, width=4)

        # 6. Central Stat Emblem Card (y = 620 to 1180)
        card_w = 920
        card_h = 520
        card_x = (cls.W - card_w) // 2
        card_y = 620
        # Glass backdrop
        draw.rounded_rectangle(
            [card_x, card_y, card_x + card_w, card_y + card_h],
            radius=28,
            fill=(16, 26, 46, 235),
            outline=cls.COLOR_GOLD,
            width=3
        )

        # Inside card: Main Headline
        f_head = cls.get_font(52, bold=True)
        bbox_h = draw.textbbox((0, 0), headline, font=f_head)
        hw = bbox_h[2] - bbox_h[0]
        hx = card_x + (card_w - hw) // 2
        draw.text((hx, card_y + 60), headline, font=f_head, fill=cls.COLOR_GOLD)

        # Subheadline
        f_sub = cls.get_font(34, bold=False)
        bbox_s = draw.textbbox((0, 0), subheadline, font=f_sub)
        sw = bbox_s[2] - bbox_s[0]
        sx = card_x + (card_w - sw) // 2
        draw.text((sx, card_y + 140), subheadline, font=f_sub, fill=cls.COLOR_MUTED)

        # Big Stat Callout Banner inside card
        stat_w = 680
        stat_h = 130
        stat_x = card_x + (card_w - stat_w) // 2
        stat_y = card_y + 240
        draw.rounded_rectangle(
            [stat_x, stat_y, stat_x + stat_w, stat_y + stat_h],
            radius=20,
            fill=(225, 29, 72, 235), # Crimson red for punch
            outline=cls.COLOR_WHITE,
            width=2
        )
        f_stat = cls.get_font(60, bold=True)
        bbox_st = draw.textbbox((0, 0), stat_callout, font=f_stat)
        stw = bbox_st[2] - bbox_st[0]
        stx = stat_x + (stat_w - stw) // 2
        draw.text((stx, stat_y + 25), stat_callout, font=f_stat, fill=cls.COLOR_WHITE)

        # Secondary label under stat
        f_note = cls.get_font(24, bold=True)
        note_txt = "OFFICIAL RECORD • VERIFIED STATISTIC"
        bbox_n = draw.textbbox((0, 0), note_txt, font=f_note)
        nw = bbox_n[2] - bbox_n[0]
        nx = card_x + (card_w - nw) // 2
        draw.text((nx, card_y + 420), note_txt, font=f_note, fill=cls.COLOR_MUTED)

        # 7. Lower dark gradient protection (y = 1500 to 1920) so subtitles remain 100% visible
        for y in range(cls.H - 350, cls.H):
            prog = (y - (cls.H - 350)) / 350.0
            alpha = int(220 * prog)
            draw.line([(0, y), (cls.W, y)], fill=(8, 12, 20, alpha))

        img.save(output_path, "PNG")
        return output_path

    @classmethod
    def create_hook_card(
        cls,
        title: str,
        subtitle: str,
        output_path: str
    ) -> str:
        """
        Renders opening hook title card (0-3s).
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (10, 15, 26, 255))
        draw = ImageDraw.Draw(img)

        # Top Badge
        f_brand = cls.get_font(24, bold=True)
        brand_txt = "🏏  CRICKET RAAZ TOP 3"
        bbox = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox[2] - bbox[0]) + 48
        bx = (cls.W - bw) // 2
        draw.rounded_rectangle([bx, 90, bx + bw, 138], radius=14, fill=cls.COLOR_NAVY_GLASS, outline=cls.COLOR_GOLD, width=2)
        draw.text((bx + 24, 100), brand_txt, font=f_brand, fill=cls.COLOR_GOLD)

        # Dramatic Center Hero Box
        card_w = 960
        card_h = 600
        cx = (cls.W - card_w) // 2
        cy = 500
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=32, fill=(16, 27, 50, 240), outline=cls.COLOR_GOLD, width=4)

        # Title words wrapped
        words = title.split()
        f_title = cls.get_font(64, bold=True)
        line1 = " ".join(words[:2]) if len(words) >= 2 else title
        line2 = " ".join(words[2:]) if len(words) > 2 else ""

        bbox1 = draw.textbbox((0, 0), line1, font=f_title)
        draw.text((cx + (card_w - (bbox1[2] - bbox1[0])) // 2, cy + 80), line1, font=f_title, fill=cls.COLOR_WHITE)

        if line2:
            bbox2 = draw.textbbox((0, 0), line2, font=f_title)
            draw.text((cx + (card_w - (bbox2[2] - bbox2[0])) // 2, cy + 180), line2, font=f_title, fill=cls.COLOR_GOLD)

        # Subtitle in Hindi
        f_sub = cls.get_font(38, bold=True)
        bbox_sub = draw.textbbox((0, 0), subtitle, font=f_sub)
        draw.text((cx + (card_w - (bbox_sub[2] - bbox_sub[0])) // 2, cy + 320), subtitle, font=f_sub, fill=(245, 158, 11))

        # Bottom badge: SWIPE TO WATCH
        cta_txt = "🔥 MUST WATCH UNTIL END 🔥"
        f_cta = cls.get_font(28, bold=True)
        bbox_c = draw.textbbox((0, 0), cta_txt, font=f_cta)
        cw = (bbox_c[2] - bbox_c[0]) + 40
        draw.rounded_rectangle([cx + (card_w - cw) // 2, cy + 450, cx + (card_w + cw) // 2, cy + 510], radius=16, fill=cls.COLOR_RED)
        draw.text((cx + (card_w - (bbox_c[2] - bbox_c[0])) // 2, cy + 465), cta_txt, font=f_cta, fill=cls.COLOR_WHITE)

        # Lower vignette
        for y in range(cls.H - 350, cls.H):
            prog = (y - (cls.H - 350)) / 350.0
            draw.line([(0, y), (cls.W, y)], fill=(8, 12, 20, int(220 * prog)))

        img.save(output_path, "PNG")
        return output_path

    @classmethod
    def create_outro_card(
        cls,
        cta_heading: str,
        cta_subheading: str,
        output_path: str
    ) -> str:
        """
        Renders outro CTA card.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        img = Image.new("RGBA", (cls.W, cls.H), (10, 15, 26, 255))
        draw = ImageDraw.Draw(img)

        # Header
        f_brand = cls.get_font(24, bold=True)
        brand_txt = "🏏  CRICKET RAAZ"
        bbox = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox[2] - bbox[0]) + 48
        bx = (cls.W - bw) // 2
        draw.rounded_rectangle([bx, 90, bx + bw, 138], radius=14, fill=cls.COLOR_NAVY_GLASS, outline=cls.COLOR_GOLD, width=2)
        draw.text((bx + 24, 100), brand_txt, font=f_brand, fill=cls.COLOR_GOLD)

        # Center Card
        card_w = 940
        card_h = 560
        cx = (cls.W - card_w) // 2
        cy = 540
        draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=32, fill=(16, 27, 50, 240), outline=cls.COLOR_GOLD, width=3)

        f_head = cls.get_font(52, bold=True)
        bbox_h = draw.textbbox((0, 0), cta_heading, font=f_head)
        draw.text((cx + (card_w - (bbox_h[2] - bbox_h[0])) // 2, cy + 90), cta_heading, font=f_head, fill=cls.COLOR_WHITE)

        f_sub = cls.get_font(36, bold=False)
        bbox_s = draw.textbbox((0, 0), cta_subheading, font=f_sub)
        draw.text((cx + (card_w - (bbox_s[2] - bbox_s[0])) // 2, cy + 180), cta_subheading, font=f_sub, fill=cls.COLOR_AMBER)

        # Red Subscribe Pill
        sub_txt = "🔴 SUBSCRIBE FOR DAILY FACTS"
        f_sub_pill = cls.get_font(32, bold=True)
        bbox_p = draw.textbbox((0, 0), sub_txt, font=f_sub_pill)
        pw = (bbox_p[2] - bbox_p[0]) + 50
        draw.rounded_rectangle([cx + (card_w - pw) // 2, cy + 300, cx + (card_w + pw) // 2, cy + 380], radius=20, fill=cls.COLOR_RED)
        draw.text((cx + (card_w - (bbox_p[2] - bbox_p[0])) // 2, cy + 322), sub_txt, font=f_sub_pill, fill=cls.COLOR_WHITE)

        # Lower vignette
        for y in range(cls.H - 350, cls.H):
            prog = (y - (cls.H - 350)) / 350.0
            draw.line([(0, y), (cls.W, y)], fill=(8, 12, 20, int(220 * prog)))

        img.save(output_path, "PNG")
        return output_path
