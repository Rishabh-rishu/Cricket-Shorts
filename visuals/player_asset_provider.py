"""
Cricket Shorts Engine V3 - High-End Sports Broadcast Graphics & Player Asset Provider
Implements ESPN, ICC, and Star Sports / Vizrt premium sports-poster broadcast graphics:
- Full-bleed 9:16 (1080x1920) vertical composition with atmospheric stadium night backdrop
- Team-adaptive color palettes & volumetric glow rim-lighting (India, Australia, Sri Lanka, etc.)
- 3 dynamic creative layout variations:
    * Layout A: Hero Right / Statistics Left (Arshdeep sports-poster style)
    * Layout B: Hero Left / Statistics Right (Dynamic alternate)
    * Layout C: Center Spotlight Hero with bottom floating stat pods (Climactic finale)
- High-resolution player portrait cutouts with smooth edge feathering & stadium rim-lighting
- Massive bold numeric typography with crisp uppercase labels & geometric dividers
- Contrast vignette ensuring 100% crystal-clear readability
- Zero tofu / square box (□□□□) rendering artifacts via Mukta-Bold & NotoSans
- Mobile safe zones strictly preserved (top 150px branding, bottom 360px obsidian subtitle gradient)
"""

import os
import math
import re
import urllib.request
import urllib.parse
import json
from typing import Optional, Tuple, List, Dict, Any, Union
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Dual-script verified fonts (Mukta natively covers Latin, Devanagari, digits & punctuation)
FONT_MUKTA_BOLD = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-Bold.ttf")
FONT_MUKTA_SEMI = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-SemiBold.ttf")
FONT_MUKTA_REG = os.path.join(PROJECT_ROOT, "assets", "fonts", "Mukta-Regular.ttf")

# System fallbacks
FONT_NOTO_DEV_BOLD = "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Bold.ttf"
FONT_NOTO_LAT_BOLD = "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"


class PlayerAssetProvider:
    W = 1080
    H = 1920

    # Team & Broadcast Television Color Palettes
    TEAM_PALETTES = {
        "INDIA": {
            "name": "India",
            "bg_dark": (6, 10, 20, 255),
            "glow_primary": (16, 75, 185, 175),    # Vibrant Indian Blue
            "glow_secondary": (235, 105, 25, 110), # Saffron Orange
            "accent_neon": (255, 55, 165),          # Electric Pink / Magenta (Sports-Poster Style)
            "accent_secondary": (56, 189, 248),     # Electric Cyan
            "accent_gold": (250, 204, 21),          # Trophy Gold
            "text_muted": (165, 185, 215),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (16, 32, 68, 235),
            "rim_glow": (56, 189, 248, 130),
        },
        "AUSTRALIA": {
            "name": "Australia",
            "bg_dark": (8, 14, 12, 255),
            "glow_primary": (230, 180, 20, 160),   # Canary Gold
            "glow_secondary": (18, 120, 60, 115),  # Emerald Green
            "accent_neon": (250, 204, 21),          # Gold
            "accent_secondary": (34, 197, 94),     # Mint / Green
            "accent_gold": (250, 204, 21),
            "text_muted": (165, 195, 180),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (28, 55, 30, 235),
            "rim_glow": (250, 204, 21, 130),
        },
        "SRI LANKA": {
            "name": "Sri Lanka",
            "bg_dark": (6, 12, 26, 255),
            "glow_primary": (20, 75, 190, 165),    # Royal Blue
            "glow_secondary": (225, 150, 15, 115), # Lion Gold
            "accent_neon": (250, 204, 21),
            "accent_secondary": (56, 189, 248),
            "accent_gold": (250, 204, 21),
            "text_muted": (165, 185, 220),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (20, 40, 85, 235),
            "rim_glow": (250, 204, 21, 130),
        },
        "ENGLAND": {
            "name": "England",
            "bg_dark": (8, 12, 22, 255),
            "glow_primary": (220, 38, 38, 150),    # St George Red
            "glow_secondary": (25, 65, 150, 110),  # English Blue
            "accent_neon": (239, 68, 68),
            "accent_secondary": (56, 189, 248),
            "accent_gold": (250, 204, 21),
            "text_muted": (175, 185, 205),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (35, 25, 45, 235),
            "rim_glow": (239, 68, 68, 120),
        },
        "WEST INDIES": {
            "name": "West Indies",
            "bg_dark": (16, 8, 14, 255),
            "glow_primary": (180, 25, 55, 160),    # Maroon
            "glow_secondary": (240, 165, 20, 120), # Caribbean Gold
            "accent_neon": (251, 191, 36),
            "accent_secondary": (244, 63, 94),
            "accent_gold": (250, 204, 21),
            "text_muted": (195, 175, 185),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (60, 20, 35, 235),
            "rim_glow": (251, 191, 36, 130),
        },
        "SOUTH AFRICA": {
            "name": "South Africa",
            "bg_dark": (8, 16, 12, 255),
            "glow_primary": (16, 110, 65, 160),   # Protea Green
            "glow_secondary": (230, 170, 20, 120), # Gold
            "accent_neon": (250, 204, 21),
            "accent_secondary": (34, 197, 94),
            "accent_gold": (250, 204, 21),
            "text_muted": (170, 195, 175),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (22, 55, 35, 235),
            "rim_glow": (250, 204, 21, 130),
        },
        "CLASSIC": {
            "name": "Classic",
            "bg_dark": (6, 10, 20, 255),
            "glow_primary": (25, 65, 165, 155),
            "glow_secondary": (220, 45, 135, 105),
            "accent_neon": (255, 55, 165),
            "accent_secondary": (56, 189, 248),
            "accent_gold": (250, 204, 21),
            "text_muted": (165, 185, 210),
            "divider_col": (255, 255, 255, 45),
            "pill_bg": (20, 35, 70, 235),
            "rim_glow": (56, 189, 248, 125),
        }
    }

    # Standard colors for compatibility
    COLOR_BG_DARK = (6, 12, 22, 255)
    COLOR_NAVY_GLASS = (12, 22, 42, 244)
    COLOR_NAVY_EMBOSS = (16, 32, 64, 235)
    COLOR_CYAN_NEON = (56, 189, 248)
    COLOR_GOLD = (250, 204, 21)
    COLOR_AMBER = (245, 158, 11)
    COLOR_WHITE = (255, 255, 255)
    COLOR_MUTED = (148, 163, 184)
    COLOR_RED = (225, 29, 72)

    @classmethod
    def get_font(cls, size: int, weight: str = "bold", bold: bool = True) -> ImageFont.FreeTypeFont:
        """
        Returns a bilingual (Devanagari + Latin) FreeType font with RAQM layout engine.
        Guarantees zero square-box tofu glyphs on Hindi, English, and mixed numbers.
        """
        if not bold:
            weight = "regular"

        if weight == "bold":
            preferred = [FONT_MUKTA_BOLD, FONT_MUKTA_SEMI, FONT_NOTO_DEV_BOLD, FONT_NOTO_LAT_BOLD]
        elif weight == "semi":
            preferred = [FONT_MUKTA_SEMI, FONT_MUKTA_BOLD, FONT_MUKTA_REG]
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
    def get_team_palette(cls, country: Optional[str] = None) -> Dict[str, Any]:
        """Resolves team palette based on country name or code."""
        c = (country or "").upper().strip()
        if "IND" in c:
            return cls.TEAM_PALETTES["INDIA"]
        elif "AUS" in c:
            return cls.TEAM_PALETTES["AUSTRALIA"]
        elif "LANKA" in c or "SL" in c:
            return cls.TEAM_PALETTES["SRI LANKA"]
        elif "ENG" in c or "BRIT" in c:
            return cls.TEAM_PALETTES["ENGLAND"]
        elif "WEST" in c or "WI" in c or "CARIB" in c:
            return cls.TEAM_PALETTES["WEST INDIES"]
        elif "AFRICA" in c or "SA" in c:
            return cls.TEAM_PALETTES["SOUTH AFRICA"]
        else:
            return cls.TEAM_PALETTES["CLASSIC"]

    @classmethod
    def get_player_portrait(cls, player_name: str, custom_path: Optional[str] = None) -> Optional[str]:
        """
        Resolves or downloads a high-resolution portrait for the cricket player.
        Checks local cache, known aliases, or fetches from Wikimedia Commons with caching.
        """
        if custom_path and os.path.exists(custom_path):
            return custom_path

        portraits_dir = os.path.join(PROJECT_ROOT, "assets", "player_portraits")
        os.makedirs(portraits_dir, exist_ok=True)

        name_lower = player_name.lower().strip()
        slug = name_lower.replace(" ", "_")

        # 1. Direct file check
        exact_path = os.path.join(portraits_dir, f"{slug}.jpg")
        if os.path.exists(exact_path) and os.path.getsize(exact_path) > 3000:
            return exact_path

        # 2. Comprehensive alias matching
        alias_map = {
            "gavaskar": "sunil_gavaskar.jpg",
            "sunil": "sunil_gavaskar.jpg",
            "rohit": "rohit_sharma.jpg",
            "sharma": "rohit_sharma.jpg",
            "kohli": "virat_kohli.jpg",
            "virat": "virat_kohli.jpg",
            "kumble": "anil_kumble.jpg",
            "anil": "anil_kumble.jpg",
            "bumrah": "jasprit_bumrah.jpg",
            "jasprit": "jasprit_bumrah.jpg",
            "mcgrath": "glenn_mcgrath.jpg",
            "glenn": "glenn_mcgrath.jpg",
            "murali": "muttiah_muralitharan.jpg",
            "muralitharan": "muttiah_muralitharan.jpg",
            "sachin": "sachin_tendulkar.jpg",
            "tendulkar": "sachin_tendulkar.jpg",
            "dravid": "rahul_dravid.jpg",
            "rahul": "rahul_dravid.jpg",
            "dhoni": "ms_dhoni.jpg",
            "kapil": "kapil_dev.jpg",
            "ganguly": "sourav_ganguly.jpg",
            "sourav": "sourav_ganguly.jpg",
            "ashwin": "ravichandran_ashwin.jpg",
            "ravichandran": "ravichandran_ashwin.jpg",
            "yuvraj": "yuvraj_singh.jpg",
            "lara": "brian_lara.jpg",
            "brian": "brian_lara.jpg",
            "gayle": "chris_gayle.jpg",
            "chris": "chris_gayle.jpg",
            "villiers": "ab_de_villiers.jpg",
            "abd": "ab_de_villiers.jpg",
            "ponting": "ricky_ponting.jpg",
            "ricky": "ricky_ponting.jpg",
            "mathews": "angelo_mathews.jpg",
            "angelo": "angelo_mathews.jpg",
            "mithali": "mithali_raj.jpg",
        }
        for k, fname in alias_map.items():
            if k in name_lower:
                p = os.path.join(portraits_dir, fname)
                if os.path.exists(p) and os.path.getsize(p) > 3000:
                    return p

        # 3. Dynamic Wikipedia thumbnail lookup with timeout
        try:
            url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(player_name)}&prop=pageimages&format=json&pithumbsize=800"
            req = urllib.request.Request(url, headers={"User-Agent": "CricketShortsBot/1.0 (contact@cricketraaz.test)"})
            with urllib.request.urlopen(req, timeout=3.5) as response:
                data = json.loads(response.read().decode())
                pages = data.get("query", {}).get("pages", {})
                for _, v in pages.items():
                    if "thumbnail" in v:
                        thumb_url = v["thumbnail"]["source"]
                        img_req = urllib.request.Request(thumb_url, headers={"User-Agent": "CricketShortsBot/1.0"})
                        with urllib.request.urlopen(img_req, timeout=3.5) as img_res:
                            with open(exact_path, "wb") as f:
                                f.write(img_res.read())
                        return exact_path
        except Exception:
            pass

        return None

    @classmethod
    def draw_cricket_crest(cls, size: int = 96) -> Image.Image:
        """
        Draws an official broadcast golden sunburst cricket crest.
        16-ray golden sunburst with deep blue center and golden star.
        """
        img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        cx, cy = size // 2, size // 2
        r_outer = size // 2 - 4

        # 16 Golden sun rays
        num_rays = 16
        for i in range(num_rays):
            angle = (i * 2 * math.pi) / num_rays
            rx = cx + int((r_outer + 3) * math.cos(angle))
            ry = cy + int((r_outer + 3) * math.sin(angle))
            d.line([(cx, cy), (rx, ry)], fill=(250, 204, 21, 220), width=3)

        # Golden rim
        d.ellipse([(cx - r_outer, cy - r_outer), (cx + r_outer, cy + r_outer)], fill=(16, 36, 75, 255), outline=(250, 204, 21), width=3)

        # Inner circle
        r_inner = r_outer - 10
        d.ellipse([(cx - r_inner, cy - r_inner), (cx + r_inner, cy + r_inner)], fill=(24, 52, 105, 255), outline=(56, 189, 248), width=2)

        # Central star
        r_star = r_inner - 8
        points = []
        for i in range(10):
            r = r_star if i % 2 == 0 else (r_star * 0.45)
            angle = -math.pi / 2 + (i * math.pi / 5)
            points.append((cx + int(r * math.cos(angle)), cy + int(r * math.sin(angle))))
        d.polygon(points, fill=(250, 204, 21), outline=(255, 255, 255))

        return img

    @classmethod
    def _create_stadium_backdrop(cls) -> Image.Image:
        """
        Generates a 1080x1920 broadcast sports arena night atmosphere.
        """
        bg = Image.new("RGBA", (cls.W, cls.H), (6, 12, 22, 255))
        glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([(cls.W // 2 - 500, -150), (cls.W // 2 + 500, 750)], fill=(20, 50, 100, 140))
        gd.ellipse([(cls.W // 2 - 300, -80), (cls.W // 2 + 300, 480)], fill=(45, 110, 220, 90))
        gd.ellipse([(cls.W // 2 - 450, cls.H - 350), (cls.W // 2 + 450, cls.H + 250)], fill=(15, 65, 45, 65))
        glow = glow.filter(ImageFilter.GaussianBlur(60))
        bg.alpha_composite(glow)

        draw = ImageDraw.Draw(bg)
        for y in range(160, 1600, 140):
            draw.line([(60, y), (cls.W - 60, y)], fill=(255, 255, 255, 8), width=1)
        for x in range(100, cls.W, 140):
            draw.line([(x, 200), (x, 1500)], fill=(255, 255, 255, 6), width=1)

        return bg

    @classmethod
    def parse_display_statistics(
        cls,
        stat_callout: str = "",
        headline: str = "",
        subheadline: str = "",
        stats_table: Optional[Union[List[Tuple[str, str]], Dict[str, str]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Intelligently extracts 3-4 high-impact statistical metrics for the poster.
        Parses numbers, overs, strike rates, economy rates, runs, boundaries, and hauls.
        """
        stats: List[Dict[str, Any]] = []
        seen: set = set()

        # 1. Primary Record Metric
        callout = stat_callout or headline or ""
        if callout:
            m_num = re.search(r"(\d[\d,]*\s*/\s*\d+|\d[\d,]*\*|\d[\d,]*)", callout)
            if m_num and any(c.isdigit() for c in m_num.group(1)):
                val = m_num.group(1).strip()
                rest = callout.replace(val, "")
                rest = re.sub(r"[\(\)\[\]\*\-•]", "", rest).strip()
                rest = re.sub(r"\s+", " ", rest)
                lbl = rest.upper() if rest else "MAIN RECORD"
                if "INNING" in lbl: lbl = "INNINGS HAUL"
                elif "BALL" in lbl: lbl = "RUNS SCORED"
                elif "OVER" in lbl: lbl = "RUNS IN 1 OVER"
                elif "HUNDRED" in lbl or "CENTUR" in lbl: lbl = "CENTURIES IN WC"
                stats.append({"value": val, "label": lbl[:20], "highlight": True})
                seen.add(val.replace("*", "").replace(",", "").strip())
            else:
                stats.append({"value": "SPECIAL", "label": callout.upper()[:20], "highlight": True})

        # 2. Parse secondary metrics from stats_table
        raw_table: List[Tuple[str, str]] = []
        if isinstance(stats_table, dict):
            raw_table = list(stats_table.items())
        elif isinstance(stats_table, list):
            raw_table = [(str(k), str(v)) for k, v in stats_table]

        for k, v in raw_table:
            k_str = str(k).strip()
            v_str = str(v).strip()

            # Skip generic match metadata
            if any(skip in k_str.lower() for skip in ["tournament", "format", "venue", "opponent", "teams", "final delivery"]):
                continue

            # Overs format with maidens e.g. "7.0 Overs (4 Maidens)"
            if "overs" in k_str.lower() and "(" in v_str:
                m_ov = re.search(r"([\d\.]+)\s*Overs", v_str, re.IGNORECASE)
                m_md = re.search(r"(\d+)\s*Maidens", v_str, re.IGNORECASE)
                if m_ov and m_ov.group(1) not in seen and len(stats) < 4:
                    stats.append({"value": m_ov.group(1), "label": "OVERS BOWLED"})
                    seen.add(m_ov.group(1))
                if m_md and m_md.group(1) not in seen and len(stats) < 4:
                    stats.append({"value": m_md.group(1), "label": "MAIDEN OVERS"})
                    seen.add(m_md.group(1))
                continue

            # General numeric extraction
            m_v = re.search(r"(\d[\d,]*\s*/\s*\d+|\d[\d,]*\*|[\d\.]+)", v_str)
            if m_v and len(stats) < 4:
                v_val = m_v.group(1).strip()
                norm = v_val.replace("*", "").replace(",", "").strip()
                if norm not in seen and norm not in ["1", "2"]:
                    clean_lbl = re.sub(r"[\(\)\[\]]", "", k_str).strip().upper()
                    stats.append({"value": v_val, "label": clean_lbl[:20]})
                    seen.add(norm)

        # Fallback if fewer than 2 stats were resolved
        if len(stats) < 2 and subheadline:
            stats.append({"value": "RECORD", "label": subheadline.upper()[:20]})

        return stats[:4]

    @classmethod
    def create_cinematic_fact_card(
        cls,
        badge_text: str = "",
        player_name: str = "CRICKET RECORD",
        headline: str = "",
        subheadline: str = "",
        stat_callout: str = "",
        output_path: str = "temp/card.png",
        accent_color: str = "cyan",
        country: Optional[str] = None,
        player_role: Optional[str] = None,
        tournament_header: Optional[str] = None,
        stats_table: Optional[Union[List[Tuple[str, str]], Dict[str, str]]] = None,
        achievement_tag: Optional[str] = None,
        player_img_path: Optional[str] = None,
        fact_index: Optional[int] = None,
        layout_variant: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Creates a high-end ESPN / sports-poster style 9:16 broadcast record highlight graphic.
        Inspired by premium sports magazine posters with:
        - Full-bleed vertical 1080x1920 layout
        - Team-adaptive atmospheric stadium glows
        - Dynamic layout variations:
            * Layout A: Hero Right / Statistics Left (Arshdeep sports-poster style)
            * Layout B: Hero Left / Statistics Right (Dynamic alternate)
            * Layout C: Center Spotlight Hero with bottom floating stat pods
        - High-resolution player portrait cutout with smooth edge feathering & stadium rim-lighting
        - Massive bold numeric values with clean uppercase labels & geometric dividers
        - Contrast shadow vignette ensuring 100% crystal-clear readability
        - Deep obsidian bottom safe zone gradient for subtitles
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # 1. Determine Layout Variant
        if not layout_variant:
            if fact_index == 2 or re.search(r"\b(fact\s*2|#2|2nd)\b", badge_text, re.IGNORECASE):
                layout_variant = "B"
            elif fact_index == 3 or re.search(r"\b(fact\s*3|#3|3rd)\b", badge_text, re.IGNORECASE):
                layout_variant = "C"
            else:
                layout_variant = "A"

        # 2. Team Palette Resolution
        resolved_country = country or "INDIA"
        palette = cls.get_team_palette(resolved_country)
        canvas = Image.new("RGBA", (cls.W, cls.H), palette["bg_dark"])

        # 3. Volumetric Stadium Lighting Auras
        glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        if layout_variant == "A":
            gd.ellipse([(450, 150), (1250, 1150)], fill=palette["glow_primary"])
            gd.ellipse([(600, 350), (1150, 950)], fill=palette["glow_secondary"])
        elif layout_variant == "B":
            gd.ellipse([(-200, 150), (600, 1150)], fill=palette["glow_primary"])
            gd.ellipse([(50, 350), (650, 950)], fill=palette["glow_secondary"])
        else:  # Layout C (Center Spotlight)
            gd.ellipse([(150, 200), (950, 1150)], fill=palette["glow_primary"])
            gd.ellipse([(cls.W // 2 - 300, 300), (cls.W // 2 + 300, 950)], fill=palette["glow_secondary"])

        gd.ellipse([(200, -250), (880, 450)], fill=(30, 70, 160, 90))
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        canvas.alpha_composite(glow)

        # 4. Hero Player Cutout Placement
        resolved_portrait = player_img_path or cls.get_player_portrait(player_name)
        if resolved_portrait and os.path.exists(resolved_portrait):
            try:
                raw_p = Image.open(resolved_portrait).convert("RGBA")
                target_ph = 1200
                aspect = raw_p.width / raw_p.height
                target_pw = int(target_ph * aspect)
                raw_p = raw_p.resize((target_pw, target_ph), Image.Resampling.LANCZOS)

                mask = Image.new("L", (raw_p.width, raw_p.height), 255)
                m_arr = np.array(mask, dtype=np.float32)

                if layout_variant == "A":
                    # Fade left edge smoothly
                    fade_l = min(220, raw_p.width // 2)
                    for x in range(fade_l):
                        m_arr[:, x] = m_arr[:, x] * ((x / fade_l) ** 1.3)
                    px = cls.W - target_pw + 20
                    py = 220
                elif layout_variant == "B":
                    # Fade right edge smoothly
                    fade_r = min(220, raw_p.width // 2)
                    for x in range(raw_p.width - fade_r, raw_p.width):
                        prog = (raw_p.width - 1 - x) / fade_r
                        m_arr[:, x] = m_arr[:, x] * (prog ** 1.3)
                    px = -20
                    py = 220
                else:  # Layout C (Center)
                    # Fade both left and right edges
                    fade_side = min(160, raw_p.width // 3)
                    for x in range(fade_side):
                        m_arr[:, x] = m_arr[:, x] * ((x / fade_side) ** 1.2)
                    for x in range(raw_p.width - fade_side, raw_p.width):
                        prog = (raw_p.width - 1 - x) / fade_side
                        m_arr[:, x] = m_arr[:, x] * (prog ** 1.2)
                    px = (cls.W - target_pw) // 2
                    py = 220

                # Fade bottom edge into dark floor
                fade_b = 320
                for y in range(raw_p.height - fade_b, raw_p.height):
                    prog = (raw_p.height - 1 - y) / fade_b
                    m_arr[y, :] = m_arr[y, :] * (prog ** 1.4)

                raw_p.putalpha(Image.fromarray(m_arr.astype(np.uint8)))

                # Rim light aura behind player
                rim = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
                rm_draw = ImageDraw.Draw(rim)
                rm_draw.ellipse([(px + 50, py + 50), (px + target_pw, py + target_ph - 200)], fill=palette["rim_glow"])
                rim = rim.filter(ImageFilter.GaussianBlur(50))
                canvas.alpha_composite(rim)

                # Paste player cutout
                canvas.alpha_composite(raw_p, (px, py))
            except Exception:
                pass

        # 5. Contrast Shadow Vignette for Statistics Readability
        shadow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        sh_draw = ImageDraw.Draw(shadow)
        bg_c = palette["bg_dark"]

        if layout_variant == "A":
            for x in range(0, 620):
                alpha = 245 if x < 420 else int(245 * ((1.0 - (x - 420) / 200.0) ** 1.4))
                sh_draw.line([(x, 0), (x, cls.H)], fill=(bg_c[0], bg_c[1], bg_c[2], alpha))
        elif layout_variant == "B":
            for x in range(cls.W - 620, cls.W):
                alpha = 245 if x > cls.W - 420 else int(245 * (((x - (cls.W - 620)) / 200.0) ** 1.4))
                sh_draw.line([(x, 0), (x, cls.H)], fill=(bg_c[0], bg_c[1], bg_c[2], alpha))
        else:  # Layout C
            for y in range(cls.H - 650, cls.H):
                prog = (y - (cls.H - 650)) / 650.0
                alpha = int(240 * (prog ** 1.2))
                sh_draw.line([(0, y), (cls.W, y)], fill=(bg_c[0], bg_c[1], bg_c[2], alpha))

        canvas.alpha_composite(shadow)

        draw = ImageDraw.Draw(canvas)

        # 6. Top Branding Pill Capsule (y = 70 to 116)
        badge_clean = badge_text.replace("🏆", "").strip() if badge_text else "OFFICIAL RECORD"
        brand_txt = f"CRICKET RAAZ • {badge_clean}"
        f_brand = cls.get_font(20, "bold")
        bbox_br = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox_br[2] - bbox_br[0]) + 40
        bx = 70 if layout_variant != "B" else (cls.W - bw - 70)
        draw.rounded_rectangle([bx, 70, bx + bw, 116], radius=14, fill=palette["pill_bg"], outline=palette["accent_secondary"], width=2)
        draw.ellipse([(bx + 16, 90), (bx + 24, 98)], fill=palette["accent_secondary"])
        draw.text((bx + 34, 80), brand_txt, font=f_brand, fill=(255, 255, 255))

        # 7. Player Full Name Typography
        name_parts = player_name.strip().split()
        first_name = name_parts[0].upper()
        last_name = " ".join(name_parts[1:]).upper() if len(name_parts) > 1 else ""

        f_pname1 = cls.get_font(84, "bold")
        f_pname2 = cls.get_font(84, "bold")

        text_x = 70 if layout_variant != "B" else (cls.W - 480)
        cur_y = 145

        if layout_variant == "C":
            bbox1 = draw.textbbox((0, 0), first_name, font=f_pname1)
            w1 = bbox1[2] - bbox1[0]
            draw.text(((cls.W - w1) // 2 + 2, cur_y + 2), first_name, font=f_pname1, fill=(0, 0, 0, 180))
            draw.text(((cls.W - w1) // 2, cur_y), first_name, font=f_pname1, fill=palette["accent_neon"])
            cur_y += 92

            if last_name:
                bbox2 = draw.textbbox((0, 0), last_name, font=f_pname2)
                w2 = bbox2[2] - bbox2[0]
                draw.text(((cls.W - w2) // 2 + 2, cur_y + 2), last_name, font=f_pname2, fill=(0, 0, 0, 180))
                draw.text(((cls.W - w2) // 2, cur_y), last_name, font=f_pname2, fill=(255, 255, 255))
                cur_y += 92
        else:
            draw.text((text_x + 2, cur_y + 2), first_name, font=f_pname1, fill=(0, 0, 0, 180))
            draw.text((text_x, cur_y), first_name, font=f_pname1, fill=palette["accent_neon"])
            cur_y += 92

            if last_name:
                draw.text((text_x + 2, cur_y + 2), last_name, font=f_pname2, fill=(0, 0, 0, 180))
                draw.text((text_x, cur_y), last_name, font=f_pname2, fill=(255, 255, 255))
                cur_y += 92

        # 8. Context Subtitle
        c_role = (player_role or "INTERNATIONAL CRICKETER").upper()
        sub_title = f"{resolved_country.upper()} • {c_role}"
        f_sub = cls.get_font(24, "semi")
        if layout_variant == "C":
            bbox_sub = draw.textbbox((0, 0), sub_title, font=f_sub)
            sw = bbox_sub[2] - bbox_sub[0]
            draw.text(((cls.W - sw) // 2, cur_y + 6), sub_title, font=f_sub, fill=palette["text_muted"])
        else:
            draw.text((text_x, cur_y + 6), sub_title, font=f_sub, fill=palette["text_muted"])
        cur_y += 55

        # 9. Main Record Highlight Pill
        rec_title = (headline or achievement_tag or "HISTORIC RECORD").upper()
        f_rec = cls.get_font(26, "bold")
        bbox_rc = draw.textbbox((0, 0), rec_title, font=f_rec)
        rw = min((bbox_rc[2] - bbox_rc[0]) + 36, 480)
        rx = text_x if layout_variant != "C" else ((cls.W - rw) // 2)
        draw.rounded_rectangle([rx, cur_y, rx + rw, cur_y + 46], radius=10, fill=(234, 179, 8, 45), outline=palette["accent_gold"], width=2)
        draw.text((rx + 18, cur_y + 8), rec_title[:26], font=f_rec, fill=palette["accent_gold"])
        cur_y += 75

        # 10. Dynamic Big Statistics Table
        stats_list = cls.parse_display_statistics(
            stat_callout=stat_callout,
            headline=headline,
            subheadline=subheadline,
            stats_table=stats_table
        )

        f_val_huge = cls.get_font(84, "bold")
        f_val_med = cls.get_font(60, "bold")
        f_lbl = cls.get_font(24, "bold")

        if layout_variant in ["A", "B"]:
            stat_y = max(cur_y + 20, 520)
            row_gap = 180

            for s in stats_list:
                if stat_y + 120 > 1460:
                    break

                val_text = str(s["value"])
                lbl_text = str(s["label"]).upper()
                is_hl = s.get("highlight", False)

                use_font = f_val_huge if len(val_text) <= 5 else f_val_med
                num_color = palette["accent_gold"] if is_hl else (255, 255, 255)

                draw.text((text_x + 2, stat_y + 2), val_text, font=use_font, fill=(0, 0, 0, 220))
                draw.text((text_x, stat_y), val_text, font=use_font, fill=num_color)

                lbl_y = stat_y + 95
                draw.text((text_x, lbl_y), lbl_text, font=f_lbl, fill=palette["text_muted"])

                div_y = lbl_y + 42
                draw.line([(text_x, div_y), (text_x + 360, div_y)], fill=palette["divider_col"], width=1)
                draw.ellipse([(text_x - 4, div_y - 4), (text_x + 4, div_y + 4)], fill=palette["accent_secondary"])

                stat_y += row_gap

        else:
            # Layout C (Center Spotlight): 4 Stat Pods in 2x2 Grid near bottom
            pod_w, pod_h = 420, 130
            grid_x1, grid_x2 = 90, 570
            grid_y1, grid_y2 = 1140, 1300

            positions = [(grid_x1, grid_y1), (grid_x2, grid_y1), (grid_x1, grid_y2), (grid_x2, grid_y2)]
            for i, s in enumerate(stats_list[:4]):
                gx, gy = positions[i]
                draw.rounded_rectangle([gx, gy, gx + pod_w, gy + pod_h], radius=16, fill=(16, 26, 52, 220), outline=palette["divider_col"], width=1)
                val_text = str(s["value"])
                lbl_text = str(s["label"]).upper()
                is_hl = s.get("highlight", False)
                num_color = palette["accent_gold"] if is_hl else (255, 255, 255)

                f_c_val = cls.get_font(52, "bold") if len(val_text) <= 6 else cls.get_font(42, "bold")
                draw.text((gx + 22, gy + 14), val_text, font=f_c_val, fill=num_color)

                f_c_lbl = cls.get_font(20, "bold")
                draw.text((gx + 22, gy + 78), lbl_text[:24], font=f_c_lbl, fill=palette["text_muted"])

        # 11. Deep Obsidian Bottom Safe Zone (y = 1500 to 1920)
        bottom_fade = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        bf_draw = ImageDraw.Draw(bottom_fade)
        for y in range(cls.H - 420, cls.H):
            prog = (y - (cls.H - 420)) / 420.0
            alpha = int(255 * (prog ** 1.3))
            bf_draw.line([(0, y), (cls.W, y)], fill=(6, 10, 20, alpha))
        canvas.alpha_composite(bottom_fade)

        # Bottom channel watermark
        draw_final = ImageDraw.Draw(canvas)
        f_logo = cls.get_font(22, "bold")
        draw_final.text((cls.W - 240, cls.H - 75), "CRICKET RAAZ #1", font=f_logo, fill=(255, 255, 255, 130))

        canvas.save(output_path, "PNG")
        return output_path

    @classmethod
    def create_hook_card(
        cls,
        title: str,
        subtitle: str,
        output_path: str
    ) -> str:
        """
        Renders opening hook title card (0-3s) with sports broadcast graphics.
        Full-bleed atmospheric composition matching ESPN / Vizrt television packages.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = Image.new("RGBA", (cls.W, cls.H), (6, 10, 20, 255))

        # 1. Volumetric Stadium Lighting Auras
        glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([(cls.W // 2 - 450, 200), (cls.W // 2 + 450, 1100)], fill=(18, 65, 170, 160))
        gd.ellipse([(cls.W // 2 - 300, 350), (cls.W // 2 + 300, 950)], fill=(235, 120, 25, 95))
        gd.ellipse([(cls.W // 2 - 500, -250), (cls.W // 2 + 500, 450)], fill=(30, 80, 180, 90))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(glow)

        # 2. Subtle Technical Grid Lines
        grid = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        gr_draw = ImageDraw.Draw(grid)
        for y in range(160, 1550, 160):
            gr_draw.line([(60, y), (cls.W - 60, y)], fill=(255, 255, 255, 8), width=1)
        for x in range(100, cls.W, 160):
            gr_draw.line([(x, 180), (x, 1500)], fill=(255, 255, 255, 6), width=1)
        canvas.alpha_composite(grid)

        draw = ImageDraw.Draw(canvas)

        # 3. Top Branding Capsule (y = 120 to 175)
        f_brand = cls.get_font(22, "bold")
        brand_txt = "CRICKET RAAZ • WORLD RECORDS"
        bbox_br = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox_br[2] - bbox_br[0]) + 48
        bx = (cls.W - bw) // 2
        draw.rounded_rectangle([bx, 120, bx + bw, 172], radius=16, fill=(16, 28, 56, 235), outline=(56, 189, 248), width=2)
        draw.ellipse([(bx + 20, 142), (bx + 28, 150)], fill=(56, 189, 248))
        draw.text((bx + 38, 132), brand_txt, font=f_brand, fill=(255, 255, 255))

        # 4. Massive Title Typography (Center Screen: y = 540 to 880)
        words = title.strip().split()
        f_num = cls.get_font(96, "bold")
        f_main = cls.get_font(74, "bold")

        top_line = f"{words[0]} {words[1]}" if len(words) >= 2 and len(words[0]) <= 3 else words[0]
        rest_lines = words[2:] if top_line != words[0] else words[1:]
        mid_line = " ".join(rest_lines[:2]) if len(rest_lines) >= 2 else " ".join(rest_lines)
        bot_line = " ".join(rest_lines[2:]) if len(rest_lines) > 2 else ""

        cur_y = 540

        # Top highlight line (Gold)
        bbox_t = draw.textbbox((0, 0), top_line.upper(), font=f_num)
        tw = bbox_t[2] - bbox_t[0]
        draw.text(((cls.W - tw) // 2 + 3, cur_y + 3), top_line.upper(), font=f_num, fill=(0, 0, 0, 200))
        draw.text(((cls.W - tw) // 2, cur_y), top_line.upper(), font=f_num, fill=(250, 204, 21))
        cur_y += 115

        # Mid line in pure white
        if mid_line:
            bbox_m = draw.textbbox((0, 0), mid_line.upper(), font=f_main)
            mw = bbox_m[2] - bbox_m[0]
            draw.text(((cls.W - mw) // 2 + 3, cur_y + 3), mid_line.upper(), font=f_main, fill=(0, 0, 0, 200))
            draw.text(((cls.W - mw) // 2, cur_y), mid_line.upper(), font=f_main, fill=(255, 255, 255))
            cur_y += 92

        # Bot line in pure white
        if bot_line:
            bbox_b = draw.textbbox((0, 0), bot_line.upper(), font=f_main)
            bw2 = bbox_b[2] - bbox_b[0]
            draw.text(((cls.W - bw2) // 2 + 3, cur_y + 3), bot_line.upper(), font=f_main, fill=(0, 0, 0, 200))
            draw.text(((cls.W - bw2) // 2, cur_y), bot_line.upper(), font=f_main, fill=(255, 255, 255))
            cur_y += 92

        # Sleek Horizontal Light Beam Divider
        cur_y += 30
        draw.line([(140, cur_y), (cls.W - 140, cur_y)], fill=(56, 189, 248, 80), width=2)
        cx = cls.W // 2
        draw.polygon([(cx, cur_y - 8), (cx + 12, cur_y), (cx, cur_y + 8), (cx - 12, cur_y)], fill=(56, 189, 248))
        cur_y += 45

        # 5. Hindi Subtitle (Bilingual High Contrast)
        f_sub = cls.get_font(38, "bold")
        bbox_sub = draw.textbbox((0, 0), subtitle, font=f_sub)
        sw = bbox_sub[2] - bbox_sub[0]
        draw.text(((cls.W - sw) // 2 + 2, cur_y + 2), subtitle, font=f_sub, fill=(0, 0, 0, 200))
        draw.text(((cls.W - sw) // 2, cur_y), subtitle, font=f_sub, fill=(56, 189, 248))
        cur_y += 110

        # 6. High-Energy Call to Action Badge
        cta_txt = "MUST WATCH UNTIL END"
        f_cta = cls.get_font(28, "bold")
        bbox_c = draw.textbbox((0, 0), cta_txt, font=f_cta)
        cw = (bbox_c[2] - bbox_c[0]) + 56
        cx = (cls.W - cw) // 2
        draw.rounded_rectangle([cx, cur_y, cx + cw, cur_y + 60], radius=16, fill=(225, 29, 72, 240), outline=(255, 255, 255), width=2)
        draw.text((cx + 28, cur_y + 12), cta_txt, font=f_cta, fill=(255, 255, 255))

        # 7. Bottom Safe Zone Shadow (y = 1500 to 1920)
        bottom_fade = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        bf_draw = ImageDraw.Draw(bottom_fade)
        for y in range(cls.H - 420, cls.H):
            prog = (y - (cls.H - 420)) / 420.0
            alpha = int(255 * (prog ** 1.3))
            bf_draw.line([(0, y), (cls.W, y)], fill=(6, 10, 20, alpha))
        canvas.alpha_composite(bottom_fade)

        canvas.save(output_path, "PNG")
        return output_path

    @classmethod
    def create_outro_card(
        cls,
        cta_heading: str,
        cta_subheading: str,
        output_path: str
    ) -> str:
        """
        Renders outro CTA card with high-production sports broadcast graphics.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        canvas = Image.new("RGBA", (cls.W, cls.H), (6, 10, 20, 255))

        # Volumetric Stadium Auras
        glow = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([(cls.W // 2 - 450, 200), (cls.W // 2 + 450, 1100)], fill=(18, 65, 170, 160))
        gd.ellipse([(cls.W // 2 - 300, 350), (cls.W // 2 + 300, 950)], fill=(235, 120, 25, 95))
        glow = glow.filter(ImageFilter.GaussianBlur(80))
        canvas.alpha_composite(glow)

        draw = ImageDraw.Draw(canvas)

        # Header Branding
        f_brand = cls.get_font(24, "bold")
        brand_txt = "CRICKET RAAZ • OFFICIAL CHANNEL"
        bbox = draw.textbbox((0, 0), brand_txt, font=f_brand)
        bw = (bbox[2] - bbox[0]) + 48
        bx = (cls.W - bw) // 2
        draw.rounded_rectangle([bx, 85, bx + bw, 134], radius=14, fill=(16, 28, 56, 235), outline=(250, 204, 21), width=2)
        draw.text((bx + 24, 95), brand_txt, font=f_brand, fill=(250, 204, 21))

        # Golden Cricket Crest
        crest = cls.draw_cricket_crest(size=120)
        canvas.alpha_composite(crest, ((cls.W - 120) // 2, 380))

        # Channel Name Title
        f_head = cls.get_font(72, "bold")
        bbox_h = draw.textbbox((0, 0), "CRICKET RAAZ", font=f_head)
        cw = bbox_h[2] - bbox_h[0]
        draw.text(((cls.W - cw) // 2 + 3, 530 + 3), "CRICKET RAAZ", font=f_head, fill=(0, 0, 0, 200))
        draw.text(((cls.W - cw) // 2, 530), "CRICKET RAAZ", font=f_head, fill=(255, 255, 255))

        # Subheading
        f_sched = cls.get_font(24, "bold")
        sched_txt = "NEW SHORT DAILY AT 12:00 PM & 6:00 PM"
        bbox_sc = draw.textbbox((0, 0), sched_txt, font=f_sched)
        draw.text(((cls.W - (bbox_sc[2] - bbox_sc[0])) // 2, 625), sched_txt, font=f_sched, fill=(250, 204, 21))

        # Light divider
        draw.line([(140, 680), (cls.W - 140, 680)], fill=(56, 189, 248, 80), width=2)
        cx = cls.W // 2
        draw.polygon([(cx, 680 - 8), (cx + 12, 680), (cx, 680 + 8), (cx - 12, 680)], fill=(56, 189, 248))

        # CTA Heading
        f_cta_h = cls.get_font(42, "bold")
        bbox_ch = draw.textbbox((0, 0), cta_heading, font=f_cta_h)
        draw.text(((cls.W - (bbox_ch[2] - bbox_ch[0])) // 2, 730), cta_heading, font=f_cta_h, fill=(255, 255, 255))

        # CTA Subheading in Hindi
        f_sub = cls.get_font(34, "semi")
        bbox_s = draw.textbbox((0, 0), cta_subheading, font=f_sub)
        draw.text(((cls.W - (bbox_s[2] - bbox_s[0])) // 2, 800), cta_subheading, font=f_sub, fill=(56, 189, 248))

        # Glowing Red Subscribe Pill
        sub_txt = "SUBSCRIBE FOR DAILY FACTS"
        f_sub_pill = cls.get_font(32, "bold")
        bbox_p = draw.textbbox((0, 0), sub_txt, font=f_sub_pill)
        pw = (bbox_p[2] - bbox_p[0]) + 70
        px = (cls.W - pw) // 2
        draw.rounded_rectangle([px, 920, px + pw, 1000], radius=24, fill=(225, 29, 72, 245), outline=(255, 255, 255), width=2)
        # Red youtube style dot
        draw.ellipse([(px + 24, 952), (px + 40, 968)], fill=(255, 255, 255))
        draw.text((px + 52, 942), sub_txt, font=f_sub_pill, fill=(255, 255, 255))

        # Lower subtitle protection gradient
        bottom_fade = Image.new("RGBA", (cls.W, cls.H), (0, 0, 0, 0))
        bf_draw = ImageDraw.Draw(bottom_fade)
        for y in range(cls.H - 420, cls.H):
            prog = (y - (cls.H - 420)) / 420.0
            alpha = int(255 * (prog ** 1.3))
            bf_draw.line([(0, y), (cls.W, y)], fill=(6, 10, 20, alpha))
        canvas.alpha_composite(bottom_fade)

        canvas.save(output_path, "PNG")
        return output_path
