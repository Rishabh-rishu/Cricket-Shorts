"""
Cricket Shorts Engine V3 - Dynamic Multi-Theme Broadcast Graphics Engine
Implements strict visual uniqueness, dynamic theme palettes, and format-specific styling:
- Reusable across any cricket format (Test, ODI, T20) and any player
- Full 1080x1920 canvas utilization, 5 broadcast scene templates
- Zero-tofu typography (Mukta-Bold / Noto Sans)
"""

import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from typing import Dict, Any, Optional, Tuple, List
from visuals.theme_manager import ThemeManager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dual-script verified fonts
FONT_MUKTA_BOLD = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-Bold.ttf")
FONT_MUKTA_SEMI = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-SemiBold.ttf")
FONT_MUKTA_REG = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-Regular.ttf")

FONT_NOTO_DEV_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_NOTO_LAT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


class V3DemoGraphics:
    W = 1080
    H = 1920

    @classmethod
    def get_font(cls, size: int, weight: str = "bold") -> ImageFont.FreeTypeFont:
        """Loads Mukta or Noto Sans with automatic fallback."""
        if weight == "bold":
            preferred = [FONT_MUKTA_BOLD, FONT_NOTO_DEV_BOLD, FONT_NOTO_LAT_BOLD]
        elif weight == "semi":
            preferred = [FONT_MUKTA_SEMI, FONT_MUKTA_BOLD, FONT_NOTO_DEV_BOLD]
        else:
            preferred = [FONT_MUKTA_REG, FONT_MUKTA_SEMI, FONT_NOTO_DEV_BOLD]

        for p in preferred:
            if p and os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size, layout_engine=ImageFont.Layout.RAQM)
                except Exception:
                    try:
                        return ImageFont.truetype(p, size)
                    except Exception:
                        continue
        return ImageFont.load_default()

    @classmethod
    def create_base_canvas(
        cls,
        theme: Dict[str, Any],
        bg_image_path: Optional[str] = None
    ) -> Image.Image:
        """
        Creates 1080x1920 base canvas with theme background and atmospheric stadium floodlights.
        Guarantees NO player images are used as background.
        """
        canvas = Image.new("RGBA", (cls.W, cls.H), theme["bg_dark"])

        stadium_candidates = [
            bg_image_path,
            os.path.join(PROJECT_ROOT, "assets", "stadium_beams_clean.jpg"),
            os.path.join(PROJECT_ROOT, "assets", "stadium_beams_cropped.jpg"),
            os.path.join(PROJECT_ROOT, "assets", "stadium_bg_base.jpg")
        ]
        loaded_bg = None
        for cand in stadium_candidates:
            if cand and os.path.exists(cand):
                try:
                    img = Image.open(cand).convert("RGBA")
                    aspect = img.width / img.height
                    target_aspect = cls.W / cls.H
                    if aspect > target_aspect:
                        new_h = cls.H
                        new_w = int(new_h * aspect)
                    else:
                        new_w = cls.W
                        new_h = int(new_w / aspect)
                    img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                    x1 = (new_w - cls.W) // 2
                    y1 = (new_h - cls.H) // 2
                    img = img.crop((x1, y1, x1 + cls.W, y1 + cls.H))
                    loaded_bg = img
                    break
                except Exception:
                    continue

        if loaded_bg:
            bg_dark = Image.new("RGBA", (cls.W, cls.H), (theme["bg_dark"][0], theme["bg_dark"][1], theme["bg_dark"][2], 195))
            canvas.alpha_composite(loaded_bg)
            canvas.alpha_composite(bg_dark)
        else:
            draw = ImageDraw.Draw(canvas)
            for y in range(cls.H):
                ratio = y / cls.H
                r = int(theme["bg_dark"][0] + 15 * ratio)
                g = int(theme["bg_dark"][1] + 15 * ratio)
                b = int(theme["bg_dark"][2] + 25 * ratio)
                draw.line([(0, y), (cls.W, y)], fill=(r, g, b, 255))

        # Volumetric theme floodlights
        beams = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        b_draw = ImageDraw.Draw(beams)
        for angle in range(-45, 10, 6):
            rad = math.radians(angle + 90)
            ex = int(180 + 1600 * math.cos(rad))
            ey = int(100 + 1600 * math.sin(rad))
            b_draw.polygon([(180, 80), (ex - 40, ey), (ex + 40, ey)], fill=(255, 240, 200, 18))
        for angle in range(-10, 45, 6):
            rad = math.radians(angle + 90)
            ex = int(900 + 1600 * math.cos(rad))
            ey = int(100 + 1600 * math.sin(rad))
            b_draw.polygon([(900, 80), (ex - 40, ey), (ex + 40, ey)], fill=(255, 240, 200, 18))

        b_draw.ellipse([(80, 20), (280, 180)], fill=(255, 245, 210, 90))
        b_draw.ellipse([(800, 20), (1000, 180)], fill=(255, 245, 210, 90))
        beams = beams.filter(ImageFilter.GaussianBlur(30))
        canvas.alpha_composite(beams)

        # Vignette shadows
        vignette = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        v_draw = ImageDraw.Draw(vignette)
        for y in range(1420, cls.H):
            prog = (y - 1420) / (cls.H - 1420)
            alpha = int(245 * (prog ** 1.3))
            v_draw.line([(0, y), (cls.W, y)], fill=(theme["bg_dark"][0], theme["bg_dark"][1], theme["bg_dark"][2], alpha))
        for y in range(0, 200):
            prog = 1.0 - (y / 200.0)
            alpha = int(210 * (prog ** 1.5))
            v_draw.line([(0, y), (cls.W, y)], fill=(theme["bg_dark"][0], theme["bg_dark"][1], theme["bg_dark"][2], alpha))

        canvas.alpha_composite(vignette)
        return canvas

    @classmethod
    def add_broadcast_header(
        cls,
        canvas: Image.Image,
        theme: Dict[str, Any],
        category: str = "ICC TEST CRICKET • HISTORIC MILESTONE",
        badge_text: str = "CRICKET RAAZ EXCLUSIVE"
    ):
        """Top broadcast header pill at y=80-160 using theme colors."""
        draw = ImageDraw.Draw(canvas)
        font_pill = cls.get_font(26, weight="bold")
        font_cat = cls.get_font(24, weight="semi")

        pill_w, pill_h = 360, 52
        px, py = 50, 90
        draw.rounded_rectangle(
            [(px, py), (px + pill_w, py + pill_h)],
            radius=26,
            fill=theme["pill_bg"],
            outline=theme["accent_primary"],
            width=2
        )
        draw.ellipse([(px + 18, py + 18), (px + 32, py + 32)], fill=theme["accent_primary"])
        draw.text((px + 44, py + 11), badge_text, font=font_pill, fill=theme["text_white"])

        cat_bbox = draw.textbbox((0, 0), category, font=font_cat)
        cat_w = cat_bbox[2] - cat_bbox[0]
        cx = cls.W - 50 - cat_w - 30
        draw.rounded_rectangle(
            [(cx, py), (cls.W - 50, py + pill_h)],
            radius=26,
            fill=theme["pill_bg"],
            outline=theme["accent_gold"],
            width=1
        )
        draw.text((cx + 15, py + 12), category, font=font_cat, fill=theme["accent_gold"])

    @staticmethod
    def draw_star(draw: ImageDraw.ImageDraw, center: Tuple[int, int], radius: float, fill: Any):
        """Draws a crisp 5-point vector star to prevent missing glyph / tofu rendering."""
        points = []
        for i in range(10):
            r = radius if i % 2 == 0 else radius * 0.42
            angle = -math.pi / 2 + i * (math.pi / 5)
            points.append((center[0] + r * math.cos(angle), center[1] + r * math.sin(angle)))
        draw.polygon(points, fill=fill)

    # =========================================================================
    # SCENE 1: OPENING HOOK
    # =========================================================================
    @classmethod
    def create_opening_scene(
        cls,
        theme: Dict[str, Any],
        bg_stadium_path: Optional[str] = None,
        alert_tag: str = "TEST RECORD ALERT",
        title: str = "400 NOT OUT",
        subtitle: str = "THE GREATEST TEST INNINGS",
        pod_title: str = "THE HISTORIC MATCH",
        pod_sub: str = "4th Test Match • Antigua Recreation Ground",
        rows_data: Optional[List[Tuple[str, str]]] = None,
        output_path: str = "output/demo_v3/previews/scene1_opening_hook.png"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme, bg_image_path=bg_stadium_path)
        cls.add_broadcast_header(canvas, theme, category="TEST CRICKET RECORD", badge_text="CRICKET RAAZ SPECIAL")

        draw = ImageDraw.Draw(canvas)

        # Central thematic radiant aura
        aura = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        a_draw = ImageDraw.Draw(aura)
        a_draw.ellipse([(cls.W // 2 - 450, 420), (cls.W // 2 + 450, 1050)], fill=theme["glow_primary"])
        a_draw.ellipse([(cls.W // 2 - 280, 520), (cls.W // 2 + 280, 950)], fill=theme["glow_secondary"])
        aura = aura.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(aura)

        # Alert Badge with crisp vector stars (Zero Tofu)
        draw = ImageDraw.Draw(canvas)
        font_tag = cls.get_font(26, weight="bold")
        clean_tag = alert_tag.replace("★", "").replace("•", "").strip()
        bbox_tag = draw.textbbox((0, 0), clean_tag, font=font_tag)
        tag_text_w = bbox_tag[2] - bbox_tag[0]
        tag_w = tag_text_w + 120
        tag_h = 52
        tx, ty = (cls.W - tag_w) // 2, 280

        draw.rounded_rectangle(
            [(tx, ty), (tx + tag_w, ty + tag_h)],
            radius=26,
            fill=theme["accent_primary"],
            outline=theme["accent_gold"],
            width=2
        )
        draw.text((tx + 60, ty + 12), clean_tag, font=font_tag, fill=theme["text_white"])
        cls.draw_star(draw, (tx + 32, ty + 26), 9, fill=theme["accent_gold"])
        cls.draw_star(draw, (tx + tag_w - 32, ty + 26), 9, fill=theme["accent_gold"])

        # Giant 3D Title
        font_main = cls.get_font(92, weight="bold")
        bbox_m = draw.textbbox((0, 0), title, font=font_main)
        mw = bbox_m[2] - bbox_m[0]
        mx = (cls.W - mw) // 2
        my = 365

        for offset in [(4, 4), (2, 2), (-2, 2), (2, -2)]:
            draw.text((mx + offset[0], my + offset[1]), title, font=font_main, fill=(0, 0, 0, 240))
        draw.text((mx, my), title, font=font_main, fill=theme["accent_gold"])

        # Subtitle
        font_sub = cls.get_font(44, weight="bold")
        bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox_s[2] - bbox_s[0]
        sx = (cls.W - sw) // 2
        sy = 485
        draw.text((sx + 2, sy + 2), subtitle, font=font_sub, fill=(0, 0, 0, 220))
        draw.text((sx, sy), subtitle, font=font_sub, fill=theme["accent_silver"])

        # Context Pod
        pod_w, pod_h = 920, 600
        pod_x = (cls.W - pod_w) // 2
        pod_y = 580

        draw.rounded_rectangle(
            [(pod_x, pod_y), (pod_x + pod_w, pod_y + pod_h)],
            radius=28,
            fill=theme["bg_card"],
            outline=theme["border_highlight"],
            width=3
        )
        draw.rounded_rectangle(
            [(pod_x, pod_y), (pod_x + pod_w, pod_y + 110)],
            radius=28,
            fill=theme["bg_card_header"]
        )

        font_pod_h = cls.get_font(38, weight="bold")
        font_pod_sub = cls.get_font(26, weight="semi")
        draw.text((pod_x + 40, pod_y + 24), pod_title, font=font_pod_h, fill=theme["text_white"])
        draw.text((pod_x + 40, pod_y + 70), pod_sub, font=font_pod_sub, fill=theme["text_muted"])

        if not rows_data:
            rows_data = [
                ("MATCH VENUE", "Antigua Recreation Ground, St John's"),
                ("HISTORIC DATE", "10 - 12 April 2004"),
                ("OPPONENT", "West Indies vs England (4th Test)"),
                ("THE RECORD", "First & Only 400 In 147 Years of Test Cricket")
            ]

        font_rk = cls.get_font(24, weight="semi")
        font_rv = cls.get_font(32, weight="bold")

        ry = pod_y + 135
        for i, (k, v) in enumerate(rows_data):
            draw.text((pod_x + 40, ry), k, font=font_rk, fill=theme["text_muted"])
            val_col = theme["accent_gold"] if i == 3 else theme["text_white"]
            draw.text((pod_x + 40, ry + 32), v, font=font_rv, fill=val_col)
            if i < len(rows_data) - 1:
                draw.line([(pod_x + 40, ry + 80), (pod_x + pod_w - 40, ry + 80)], fill=(255, 255, 255, 25), width=1)
            ry += 112

        # Bottom Broadcast Feature Banner (Full-Screen Utilization, No Dead Space)
        b_banner_y = 1240
        b_banner_h = 170
        draw.rounded_rectangle(
            [(pod_x, b_banner_y), (pod_x + pod_w, b_banner_y + b_banner_h)],
            radius=22,
            fill=theme["bg_card"],
            outline=theme["accent_primary"],
            width=2
        )
        draw.rounded_rectangle(
            [(pod_x + 24, b_banner_y + 20), (pod_x + 360, b_banner_y + 64)],
            radius=12,
            fill=theme["accent_primary"]
        )
        font_bpill = cls.get_font(22, weight="bold")
        draw.text((pod_x + 42, b_banner_y + 30), "UNBROKEN WORLD RECORD", font=font_bpill, fill=theme["text_white"])

        font_btitle = cls.get_font(32, weight="bold")
        font_bsub = cls.get_font(24, weight="semi")
        draw.text((pod_x + 30, b_banner_y + 82), "778 Minutes At The Crease • 582 Balls Faced", font=font_btitle, fill=theme["accent_gold"])
        draw.text((pod_x + 30, b_banner_y + 124), "147 Years of Test Cricket • Still The Highest Score in History", font=font_bsub, fill=theme["accent_silver"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 2: PLAYER HERO SPORTS POSTER
    # =========================================================================
    @classmethod
    def create_player_hero_scene(
        cls,
        theme: Dict[str, Any],
        player_poster_path: str,
        player_name: str = "BRIAN LARA",
        hero_tag: str = "THE PRINCE OF TRINIDAD | TEST CRICKET ICON",
        stencil_lines: Tuple[str, str] = ("BRIAN", "LARA"),
        callouts: Optional[List[Dict[str, Any]]] = None,
        bot_banner1: str = "THE RECORD STANDS UNBROKEN",
        bot_banner2: str = "400*",
        output_path: str = "output/demo_v3/previews/scene2_player_hero.png"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="TEST CRICKET LEGEND", badge_text="#400NOTOUT")

        # Background Stencil Typography
        stencil = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        st_draw = ImageDraw.Draw(stencil)
        font_stencil = cls.get_font(180, weight="bold")
        st_draw.text((60, 360), stencil_lines[0], font=font_stencil, fill=(255, 255, 255, 22))
        st_draw.text((60, 520), stencil_lines[1], font=font_stencil, fill=(255, 255, 255, 18))
        stencil = stencil.filter(ImageFilter.GaussianBlur(2))
        canvas.alpha_composite(stencil)

        # Hero Player Cutout
        if os.path.exists(player_poster_path):
            try:
                p_crop = Image.open(player_poster_path).convert("RGBA")
                target_h = 1200
                aspect = p_crop.width / p_crop.height
                target_w = int(target_h * aspect)
                p_crop = p_crop.resize((target_w, target_h), Image.Resampling.LANCZOS)

                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_b = 320
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                p_crop.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                px = (cls.W - target_w) // 2
                py = 320
                canvas.alpha_composite(p_crop, (px, py))
            except Exception as e:
                print(f"Error loading hero poster: {e}")

        # Typography
        draw = ImageDraw.Draw(canvas)
        font_name = cls.get_font(92, weight="bold")
        font_sub = cls.get_font(30, weight="bold")

        name_bbox = draw.textbbox((0, 0), player_name, font=font_name)
        nw = name_bbox[2] - name_bbox[0]
        nx = (cls.W - nw) // 2
        ny = 200

        draw.text((nx + 3, ny + 3), player_name, font=font_name, fill=(0, 0, 0, 240))
        draw.text((nx, ny), player_name, font=font_name, fill=theme["text_white"])

        sub_bbox = draw.textbbox((0, 0), hero_tag, font=font_sub)
        sw = sub_bbox[2] - sub_bbox[0]
        sx = (cls.W - sw) // 2
        sy = ny + 105
        draw.text((sx + 2, sy + 2), hero_tag, font=font_sub, fill=(0, 0, 0, 200))
        draw.text((sx, sy), hero_tag, font=font_sub, fill=theme["accent_primary"])

        if not callouts:
            callouts = [
                {"text": "RECORD HOLDER", "x": 50, "y": 620, "color": theme["text_white"], "border": theme["accent_primary"]},
                {"text": "13 HOURS BATTING", "x": 50, "y": 740, "color": theme["text_white"], "border": theme["accent_gold"]},
                {"text": "582 BALLS FACED", "x": 50, "y": 860, "color": theme["text_white"], "border": theme["accent_silver"]},
                {"text": "400* UNBEATEN", "x": 730, "y": 620, "color": theme["accent_gold"], "border": theme["accent_gold"]},
                {"text": "43 FOURS 4 SIXES", "x": 710, "y": 740, "color": theme["accent_primary"], "border": theme["accent_primary"]},
                {"text": "THE PRINCE", "x": 750, "y": 860, "color": theme["text_white"], "border": theme["accent_silver"]},
            ]

        font_badge = cls.get_font(26, weight="bold")
        for b in callouts:
            bb = draw.textbbox((0, 0), b["text"], font=font_badge)
            bw = (bb[2] - bb[0]) + 44
            bh = 48
            bx, by = b["x"], b["y"]
            draw.rounded_rectangle(
                [(bx, by), (bx + bw, by + bh)],
                radius=14,
                fill=theme["pill_bg"],
                outline=b["border"],
                width=2
            )
            cls.draw_star(draw, (bx + 18, by + 24), 6, fill=b["color"])
            draw.text((bx + 32, by + 8), b["text"], font=font_badge, fill=b["color"])

        # Bottom banner
        bot_banner_y = 1430
        draw.rounded_rectangle(
            [(60, bot_banner_y), (cls.W - 60, bot_banner_y + 80)],
            radius=18,
            fill=theme["bg_card"],
            outline=theme["accent_gold"],
            width=2
        )
        font_bot1 = cls.get_font(34, weight="bold")
        font_bot2 = cls.get_font(44, weight="bold")
        draw.text((95, bot_banner_y + 20), bot_banner1, font=font_bot1, fill=theme["text_white"])
        draw.text((820, bot_banner_y + 14), bot_banner2, font=font_bot2, fill=theme["accent_gold"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 3: RECORD STATISTICS PRESENTATION
    # =========================================================================
    @classmethod
    def create_record_stats_scene(
        cls,
        theme: Dict[str, Any],
        action_photo_path: str,
        player_name: str = "Masterclass Lara",
        stats_subtitle: str = "World Record Stats in Test Cricket",
        stats: Optional[List[Dict[str, Any]]] = None,
        bot_tag1: str = "#TEST CRICKET",
        bot_tag2: str = "CRICKET RAAZ",
        bot_tag3: str = "WEST INDIES",
        output_path: str = "output/demo_v3/previews/scene3_record_stats.png"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="TEST MILESTONE", badge_text="ESPN CRICINFO STYLE")

        if os.path.exists(action_photo_path):
            try:
                p_img = Image.open(action_photo_path).convert("RGBA")
                target_h = 1280
                aspect = p_img.width / p_img.height
                target_w = int(target_h * aspect)
                p_img = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_r = int(target_w * 0.35)
                for x in range(target_w - fade_r, target_w):
                    m_arr[:, x] *= ((target_w - 1 - x) / fade_r) ** 1.3
                fade_b = 300
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                p_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
                g_draw = ImageDraw.Draw(glow)
                g_draw.ellipse([(20, 300), (450, 1100)], fill=theme.get("glow_primary", (120, 20, 40, 60)))
                glow = glow.filter(ImageFilter.GaussianBlur(60))
                canvas.alpha_composite(glow)

                canvas.alpha_composite(p_img, (-30, 240))
            except Exception as e:
                print(f"Stats action photo error: {e}")

        # Broadcast Card on Right Side
        card_x = 450
        card_y = 200
        card_w = 580
        card_h = 1260

        panel = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(panel)
        p_draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_w, card_y + card_h)],
            radius=24,
            fill=theme["bg_card"],
            outline=theme["border_highlight"],
            width=2
        )
        p_draw.rounded_rectangle(
            [(card_x, card_y), (card_x + card_w, card_y + 150)],
            radius=24,
            fill=theme["bg_card_header"]
        )
        canvas.alpha_composite(panel)

        draw = ImageDraw.Draw(canvas)
        font_title = cls.get_font(46, weight="bold")
        font_sub = cls.get_font(24, weight="semi")
        draw.text((card_x + 36, card_y + 24), player_name, font=font_title, fill=theme["text_white"])
        draw.text((card_x + 36, card_y + 82), stats_subtitle, font=font_sub, fill=theme["text_muted"])

        draw.line([(card_x + 36, card_y + 148), (card_x + card_w - 36, card_y + 148)], fill=theme["accent_gold"], width=4)

        if not stats:
            stats = [
                {"label": "TOTAL RUNS", "value": "400*", "highlight": True},
                {"label": "BALLS FACED", "value": "582", "sub": "Strike Rate 68.7"},
                {"label": "TIME ON CREASE", "value": "778m", "sub": "13 Hours Batting"},
                {"label": "BOUNDARIES", "value": "47", "sub": "43 Fours & 4 Sixes"},
                {"label": "TEAM TOTAL", "value": "751/5", "sub": "Decl vs England"},
            ]

        font_lbl = cls.get_font(22, weight="semi")
        font_val = cls.get_font(58, weight="bold")
        font_val_hl = cls.get_font(64, weight="bold")
        font_note = cls.get_font(22, weight="regular")

        start_y = card_y + 175
        spacing = (card_h - 260) / len(stats)

        for i, s in enumerate(stats):
            cy = int(start_y + i * spacing)
            if s.get("highlight"):
                draw.rounded_rectangle(
                    [(card_x + 20, cy - 6), (card_x + card_w - 20, cy + 128)],
                    radius=16,
                    fill=(theme["accent_primary"][0], theme["accent_primary"][1], theme["accent_primary"][2], 60),
                    outline=theme["accent_gold"],
                    width=2
                )
                draw.text((card_x + 36, cy + 8), s["label"].upper(), font=font_lbl, fill=theme["accent_gold"])
                draw.text((card_x + 36, cy + 42), s["value"], font=font_val_hl, fill=theme["accent_gold"])
                cls.draw_star(draw, (card_x + card_w - 50, cy + 40), 12, fill=theme["accent_gold"])
                if s.get("sub"):
                    draw.text((card_x + 230, cy + 62), f"• {s['sub']}", font=font_note, fill=theme["accent_silver"])
            else:
                draw.text((card_x + 36, cy + 8), s["label"].upper(), font=font_lbl, fill=theme["text_muted"])
                draw.text((card_x + 36, cy + 38), s["value"], font=font_val, fill=theme["text_white"])
                if s.get("sub"):
                    draw.text((card_x + 210, cy + 54), f"• {s['sub']}", font=font_note, fill=theme["accent_silver"])

            if i < len(stats) - 1:
                draw.line([(card_x + 36, cy + int(spacing - 15)), (card_x + card_w - 36, cy + int(spacing - 15))], fill=(255, 255, 255, 30), width=1)

        # Bottom Bar
        bot_y = card_y + card_h - 60
        font_bot = cls.get_font(22, weight="bold")
        draw.text((card_x + 36, bot_y), bot_tag1, font=font_bot, fill=theme["text_muted"])
        draw.text((card_x + 210, bot_y), bot_tag2, font=font_bot, fill=theme["accent_gold"])
        draw.text((card_x + card_w - 170, bot_y), bot_tag3, font=font_bot, fill=theme["accent_primary"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 4: ALL-TIME LEADERBOARD
    # =========================================================================
    @classmethod
    def create_leaderboard_scene(
        cls,
        theme: Dict[str, Any],
        captain_photo_path: str,
        title: str = "INTO THE RECORD BOOKS",
        subtitle: str = "HIGHEST INDIVIDUAL SCORES IN TEST CRICKET*",
        rows: Optional[List[Dict[str, Any]]] = None,
        callout_h: str = "ONLY QUADRUPLE CENTURY IN HISTORY",
        callout_s: str = "Brian Lara broke Hayden's 380 record just 6 months later!",
        output_path: str = "output/demo_v3/previews/scene4_leaderboard.png"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="HISTORIC RANKINGS", badge_text="ICC HALL OF FAME")

        # High-res player portrait in Test whites positioned on right half
        if os.path.exists(captain_photo_path):
            try:
                p_img = Image.open(captain_photo_path).convert("RGBA")
                target_h = 1240
                aspect = p_img.width / p_img.height
                target_w = int(target_h * aspect)
                p_img = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_l = int(target_w * 0.45)
                for x in range(fade_l):
                    m_arr[:, x] *= (x / fade_l) ** 1.3
                fade_b = 320
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                p_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                px = cls.W - target_w + 30
                py = 280
                canvas.alpha_composite(p_img, (px, py))
            except Exception as e:
                print(f"Leaderboard captain photo error: {e}")

        draw = ImageDraw.Draw(canvas)
        font_h1 = cls.get_font(68, weight="bold")
        font_h2 = cls.get_font(26, weight="semi")

        draw.text((50, 200), title, font=font_h1, fill=theme["text_white"])
        draw.text((54, 280), subtitle, font=font_h2, fill=theme["text_muted"])

        draw.line([(50, 335), (680, 335)], fill=(255, 255, 255, 60), width=2)

        # Clean Column Headers with exact spacing (NO COLLISION)
        font_col = cls.get_font(22, weight="bold")
        draw.text((65, 350), "#", font=font_col, fill=theme["text_muted"])
        draw.text((115, 350), "BATSMAN", font=font_col, fill=theme["text_muted"])
        draw.text((380, 350), "OPPONENT", font=font_col, fill=theme["text_muted"])
        draw.text((605, 350), "RUNS", font=font_col, fill=theme["text_muted"])

        draw.line([(50, 385), (680, 385)], fill=(255, 255, 255, 40), width=1)

        if not rows:
            rows = [
                {"rank": "1", "player": "Brian Lara", "country": "WI", "inns": "v ENG (2004)", "stat": "400*", "highlight": True},
                {"rank": "2", "player": "Matthew Hayden", "country": "AUS", "inns": "v ZIM (2003)", "stat": "380", "highlight": False},
                {"rank": "3", "player": "Brian Lara", "country": "WI", "inns": "v ENG (1994)", "stat": "375", "highlight": False},
                {"rank": "4", "player": "M. Jayawardene", "country": "SL", "inns": "v SA (2006)", "stat": "374", "highlight": False},
                {"rank": "5", "player": "Gary Sobers", "country": "WI", "inns": "v PAK (1958)", "stat": "365*", "highlight": False},
            ]

        start_y = 405
        row_height = 120
        font_row_name = cls.get_font(30, weight="bold")
        font_row_country = cls.get_font(20, weight="semi")
        font_row_inns = cls.get_font(22, weight="bold")
        font_row_stat = cls.get_font(44, weight="bold")

        for i, r in enumerate(rows):
            ry = start_y + i * (row_height + 12)
            if r.get("highlight"):
                draw.rounded_rectangle(
                    [(50, ry - 6), (680, ry + row_height - 6)],
                    radius=16,
                    fill=theme["bg_card"],
                    outline=theme["accent_gold"],
                    width=3
                )
                draw.rounded_rectangle([(62, ry + 24), (100, ry + 62)], radius=8, fill=theme["accent_gold"])
                draw.text((74, ry + 30), "1", font=font_row_inns, fill=(10, 15, 30))

                draw.text((115, ry + 16), r["player"], font=font_row_name, fill=theme["accent_gold"])
                draw.text((115, ry + 56), f"({r['country']})", font=font_row_country, fill=theme["accent_silver"])
                draw.text((380, ry + 30), r["inns"], font=font_row_inns, fill=theme["text_white"])

                # Right-aligned score to completely prevent any text overlap
                s_bbox = draw.textbbox((0, 0), r["stat"], font=font_row_stat)
                s_w = s_bbox[2] - s_bbox[0]
                draw.text((665 - s_w, ry + 18), r["stat"], font=font_row_stat, fill=theme["accent_gold"])
            else:
                draw.rounded_rectangle(
                    [(50, ry - 6), (680, ry + row_height - 6)],
                    radius=14,
                    fill=theme["pill_bg"],
                    outline=(255, 255, 255, 30),
                    width=1
                )
                draw.text((74, ry + 30), r["rank"], font=font_row_inns, fill=theme["text_muted"])
                draw.text((115, ry + 16), r["player"], font=font_row_name, fill=theme["text_white"])
                draw.text((115, ry + 56), f"({r['country']})", font=font_row_country, fill=theme["text_muted"])
                draw.text((380, ry + 30), r["inns"], font=font_row_inns, fill=theme["text_muted"])

                # Right-aligned score
                s_bbox = draw.textbbox((0, 0), r["stat"], font=font_row_stat)
                s_w = s_bbox[2] - s_bbox[0]
                draw.text((665 - s_w, ry + 20), r["stat"], font=font_row_stat, fill=theme["text_white"])

        font_note = cls.get_font(20, weight="regular")
        draw.text((54, 1160), "*ALL-TIME ICC MEN'S TEST CRICKET RECORDS (AS OF 2026)", font=font_note, fill=theme["text_muted"])

        # Bottom Callout Card with Zero Tofu
        draw.rounded_rectangle(
            [(50, 1210), (cls.W - 50, 1330)],
            radius=18,
            fill=theme["bg_card"],
            outline=theme["accent_primary"],
            width=2
        )
        font_callout = cls.get_font(28, weight="bold")
        cls.draw_star(draw, (85, 1248), 10, fill=theme["accent_gold"])
        draw.text((110, 1232), callout_h, font=font_callout, fill=theme["accent_gold"])
        draw.text((110, 1276), callout_s, font=font_note, fill=theme["text_white"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 5: OUTRO & DEBATE
    # =========================================================================
    @classmethod
    def create_final_reveal_scene(
        cls,
        theme: Dict[str, Any],
        trophy_photo_path: str,
        header: str = "THE GREATEST INNINGS IN TEST HISTORY?",
        question_title: str = "सवाल आपके लिए",
        question_hindi: str = "क्या कोई बल्लेबाज टेस्ट क्रिकेट में कभी\n400 रन का रिकॉर्ड तोड़ पाएगा?",
        question_eng: str = "Can any batsman in modern cricket ever\nsurpass Brian Lara's 400 not out?",
        output_path: str = "output/demo_v3/previews/scene5_final_reveal.png"
    ) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="COMMUNITY DEBATE", badge_text="SHARE YOUR OPINION")

        if os.path.exists(trophy_photo_path):
            try:
                t_img = Image.open(trophy_photo_path).convert("RGBA")
                target_h = 1200
                aspect = t_img.width / t_img.height
                target_w = int(target_h * aspect)
                t_img = t_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Soft atmospheric alpha composite
                mask = Image.new("L", (target_w, target_h), 140)
                m_arr = np.array(mask, dtype=np.float32)
                fade_b = 350
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                fade_t = 120
                for y in range(fade_t):
                    m_arr[y, :] *= (y / fade_t) ** 1.3
                t_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                px = (cls.W - target_w) // 2
                py = 220
                canvas.alpha_composite(t_img, (px, py))
            except Exception as e:
                print(f"Trophy/Celebration photo error: {e}")

        aura = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        a_draw = ImageDraw.Draw(aura)
        a_draw.ellipse([(cls.W // 2 - 380, 400), (cls.W // 2 + 380, 1100)], fill=theme["glow_secondary"])
        aura = aura.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(aura)

        draw = ImageDraw.Draw(canvas)
        font_h1 = cls.get_font(56, weight="bold")
        draw.text((70, 230), header, font=font_h1, fill=theme["accent_gold"])

        pod_x, pod_y = 60, 350
        pod_w, pod_h = cls.W - 120, 560

        draw.rounded_rectangle(
            [(pod_x, pod_y), (pod_x + pod_w, pod_y + pod_h)],
            radius=28,
            fill=theme["bg_card"],
            outline=theme["accent_gold"],
            width=3
        )

        font_q_title = cls.get_font(42, weight="bold")
        font_q_hindi = cls.get_font(38, weight="bold")
        font_q_eng = cls.get_font(28, weight="semi")

        draw.text((pod_x + 40, pod_y + 36), question_title, font=font_q_title, fill=theme["accent_primary"])
        draw.line([(pod_x + 40, pod_y + 100), (pod_x + pod_w - 40, pod_y + 100)], fill=theme["accent_gold"], width=2)

        draw.text((pod_x + 40, pod_y + 130), question_hindi, font=font_q_hindi, fill=theme["text_white"])
        draw.text((pod_x + 40, pod_y + 250), question_eng, font=font_q_eng, fill=theme["text_muted"])

        draw.rounded_rectangle(
            [(pod_x + 40, pod_y + 400), (pod_x + pod_w - 40, pod_y + 490)],
            radius=20,
            fill=theme["accent_gold"]
        )
        font_prompt = cls.get_font(32, weight="bold")
        draw.text((pod_x + 95, pod_y + 428), "COMMENT YOUR ANSWER BELOW!", font=font_prompt, fill=(10, 15, 30))

        sub_x, sub_y = 60, 1000
        sub_w, sub_h = cls.W - 120, 360

        draw.rounded_rectangle(
            [(sub_x, sub_y), (sub_x + sub_w, sub_y + sub_h)],
            radius=28,
            fill=theme["bg_card"],
            outline=theme["accent_primary"],
            width=2
        )

        font_ch = cls.get_font(52, weight="bold")
        font_ch_sub = cls.get_font(28, weight="semi")

        draw.text((sub_x + 50, sub_y + 36), "CRICKET RAAZ", font=font_ch, fill=theme["text_white"])
        draw.text((sub_x + 50, sub_y + 110), "Daily Rare Cricket Facts & World Records", font=font_ch_sub, fill=theme["text_muted"])

        btn_w, btn_h = sub_w - 100, 90
        bx, by = sub_x + 50, sub_y + 210
        draw.rounded_rectangle(
            [(bx, by), (bx + btn_w, by + btn_h)],
            radius=24,
            fill=theme["accent_primary"],
            outline=theme["text_white"],
            width=2
        )
        font_btn = cls.get_font(38, weight="bold")
        draw.text((bx + 110, by + 22), "SUBSCRIBE FOR MORE", font=font_btn, fill=theme["text_white"])

        canvas.save(output_path, quality=95)
        return output_path


class V3CinematicGraphics(V3DemoGraphics):
    pass

__all__ = ["V3CinematicGraphics", "V3DemoGraphics"]
