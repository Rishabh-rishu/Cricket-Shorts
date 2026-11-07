"""
Cricket Shorts Engine V3 - Dynamic Sports Broadcast Theme Manager
Provides 6 distinct, high-contrast TV broadcast color palettes for visual variety across videos:
1. CRIMSON_OBSIDIAN (Midnight Obsidian + Crimson Red + Platinum Silver + Trophy Gold)
2. NEON_CYBER (Deep Purple + Electric Cyan + Neon Magenta)
3. ROYAL_EMPIRE (Deep Royal Blue + Canary Gold + Pure White)
4. EMERALD_MASTER (Forest Emerald + Trophy Gold + Ice Mint)
5. CHARCOAL_EMBER (Charcoal Slate + Fire Orange + Warm Amber)
6. MIDNIGHT_NAVY (Midnight Navy + Cyan Neon + Trophy Gold)
"""

from typing import Dict, Any, Tuple


class ThemeManager:
    THEMES: Dict[str, Dict[str, Any]] = {
        "CRIMSON_OBSIDIAN": {
            "name": "Crimson Obsidian",
            "bg_dark": (10, 12, 18, 255),           # Deep midnight obsidian
            "bg_card": (18, 20, 30, 248),           # Card glass dark
            "bg_card_header": (34, 22, 36, 255),    # Card header with subtle crimson tone
            "accent_primary": (225, 29, 72),        # Crimson Red (#E11D48)
            "accent_secondary": (244, 63, 94),      # Rose Crimson
            "accent_gold": (250, 204, 21),          # Trophy Gold (#FACC15)
            "accent_silver": (226, 232, 240),       # Platinum Silver
            "text_white": (255, 255, 255),          # Crisp white
            "text_muted": (160, 174, 192),          # Cool muted slate
            "glow_primary": (190, 18, 60, 85),      # Crimson volumetric glow
            "glow_secondary": (250, 204, 21, 65),   # Golden rim glow
            "border_highlight": (225, 29, 72, 220), # Crimson border
            "pill_bg": (28, 20, 32, 235),
            "tagline_color": (250, 204, 21),        # Gold tagline
        },
        "NEON_CYBER": {
            "name": "Neon Cyber",
            "bg_dark": (8, 10, 24, 255),
            "bg_card": (16, 18, 48, 248),
            "bg_card_header": (28, 22, 78, 255),
            "accent_primary": (56, 189, 248),       # Electric Cyan
            "accent_secondary": (244, 63, 142),     # Magenta / Neon Pink
            "accent_gold": (250, 204, 21),
            "accent_silver": (226, 232, 240),
            "text_white": (255, 255, 255),
            "text_muted": (165, 185, 215),
            "glow_primary": (56, 189, 248, 85),
            "glow_secondary": (244, 63, 142, 65),
            "border_highlight": (56, 189, 248, 220),
            "pill_bg": (16, 24, 56, 235),
            "tagline_color": (56, 189, 248),
        },
        "ROYAL_EMPIRE": {
            "name": "Royal Empire",
            "bg_dark": (6, 14, 32, 255),
            "bg_card": (12, 24, 54, 248),
            "bg_card_header": (18, 36, 80, 255),
            "accent_primary": (250, 204, 21),       # Canary Gold
            "accent_secondary": (56, 189, 248),
            "accent_gold": (250, 204, 21),
            "accent_silver": (241, 245, 249),
            "text_white": (255, 255, 255),
            "text_muted": (175, 195, 225),
            "glow_primary": (0, 75, 185, 95),
            "glow_secondary": (250, 204, 21, 75),
            "border_highlight": (250, 204, 21, 220),
            "pill_bg": (14, 30, 68, 235),
            "tagline_color": (250, 204, 21),
        },
        "EMERALD_MASTER": {
            "name": "Emerald Master",
            "bg_dark": (6, 18, 14, 255),
            "bg_card": (10, 32, 24, 248),
            "bg_card_header": (16, 50, 36, 255),
            "accent_primary": (34, 197, 94),        # Mint Emerald
            "accent_secondary": (250, 204, 21),     # Trophy Gold
            "accent_gold": (250, 204, 21),
            "accent_silver": (226, 232, 240),
            "text_white": (255, 255, 255),
            "text_muted": (165, 200, 180),
            "glow_primary": (16, 120, 65, 90),
            "glow_secondary": (250, 204, 21, 70),
            "border_highlight": (34, 197, 94, 220),
            "pill_bg": (14, 40, 28, 235),
            "tagline_color": (34, 197, 94),
        },
        "CHARCOAL_EMBER": {
            "name": "Charcoal Ember",
            "bg_dark": (14, 14, 18, 255),
            "bg_card": (24, 22, 28, 248),
            "bg_card_header": (42, 30, 32, 255),
            "accent_primary": (249, 115, 22),       # Fire Orange (#F97316)
            "accent_secondary": (250, 204, 21),     # Amber Gold
            "accent_gold": (250, 204, 21),
            "accent_silver": (226, 232, 240),
            "text_white": (255, 255, 255),
            "text_muted": (180, 175, 175),
            "glow_primary": (234, 88, 12, 90),
            "glow_secondary": (250, 204, 21, 65),
            "border_highlight": (249, 115, 22, 220),
            "pill_bg": (36, 26, 24, 235),
            "tagline_color": (249, 115, 22),
        },
        "MIDNIGHT_NAVY": {
            "name": "Midnight Navy",
            "bg_dark": (6, 11, 25, 255),
            "bg_card": (13, 20, 44, 248),
            "bg_card_header": (24, 32, 70, 255),
            "accent_primary": (56, 189, 248),       # Cyan Neon
            "accent_secondary": (244, 63, 142),
            "accent_gold": (250, 204, 21),
            "accent_silver": (226, 232, 240),
            "text_white": (255, 255, 255),
            "text_muted": (165, 185, 215),
            "glow_primary": (0, 75, 185, 95),
            "glow_secondary": (250, 204, 21, 65),
            "border_highlight": (56, 189, 248, 220),
            "pill_bg": (16, 28, 58, 235),
            "tagline_color": (56, 189, 248),
        },
        "CARIBBEAN_MAROON": {
            "name": "Caribbean Maroon",
            "bg_dark": (18, 8, 14, 255),            # Deep mahogany maroon obsidian
            "bg_card": (32, 14, 24, 248),           # Rich maroon glass
            "bg_card_header": (48, 18, 34, 255),    # Card header with deep maroon tone
            "accent_primary": (190, 24, 60),        # West Indies Maroon (#BE183C)
            "accent_secondary": (244, 114, 182),    # Rose Pink
            "accent_gold": (250, 204, 21),          # Trophy Gold (#FACC15)
            "accent_silver": (241, 245, 249),       # Platinum White
            "text_white": (255, 255, 255),          # Crisp white
            "text_muted": (195, 175, 185),          # Cool muted rose
            "glow_primary": (180, 24, 54, 90),      # Maroon volumetric glow
            "glow_secondary": (250, 204, 21, 70),   # Golden rim glow
            "border_highlight": (190, 24, 60, 220), # Maroon border
            "pill_bg": (34, 16, 28, 235),
            "tagline_color": (250, 204, 21),        # Gold tagline
        }
    }

    @classmethod
    def get_theme(cls, theme_name: str = "CRIMSON_OBSIDIAN") -> Dict[str, Any]:
        """Returns color palette for requested theme name."""
        return cls.THEMES.get(theme_name.upper(), cls.THEMES["CRIMSON_OBSIDIAN"])

    @classmethod
    def rotate_theme(cls, video_index: int) -> Dict[str, Any]:
        """Automatically rotates themes deterministically across successive video generations."""
        keys = list(cls.THEMES.keys())
        selected_key = keys[video_index % len(keys)]
        return cls.THEMES[selected_key]

    @classmethod
    def get_theme_for_topic(cls, topic: str, fallback_idx: int = 0) -> Dict[str, Any]:
        """
        Selects the best matching broadcast theme based on format, player, or topic,
        falling back to deterministic rotation across videos.
        """
        import re
        t = topic.lower()
        def has_word(words):
            return any(re.search(r'\b' + re.escape(w) + r'\b', t) for w in words)

        if has_word(["test", "tests", "lara", "antigua", "whites", "ashes"]):
            return cls.THEMES["CARIBBEAN_MAROON"]
        elif has_word(["bowling", "shami", "kumble", "spin", "pakistan"]):
            return cls.THEMES["EMERALD_MASTER"]
        elif has_word(["kohli", "century", "centuries", "sachin", "rohit", "world cup", "odi"]):
            return cls.THEMES["CRIMSON_OBSIDIAN"]
        elif has_word(["finisher", "dhoni", "rinku", "six", "chase", "over"]):
            return cls.THEMES["CHARCOAL_EMBER"]
        elif has_word(["t20", "t20i", "ipl", "fastest"]):
            return cls.THEMES["NEON_CYBER"]
        elif has_word(["captain", "trophy", "icc"]):
            return cls.THEMES["ROYAL_EMPIRE"]
        else:
            return cls.rotate_theme(fallback_idx)
