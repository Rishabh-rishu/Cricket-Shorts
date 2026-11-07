"""
Cricket Shorts Engine V3 - Dynamic Multi-Theme Broadcast Graphics Engine
Implements strict visual uniqueness & dynamic theme color palettes:
1. Scene 1 (Opening Hook): Pure Atmospheric Night Stadium (No repeated player image)
2. Scene 2 (Player Hero): Displate Style Sports Poster Cutout (Virat celebration)
3. Scene 3 (Record Statistics): Authentic World Cup Batting Action Photo (4928x3264)
4. Scene 4 (Leaderboard): Intense Match Captaincy Portrait (2644x2365) + Zero-Tofu Badges
5. Scene 5 (Outro & Debate): Golden ICC World Cup Trophy (2448x3264) + Community Debate Pod
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

        # 2. Volumetric theme floodlights
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

        # 3. Vignette shadows
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
        category: str = "ICC WORLD CUP • HISTORIC MOMENT",
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

    # =========================================================================
    # SCENE 1: OPENING HOOK (Pure Stadium Floodlights & 3D Title, No Player Image)
    # =========================================================================
    @classmethod
    def create_opening_scene(
        cls,
        theme: Dict[str, Any],
        bg_stadium_path: Optional[str] = None,
        title: str = "50TH ODI CENTURY",
        subtitle: str = "THE CHASE MASTER",
        output_path: str = "output/demo_v3/previews/scene1_opening_hook.png"
    ) -> str:
        """
        Creates Hook scene: Pure atmospheric night stadium with volumetric light rays,
        stadium crowd atmosphere, and massive 3D kinetic typography.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme, bg_image_path=bg_stadium_path)
        cls.add_broadcast_header(canvas, theme, category="ALL-TIME WORLD RECORD", badge_text="CRICKET RAAZ SPECIAL")

        draw = ImageDraw.Draw(canvas)

        # 1. Central thematic radiant aura
        aura = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        a_draw = ImageDraw.Draw(aura)
        a_draw.ellipse([(cls.W // 2 - 450, 420), (cls.W // 2 + 450, 1050)], fill=theme["glow_primary"])
        a_draw.ellipse([(cls.W // 2 - 280, 520), (cls.W // 2 + 280, 950)], fill=theme["glow_secondary"])
        aura = aura.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(aura)

        # 2. Alert Badge
        draw = ImageDraw.Draw(canvas)
        tag_w, tag_h = 440, 52
        tx, ty = (cls.W - tag_w) // 2, 290
        draw.rounded_rectangle([(tx, ty), (tx + tag_w, ty + tag_h)], radius=26, fill=theme["accent_primary"], outline=theme["accent_gold"], width=2)
        font_tag = cls.get_font(26, weight="bold")
        draw.text((tx + 32, ty + 12), "★ WORLD RECORD ALERT ★", font=font_tag, fill=theme["text_white"])

        # 3. Giant 3D Title
        font_main = cls.get_font(88, weight="bold")
        bbox_m = draw.textbbox((0, 0), title, font=font_main)
        mw = bbox_m[2] - bbox_m[0]
        mx = (cls.W - mw) // 2
        my = 380

        # Drop shadows
        for offset in [(4, 4), (2, 2), (-2, 2), (2, -2)]:
            draw.text((mx + offset[0], my + offset[1]), title, font=font_main, fill=(0, 0, 0, 240))
        draw.text((mx, my), title, font=font_main, fill=theme["accent_gold"])

        # Subtitle
        font_sub = cls.get_font(48, weight="bold")
        bbox_s = draw.textbbox((0, 0), subtitle, font=font_sub)
        sw = bbox_s[2] - bbox_s[0]
        sx = (cls.W - sw) // 2
        sy = 495
        draw.text((sx + 2, sy + 2), subtitle, font=font_sub, fill=(0, 0, 0, 220))
        draw.text((sx, sy), subtitle, font=font_sub, fill=theme["accent_silver"])

        # 4. Central Visual Card: Historic Match Context Pod (y=640 to 1320)
        pod_w, pod_h = 920, 640
        pod_x = (cls.W - pod_w) // 2
        pod_y = 660

        draw.rounded_rectangle(
            [(pod_x, pod_y), (pod_x + pod_w, pod_y + pod_h)],
            radius=28,
            fill=theme["bg_card"],
            outline=theme["border_highlight"],
            width=3
        )

        # Header bar inside pod
        draw.rounded_rectangle(
            [(pod_x, pod_y), (pod_x + pod_w, pod_y + 110)],
            radius=28,
            fill=theme["bg_card_header"]
        )

        font_pod_h = cls.get_font(38, weight="bold")
        font_pod_sub = cls.get_font(26, weight="semi")
        draw.text((pod_x + 40, pod_y + 24), "THE HISTORIC DAY", font=font_pod_h, fill=theme["text_white"])
        draw.text((pod_x + 40, pod_y + 70), "ICC Cricket World Cup Semi-Final", font=font_pod_sub, fill=theme["text_muted"])

        # Match Details Rows
        rows_data = [
            ("MATCH VENUE", "Wankhede Stadium, Mumbai"),
            ("HISTORIC DATE", "15 November 2023"),
            ("OPPONENT", "India vs New Zealand"),
            ("THE MILESTONE", "Broke Sachin Tendulkar's Record of 49 ODI Tons")
        ]

        font_rk = cls.get_font(24, weight="semi")
        font_rv = cls.get_font(32, weight="bold")

        ry = pod_y + 140
        for i, (k, v) in enumerate(rows_data):
            draw.text((pod_x + 40, ry), k, font=font_rk, fill=theme["text_muted"])
            val_col = theme["accent_gold"] if i == 3 else theme["text_white"]
            draw.text((pod_x + 40, ry + 32), v, font=font_rv, fill=val_col)
            if i < len(rows_data) - 1:
                draw.line([(pod_x + 40, ry + 82), (pod_x + pod_w - 40, ry + 82)], fill=(255, 255, 255, 25), width=1)
            ry += 115

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 2: PLAYER HERO SPORTS POSTER (Displate Style Celebration Cutout)
    # =========================================================================
    @classmethod
    def create_player_hero_scene(
        cls,
        theme: Dict[str, Any],
        player_poster_path: str,
        output_path: str = "output/demo_v3/previews/scene2_player_hero.png"
    ) -> str:
        """
        Creates full-bleed sports poster using fresh Displate celebration cutout.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="CRICKET ICON • LEGEND", badge_text="#VK18 SPECIAL")

        # 1. Background Big Stencil: "KING KOHLI"
        stencil = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        st_draw = ImageDraw.Draw(stencil)
        font_stencil = cls.get_font(180, weight="bold")
        st_draw.text((60, 360), "KING", font=font_stencil, fill=(255, 255, 255, 24))
        st_draw.text((60, 520), "KOHLI", font=font_stencil, fill=(255, 255, 255, 20))
        stencil = stencil.filter(ImageFilter.GaussianBlur(2))
        canvas.alpha_composite(stencil)

        # 2. Hero Cutout Placement
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

        # 3. Typography
        draw = ImageDraw.Draw(canvas)
        font_name = cls.get_font(92, weight="bold")
        font_sub = cls.get_font(30, weight="bold")

        name_text = "VIRAT KOHLI"
        name_bbox = draw.textbbox((0, 0), name_text, font=font_name)
        nw = name_bbox[2] - name_bbox[0]
        nx = (cls.W - nw) // 2
        ny = 200

        draw.text((nx + 3, ny + 3), name_text, font=font_name, fill=(0, 0, 0, 240))
        draw.text((nx, ny), name_text, font=font_name, fill=theme["text_white"])

        hero_tag = "THE KING OF CHASES | INDIAN CRICKET ICON"
        sub_bbox = draw.textbbox((0, 0), hero_tag, font=font_sub)
        sw = sub_bbox[2] - sub_bbox[0]
        sx = (cls.W - sw) // 2
        sy = ny + 105
        draw.text((sx + 2, sy + 2), hero_tag, font=font_sub, fill=(0, 0, 0, 200))
        draw.text((sx, sy), hero_tag, font=font_sub, fill=theme["accent_primary"])

        # 4. Kinetic Callouts
        callouts = [
            {"text": "PASSION", "x": 60, "y": 620, "color": theme["text_white"], "border": theme["accent_primary"]},
            {"text": "AGGRESSION", "x": 70, "y": 740, "color": theme["text_white"], "border": theme["accent_gold"]},
            {"text": "INTENSITY", "x": 80, "y": 860, "color": theme["text_white"], "border": theme["accent_silver"]},
            {"text": "50 ODI TONS", "x": 770, "y": 620, "color": theme["accent_gold"], "border": theme["accent_gold"]},
            {"text": "CHASE MASTER", "x": 750, "y": 740, "color": theme["accent_primary"], "border": theme["accent_primary"]},
            {"text": "LEGENDARY", "x": 780, "y": 860, "color": theme["text_white"], "border": theme["accent_silver"]},
        ]

        font_badge = cls.get_font(28, weight="bold")
        for b in callouts:
            bb = draw.textbbox((0, 0), b["text"], font=font_badge)
            bw = (bb[2] - bb[0]) + 36
            bh = 46
            bx, by = b["x"], b["y"]
            draw.rounded_rectangle(
                [(bx, by), (bx + bw, by + bh)],
                radius=14,
                fill=theme["pill_bg"],
                outline=b["border"],
                width=2
            )
            draw.text((bx + 18, by + 8), b["text"], font=font_badge, fill=b["color"])

        # Bottom banner
        bot_banner_y = 1430
        draw.rounded_rectangle(
            [(60, bot_banner_y), (cls.W - 60, bot_banner_y + 80)],
            radius=18,
            fill=theme["bg_card"],
            outline=theme["accent_gold"],
            width=2
        )
        font_bot1 = cls.get_font(38, weight="bold")
        font_bot2 = cls.get_font(42, weight="bold")
        draw.text((95, bot_banner_y + 18), "THE LEGEND CONTINUES", font=font_bot1, fill=theme["text_white"])
        draw.text((820, bot_banner_y + 16), "vk 18", font=font_bot2, fill=theme["accent_gold"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 3: RECORD STATISTICS (Authentic World Cup Batting Action Photo)
    # =========================================================================
    @classmethod
    def create_record_stats_scene(
        cls,
        theme: Dict[str, Any],
        action_photo_path: str,
        output_path: str = "output/demo_v3/previews/scene3_record_stats.png"
    ) -> str:
        """
        Creates split-screen broadcast stats card with authentic World Cup batting action photo.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="CAREER MILESTONE", badge_text="ESPN CRICINFO STYLE")

        # 1. Action Batting Cutout on Left Side (x=-40 to 480)
        if os.path.exists(action_photo_path):
            try:
                p_img = Image.open(action_photo_path).convert("RGBA")
                target_h = 1250
                aspect = p_img.width / p_img.height
                target_w = int(target_h * aspect)
                p_img = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Fade right edge & bottom
                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_r = int(target_w * 0.35)
                for x in range(target_w - fade_r, target_w):
                    m_arr[:, x] *= ((target_w - 1 - x) / fade_r) ** 1.3
                fade_b = 300
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                p_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                # Glow behind action player
                glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
                g_draw = ImageDraw.Draw(glow)
                g_draw.ellipse([(20, 300), (450, 1100)], fill=theme["glow_primary"])
                glow = glow.filter(ImageFilter.GaussianBlur(60))
                canvas.alpha_composite(glow)

                canvas.alpha_composite(p_img, (-40, 260))
            except Exception as e:
                print(f"Stats action photo error: {e}")

        # 2. Broadcast Card on Right Side
        card_x = 460
        card_y = 220
        card_w = 570
        card_h = 1220

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
            [(card_x, card_y), (card_x + card_w, card_y + 160)],
            radius=24,
            fill=theme["bg_card_header"]
        )
        canvas.alpha_composite(panel)

        # 3. Card Typography & Statistics
        draw = ImageDraw.Draw(canvas)
        font_title = cls.get_font(48, weight="bold")
        font_sub = cls.get_font(26, weight="semi")
        draw.text((card_x + 36, card_y + 26), "Sensational Kohli", font=font_title, fill=theme["text_white"])
        draw.text((card_x + 36, card_y + 88), "World Record Stats in ODI Cricket", font=font_sub, fill=theme["text_muted"])

        # Accent divider
        draw.line([(card_x + 36, card_y + 158), (card_x + card_w - 36, card_y + 158)], fill=theme["accent_primary"], width=4)

        stats = [
            {"label": "CENTURIES", "value": "50", "highlight": True},
            {"label": "INNINGS TAKEN", "value": "279", "sub": "Fastest in 147 Yrs"},
            {"label": "CHASE RUNS", "value": "7,794", "sub": "Average 65.4"},
            {"label": "CHASE 100s", "value": "27", "highlight": True},
            {"label": "CAREER AVERAGE", "value": "58.67", "sub": "Highest in Era"},
        ]

        font_lbl = cls.get_font(24, weight="semi")
        font_val = cls.get_font(68, weight="bold")
        font_note = cls.get_font(22, weight="regular")

        row_y = card_y + 185
        spacing = (card_h - 280) / len(stats)

        for i, s in enumerate(stats):
            cy = int(row_y + i * spacing)
            if s.get("highlight"):
                draw.rounded_rectangle(
                    [(card_x + 20, cy - 6), (card_x + card_w - 20, cy + 96)],
                    radius=12,
                    fill=(theme["accent_primary"][0], theme["accent_primary"][1], theme["accent_primary"][2], 40),
                    outline=theme["accent_gold"],
                    width=1
                )

            draw.text((card_x + 36, cy + 6), s["label"].upper(), font=font_lbl, fill=theme["text_muted"])
            val_color = theme["accent_gold"] if s.get("highlight") else theme["text_white"]
            draw.text((card_x + 36, cy + 32), s["value"], font=font_val, fill=val_color)

            if s.get("sub"):
                draw.text((card_x + 220, cy + 54), f"• {s['sub']}", font=font_note, fill=theme["accent_silver"])

            if i < len(stats) - 1:
                draw.line([(card_x + 36, cy + 104), (card_x + card_w - 36, cy + 104)], fill=(255, 255, 255, 25), width=1)

        # Bottom Bar
        bot_y = card_y + card_h - 60
        font_bot = cls.get_font(24, weight="bold")
        draw.text((card_x + 36, bot_y), "#CWC23", font=font_bot, fill=theme["text_muted"])
        draw.text((card_x + 190, bot_y), "CRICKET RAAZ", font=font_bot, fill=theme["accent_gold"])
        draw.text((card_x + card_w - 120, bot_y), "INDIA", font=font_bot, fill=theme["accent_primary"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 4: LEADERBOARD (Intense Captaincy Portrait + Zero-Tofu Badges)
    # =========================================================================
    @classmethod
    def create_leaderboard_scene(
        cls,
        theme: Dict[str, Any],
        captain_photo_path: str,
        output_path: str = "output/demo_v3/previews/scene4_leaderboard.png"
    ) -> str:
        """
        Creates modern leaderboard with intense match captain portrait.
        Uses clean typography with ZERO square-box tofu glyphs.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="HISTORIC RANKINGS", badge_text="ICC HALL OF FAME")

        # 1. Player Cutout on Right Side
        if os.path.exists(captain_photo_path):
            try:
                p_img = Image.open(captain_photo_path).convert("RGBA")
                target_h = 1200
                aspect = p_img.width / p_img.height
                target_w = int(target_h * aspect)
                p_img = p_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_l = int(target_w * 0.4)
                for x in range(fade_l):
                    m_arr[:, x] *= (x / fade_l) ** 1.3
                fade_b = 320
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                p_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                px = cls.W - target_w + 30
                py = 320
                canvas.alpha_composite(p_img, (px, py))
            except Exception as e:
                print(f"Leaderboard captain photo error: {e}")

        # 2. Table Section
        draw = ImageDraw.Draw(canvas)
        font_h1 = cls.get_font(68, weight="bold")
        font_h2 = cls.get_font(28, weight="semi")

        draw.text((60, 210), "INTO THE RECORD BOOKS", font=font_h1, fill=theme["text_white"])
        draw.text((64, 290), "MOST CENTURIES IN MEN'S ODI CRICKET*", font=font_h2, fill=theme["text_muted"])

        draw.line([(60, 345), (660, 345)], fill=(255, 255, 255, 60), width=2)

        # Header Columns
        font_col = cls.get_font(24, weight="bold")
        draw.text((70, 365), "#", font=font_col, fill=theme["text_muted"])
        draw.text((120, 365), "PLAYER", font=font_col, fill=theme["text_muted"])
        draw.text((450, 365), "INNS", font=font_col, fill=theme["text_muted"])
        draw.text((570, 365), "100s", font=font_col, fill=theme["text_muted"])

        draw.line([(60, 405), (660, 405)], fill=(255, 255, 255, 40), width=1)

        rows = [
            {"rank": "1", "player": "Virat Kohli", "country": "IND", "inns": "279", "stat": "50", "highlight": True},
            {"rank": "2", "player": "Sachin Tendulkar", "country": "IND", "inns": "452", "stat": "49", "highlight": False},
            {"rank": "3", "player": "Rohit Sharma", "country": "IND", "inns": "262", "stat": "31", "highlight": False},
            {"rank": "4", "player": "Ricky Ponting", "country": "AUS", "inns": "365", "stat": "30", "highlight": False},
            {"rank": "5", "player": "Sanath Jayasuriya", "country": "SL", "inns": "433", "stat": "28", "highlight": False},
        ]

        start_y = 425
        row_height = 110
        font_row_name = cls.get_font(34, weight="bold")
        font_row_country = cls.get_font(24, weight="semi")
        font_row_stat = cls.get_font(42, weight="bold")
        font_badge_txt = cls.get_font(20, weight="bold")

        for i, r in enumerate(rows):
            ry = start_y + i * (row_height + 15)
            if r.get("highlight"):
                # Glowing Row for #1
                draw.rounded_rectangle(
                    [(50, ry - 6), (670, ry + row_height - 6)],
                    radius=16,
                    fill=theme["bg_card"],
                    outline=theme["accent_gold"],
                    width=3
                )
                # Clean zero-tofu badge for #1
                draw.rounded_rectangle([(65, ry + 24), (105, ry + 64)], radius=8, fill=theme["accent_gold"])
                draw.text((75, ry + 30), "1", font=font_row_country, fill=(10, 15, 30))

                draw.text((120, ry + 16), r["player"], font=font_row_name, fill=theme["accent_gold"])
                draw.text((120, ry + 60), f"({r['country']})", font=font_row_country, fill=theme["accent_silver"])
                draw.text((455, ry + 30), r["inns"], font=font_row_country, fill=theme["text_white"])
                draw.text((570, ry + 20), r["stat"], font=font_row_stat, fill=theme["accent_gold"])
            else:
                draw.rounded_rectangle(
                    [(50, ry - 6), (670, ry + row_height - 6)],
                    radius=14,
                    fill=theme["pill_bg"],
                    outline=(255, 255, 255, 30),
                    width=1
                )
                draw.text((75, ry + 30), r["rank"], font=font_row_country, fill=theme["text_muted"])
                draw.text((120, ry + 16), r["player"], font=font_row_name, fill=theme["text_white"])
                draw.text((120, ry + 60), f"({r['country']})", font=font_row_country, fill=theme["text_muted"])
                draw.text((455, ry + 30), r["inns"], font=font_row_country, fill=theme["text_muted"])
                draw.text((570, ry + 22), r["stat"], font=font_row_stat, fill=theme["text_white"])

        # Footnote & callout pill
        font_note = cls.get_font(22, weight="regular")
        draw.text((64, 1180), "*ALL-TIME ICC MEN'S ODI CRICKET RECORDS (AS OF 2026)", font=font_note, fill=theme["text_muted"])

        draw.rounded_rectangle(
            [(60, 1240), (cls.W - 60, 1340)],
            radius=18,
            fill=theme["bg_card"],
            outline=theme["accent_primary"],
            width=2
        )
        font_callout = cls.get_font(28, weight="bold")
        draw.text((90, 1258), "FASTEST TO 50 TONS: 279 INNINGS", font=font_callout, fill=theme["accent_gold"])
        draw.text((90, 1294), "Kohli beat Tendulkar's record in 173 fewer innings!", font=font_note, fill=theme["text_white"])

        canvas.save(output_path, quality=95)
        return output_path

    # =========================================================================
    # SCENE 5: OUTRO & DEBATE (Golden World Cup Trophy & Community Pod)
    # =========================================================================
    @classmethod
    def create_final_reveal_scene(
        cls,
        theme: Dict[str, Any],
        trophy_photo_path: str,
        output_path: str = "output/demo_v3/previews/scene5_final_reveal.png"
    ) -> str:
        """
        Creates climactic outro using authentic ICC Cricket World Cup Golden Trophy.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = cls.create_base_canvas(theme)
        cls.add_broadcast_header(canvas, theme, category="COMMUNITY DEBATE", badge_text="SHARE YOUR OPINION")

        # 1. Golden Trophy Cutout in Center-Right Spotlight
        if os.path.exists(trophy_photo_path):
            try:
                t_img = Image.open(trophy_photo_path).convert("RGBA")
                target_h = 1050
                aspect = t_img.width / t_img.height
                target_w = int(target_h * aspect)
                t_img = t_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

                # Fade edges smoothly
                mask = Image.new("L", (target_w, target_h), 255)
                m_arr = np.array(mask, dtype=np.float32)
                fade_b = 260
                for y in range(target_h - fade_b, target_h):
                    m_arr[y, :] *= ((target_h - 1 - y) / fade_b) ** 1.3
                t_img.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                # Place trophy in right-center
                px = cls.W - target_w - 40
                py = 350
                canvas.alpha_composite(t_img, (px, py))
            except Exception as e:
                print(f"Trophy photo error: {e}")

        # 2. Golden Aura
        aura = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        a_draw = ImageDraw.Draw(aura)
        a_draw.ellipse([(cls.W // 2 - 380, 400), (cls.W // 2 + 380, 1100)], fill=theme["glow_secondary"])
        aura = aura.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(aura)

        draw = ImageDraw.Draw(canvas)
        font_h1 = cls.get_font(56, weight="bold")
        draw.text((70, 230), "THE GREATEST OF ALL TIME?", font=font_h1, fill=theme["accent_gold"])

        # 3. Interactive Debate Pod (Left / Mid Section)
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

        draw.text((pod_x + 40, pod_y + 36), "सवाल आपके लिए", font=font_q_title, fill=theme["accent_primary"])
        draw.line([(pod_x + 40, pod_y + 100), (pod_x + pod_w - 40, pod_y + 100)], fill=theme["accent_gold"], width=2)

        draw.text((pod_x + 40, pod_y + 130), "क्या कोई बल्लेबाज कभी विराट के 50\nशतकों का महा-रिकॉर्ड तोड़ पाएगा?", font=font_q_hindi, fill=theme["text_white"])
        draw.text((pod_x + 40, pod_y + 250), "Can anyone in modern cricket ever surpass\nKohli's milestone of 50 ODI centuries?", font=font_q_eng, fill=theme["text_muted"])

        # Comment prompt
        draw.rounded_rectangle(
            [(pod_x + 40, pod_y + 400), (pod_x + pod_w - 40, pod_y + 490)],
            radius=20,
            fill=theme["accent_gold"]
        )
        font_prompt = cls.get_font(32, weight="bold")
        draw.text((pod_x + 95, pod_y + 428), "COMMENT YOUR ANSWER BELOW!", font=font_prompt, fill=(10, 15, 30))

        # 4. Subscribe CTA Section
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
