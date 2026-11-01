"""
Programmatic Cricket Animation and Graphic Engine
Generates 1080x1920 high-resolution visual scenes using Pillow & NumPy:
1. Cinematic Stadium & Pitch Backdrops with Stadium Floodlight Effects
2. Cricket Rule Demonstrations (e.g. Helmet 5-Penalty Runs, Mankading, Timed Out)
3. Broadcast Scoreboard & Record Cards (Big bold statistics, comparisons)
4. Player & Incident Spotlight Cards (Verified badge, historical context)
5. Call-to-Action Subscriber & Comment Screen
"""

import os
from typing import Dict, Any, Tuple
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

FONT_BOLD_PATH = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_REG_PATH = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf"


class CricketAnimationEngine:
    WIDTH = 1080
    HEIGHT = 1920

    # Sports palette
    COLOR_BG_DARK = (11, 16, 27)         # Deep stadium night blue
    COLOR_BG_CARD = (18, 25, 42)         # Sleek dark card
    COLOR_GOLD = (255, 204, 0)           # Cricket trophy gold
    COLOR_CYAN = (0, 212, 255)           # Electric sports cyan
    COLOR_WHITE = (255, 255, 255)
    COLOR_GRAY = (170, 185, 205)
    COLOR_RED = (235, 50, 50)            # Umpire penalty red
    COLOR_PITCH = (205, 175, 130)        # Cricket pitch clay/tan
    COLOR_GRASS = (24, 76, 42)           # Stadium lush green

    @classmethod
    def get_font(cls, size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
        font_path = FONT_BOLD_PATH if bold else FONT_REG_PATH
        if os.path.exists(font_path):
            return ImageFont.truetype(font_path, size)
        return ImageFont.load_default()

    @classmethod
    def create_stadium_background(cls, accent_color: Tuple[int, int, int] = COLOR_CYAN) -> Image.Image:
        """Generates a cinematic stadium night background with floodlight glow."""
        # Base radial gradient
        img = Image.new("RGBA", (cls.WIDTH, cls.HEIGHT), cls.COLOR_BG_DARK)
        draw = ImageDraw.Draw(img)

        # Draw stadium floodlight top glows
        glow_layer = Image.new("RGBA", (cls.WIDTH, cls.HEIGHT), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow_layer)

        # Top floodlights
        glow_draw.ellipse((-200, -200, 600, 600), fill=(accent_color[0], accent_color[1], accent_color[2], 45))
        glow_draw.ellipse((cls.WIDTH - 600, -200, cls.WIDTH + 200, 600), fill=(accent_color[0], accent_color[1], accent_color[2], 45))

        # Center subtle stadium pitch spotlight
        glow_draw.ellipse((140, 600, 940, 1400), fill=(accent_color[0], accent_color[1], accent_color[2], 30))

        glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(80))
        img = Image.alpha_composite(img, glow_layer)

        # Add subtle cricket field grass horizon at the bottom
        horizon = Image.new("RGBA", (cls.WIDTH, cls.HEIGHT), (0, 0, 0, 0))
        h_draw = ImageDraw.Draw(horizon)
        h_draw.rectangle([0, 1450, cls.WIDTH, cls.HEIGHT], fill=(16, 48, 28, 220))
        horizon = horizon.filter(ImageFilter.GaussianBlur(40))
        img = Image.alpha_composite(img, horizon)

        return img.convert("RGB")

    @classmethod
    def create_rule_scene(
        cls,
        topic: str,
        highlight_text: str,
        rule_label: str = "MCC LAW EXPLAINED",
        output_path: str = ""
    ) -> Image.Image:
        """
        Renders a detailed cricket pitch diagram demonstrating a rule (e.g. Helmet Penalty, Timed Out).
        """
        img = cls.create_stadium_background(accent_color=cls.COLOR_RED)
        draw = ImageDraw.Draw(img)

        # Top Category Badge
        cls._draw_header_badge(draw, rule_label, badge_color=cls.COLOR_RED)

        # Topic Title
        f_title = cls.get_font(52, bold=True)
        cls._draw_multiline_text_centered(draw, topic, y=280, font=f_title, fill=cls.COLOR_WHITE, max_width=920)

        # Visual Pitch Illustration Container
        pitch_box = [140, 480, 940, 1260]
        # Rounded grass outer pad
        draw.rounded_rectangle(pitch_box, radius=32, fill=(18, 54, 32), outline=cls.COLOR_CYAN, width=3)

        # Pitch strip in center
        strip_box = [370, 520, 710, 1220]
        draw.rectangle(strip_box, fill=cls.COLOR_PITCH, outline=(175, 145, 105), width=2)

        # Crease markings (Popping crease & bowling crease)
        # Batsman crease
        draw.line([(320, 680), (760, 680)], fill=cls.COLOR_WHITE, width=4)
        draw.rectangle([510, 630, 570, 640], fill=cls.COLOR_WHITE) # Stumps

        # Non-striker crease
        draw.line([(320, 1060), (760, 1060)], fill=cls.COLOR_WHITE, width=4)
        draw.rectangle([510, 1100, 570, 1110], fill=cls.COLOR_WHITE) # Stumps

        # Specific illustration: Helmet Behind Wicketkeeper with +5 Penalty badge
        if "helmet" in topic.lower() or "हेलमेट" in highlight_text.lower():
            # Helmet graphic behind batsman stumps
            draw.ellipse([500, 560, 580, 610], fill=(20, 40, 120), outline=cls.COLOR_GOLD, width=3)
            # Red warning circle
            draw.ellipse([470, 530, 610, 640], outline=cls.COLOR_RED, width=4)
            # Ball trajectory hitting helmet
            draw.line([(540, 800), (540, 615)], fill=cls.COLOR_GOLD, width=5)
            draw.ellipse([532, 605, 548, 621], fill=cls.COLOR_RED) # Red cricket ball

            # +5 RUNS PENALTY badge
            cls._draw_metric_pill(draw, "⚡ +5 PENALTY RUNS", x=540, y=750, color=cls.COLOR_RED)
        else:
            # Ball trajectory to stumps
            draw.line([(540, 1000), (540, 660)], fill=cls.COLOR_GOLD, width=5)
            draw.ellipse([532, 650, 548, 666], fill=cls.COLOR_RED) # Red cricket ball
            cls._draw_metric_pill(draw, "⚡ OFFICIAL CRICKET LAW", x=540, y=860, color=cls.COLOR_CYAN)

        # Key Explanatory Card below
        cls._draw_bottom_highlight_card(draw, highlight_text)

        if output_path:
            img.save(output_path, quality=95)
        return img

    @classmethod
    def create_scoreboard_scene(
        cls,
        title: str,
        big_metric: str,
        metric_label: str,
        detail_lines: list,
        output_path: str = ""
    ) -> Image.Image:
        """
        Renders an authentic sports broadcast digital scoreboard.
        """
        img = cls.create_stadium_background(accent_color=cls.COLOR_GOLD)
        draw = ImageDraw.Draw(img)

        # Top Category Badge
        cls._draw_header_badge(draw, "HISTORIC CRICKET RECORD", badge_color=cls.COLOR_GOLD)

        # Match / Record Title
        f_title = cls.get_font(48, bold=True)
        cls._draw_multiline_text_centered(draw, title, y=280, font=f_title, fill=cls.COLOR_WHITE, max_width=920)

        # Scoreboard Frame
        board_box = [100, 480, 980, 1240]
        draw.rounded_rectangle(board_box, radius=24, fill=cls.COLOR_BG_CARD, outline=cls.COLOR_GOLD, width=3)

        # Gold Banner inside scoreboard
        draw.rounded_rectangle([120, 500, 960, 580], radius=12, fill=(40, 32, 10), outline=cls.COLOR_GOLD, width=2)
        f_banner = cls.get_font(34, bold=True)
        cls._draw_multiline_text_centered(draw, "OFFICIAL MATCH RECORD", y=522, font=f_banner, fill=cls.COLOR_GOLD, max_width=800)

        # Big Hero Metric (e.g. 35 RUNS / 800 WICKETS / 36* NOT OUT)
        f_metric = cls.get_font(96, bold=True)
        cls._draw_multiline_text_centered(draw, big_metric, y=620, font=f_metric, fill=cls.COLOR_GOLD, max_width=860)

        # Metric Label
        f_lbl = cls.get_font(38, bold=True)
        cls._draw_multiline_text_centered(draw, metric_label, y=740, font=f_lbl, fill=cls.COLOR_CYAN, max_width=860)

        # Dividing line
        draw.line([(150, 810), (930, 810)], fill=(60, 75, 105), width=2)

        # Detailed breakdown rows
        y_cursor = 840
        f_row = cls.get_font(34, bold=False)
        for line in detail_lines[:3]:
            # Bullet dot
            draw.ellipse([160, y_cursor + 10, 175, y_cursor + 25], fill=cls.COLOR_GOLD)
            draw.text((195, y_cursor), line, font=f_row, fill=cls.COLOR_WHITE)
            y_cursor += 65

        # 100% Verified Stamp
        cls._draw_metric_pill(draw, "✓ 100% OFFICIALLY VERIFIED", x=540, y=1170, color=cls.COLOR_CYAN)

        if output_path:
            img.save(output_path, quality=95)
        return img

    @classmethod
    def create_spotlight_scene(
        cls,
        badge_text: str,
        headline: str,
        key_point: str,
        output_path: str = ""
    ) -> Image.Image:
        """
        Renders a cinematic player/incident spotlight card.
        """
        img = cls.create_stadium_background(accent_color=cls.COLOR_CYAN)
        draw = ImageDraw.Draw(img)

        # Top Badge
        cls._draw_header_badge(draw, badge_text, badge_color=cls.COLOR_CYAN)

        # Hero Headline
        f_head = cls.get_font(60, bold=True)
        cls._draw_multiline_text_centered(draw, headline, y=340, font=f_head, fill=cls.COLOR_WHITE, max_width=900)

        # Center Graphic Frame
        frame_box = [120, 550, 960, 1180]
        draw.rounded_rectangle(frame_box, radius=28, fill=cls.COLOR_BG_CARD, outline=cls.COLOR_CYAN, width=3)

        # Center Cricket Icon / Emblem
        center_x, center_y = 540, 750
        draw.ellipse([center_x - 110, center_y - 110, center_x + 110, center_y + 110], fill=(22, 38, 62), outline=cls.COLOR_GOLD, width=4)
        # Cricket ball in center
        draw.ellipse([center_x - 70, center_y - 70, center_x + 70, center_y + 70], fill=cls.COLOR_RED, outline=cls.COLOR_WHITE, width=2)
        # Seam
        draw.arc([center_x - 60, center_y - 65, center_x + 60, center_y + 65], start=45, end=225, fill=cls.COLOR_WHITE, width=3)

        # Key Point Box below Emblem
        f_point = cls.get_font(42, bold=True)
        cls._draw_multiline_text_centered(draw, key_point, y=930, font=f_point, fill=cls.COLOR_GOLD, max_width=780)

        # Verified by Wisden & ICC pill
        cls._draw_metric_pill(draw, "★ ICC & WISDEN STATS ARCHIVE", x=540, y=1110, color=cls.COLOR_CYAN)

        if output_path:
            img.save(output_path, quality=95)
        return img

    @classmethod
    def create_cta_scene(
        cls,
        question_text: str,
        output_path: str = ""
    ) -> Image.Image:
        """
        Renders high-engagement Call to Action screen (Comments + Subscribe).
        """
        img = cls.create_stadium_background(accent_color=cls.COLOR_GOLD)
        draw = ImageDraw.Draw(img)

        # Top Badge
        cls._draw_header_badge(draw, "YOUR OPINION MATTERS", badge_color=cls.COLOR_GOLD)

        # Question prompt
        f_q = cls.get_font(52, bold=True)
        cls._draw_multiline_text_centered(draw, question_text, y=340, font=f_q, fill=cls.COLOR_WHITE, max_width=900)

        # Comment & Subscribe Box
        card_box = [100, 600, 980, 1180]
        draw.rounded_rectangle(card_box, radius=30, fill=cls.COLOR_BG_CARD, outline=cls.COLOR_GOLD, width=3)

        # Subscribe Pill Button
        sub_box = [200, 700, 880, 810]
        draw.rounded_rectangle(sub_box, radius=20, fill=cls.COLOR_RED)
        f_btn = cls.get_font(46, bold=True)
        cls._draw_multiline_text_centered(draw, "🔔 SUBSCRIBE FOR DAILY FACTS", y=725, font=f_btn, fill=cls.COLOR_WHITE, max_width=660)

        # Comment Icon & prompt
        f_com = cls.get_font(40, bold=True)
        cls._draw_multiline_text_centered(draw, "💬 कमेंट्स में अपनी राय जरूर लिखें!", y=900, font=f_com, fill=cls.COLOR_GOLD, max_width=780)
        f_sub2 = cls.get_font(34, bold=False)
        cls._draw_multiline_text_centered(draw, "रोजाना 2 नए अनसुने क्रिकेट फैक्ट्स 🏏", y=980, font=f_sub2, fill=cls.COLOR_GRAY, max_width=780)

        if output_path:
            img.save(output_path, quality=95)
        return img

    @classmethod
    def _draw_header_badge(cls, draw: ImageDraw.Draw, text: str, badge_color: Tuple[int, int, int]):
        """Renders top category pill badge."""
        font = cls.get_font(28, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = (bbox[2] - bbox[0]) + 60
        x1 = (cls.WIDTH - w) // 2
        y1 = 150
        x2 = x1 + w
        y2 = y1 + 54
        draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=(18, 25, 42), outline=badge_color, width=2)
        draw.text((x1 + 30, y1 + 10), text, font=font, fill=badge_color)

    @classmethod
    def _draw_metric_pill(cls, draw: ImageDraw.Draw, text: str, x: int, y: int, color: Tuple[int, int, int]):
        """Renders small pill centered at (x, y)."""
        font = cls.get_font(26, bold=True)
        bbox = draw.textbbox((0, 0), text, font=font)
        w = (bbox[2] - bbox[0]) + 40
        h = (bbox[3] - bbox[1]) + 20
        box = [x - w // 2, y - h // 2, x + w // 2, y + h // 2]
        draw.rounded_rectangle(box, radius=12, fill=(14, 20, 32), outline=color, width=2)
        draw.text((x - w // 2 + 20, y - h // 2 + 8), text, font=font, fill=color)

    @classmethod
    def _draw_bottom_highlight_card(cls, draw: ImageDraw.Draw, text: str):
        """Renders highlight card at the bottom of the graphic."""
        box = [100, 1320, 980, 1500]
        draw.rounded_rectangle(box, radius=20, fill=cls.COLOR_BG_CARD, outline=cls.COLOR_GOLD, width=2)
        font = cls.get_font(34, bold=True)
        cls._draw_multiline_text_centered(draw, text, y=1350, font=font, fill=cls.COLOR_GOLD, max_width=820)

    @classmethod
    def _draw_multiline_text_centered(
        cls,
        draw: ImageDraw.Draw,
        text: str,
        y: int,
        font: ImageFont.FreeTypeFont,
        fill: Tuple[int, int, int],
        max_width: int
    ):
        """Splits text into lines fitting within max_width and draws centered."""
        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = " ".join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if (bbox[2] - bbox[0]) <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(" ".join(current_line))
                current_line = [word]

        if current_line:
            lines.append(" ".join(current_line))

        current_y = y
        line_height = font.size + 14
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]
            x = (cls.WIDTH - line_w) // 2
            draw.text((x, current_y), line, font=font, fill=fill)
            current_y += line_height
