"""
Cricket Shorts Engine V3 - Multi-Tier Visual Asset & Footage Provider
Orchestrates:
1. High-production Pexels moving footage matching curated sports taxonomy
2. Dynamic Ken Burns player/stat visual motion cards via FFmpeg
3. Overlay composition for broadcast documentary aesthetic
"""

import os
import subprocess
import logging
from typing import Dict, Any, Tuple, Optional
from visuals.pexels_provider import PexelsVideoProvider
from visuals.player_asset_provider import PlayerAssetProvider

logger = logging.getLogger("cricket_shorts.v3_assets")


class V3AssetProvider:
    TAXONOMY_QUERIES = {
        "stadium_night": "cricket stadium floodlights night",
        "bowler_action": "cricket fast bowler run up delivery",
        "batsman_six": "cricket batsman hitting six stadium",
        "stumps_flying": "cricket ball hitting stumps bails",
        "crowd_cheer": "cricket stadium crowd cheering excitement",
        "umpire_decision": "cricket umpire decision signal",
        "wicketkeeper": "cricket wicketkeeper catching ball",
        "field_aerial": "cricket field aerial view match"
    }

    def __init__(self, pexels_key: str = ""):
        self.pexels = PexelsVideoProvider(api_key=pexels_key)

    def generate_scene_video(
        self,
        scene_type: str,
        scene_data: Dict[str, Any],
        duration: float,
        output_clip_path: str,
        temp_dir: str
    ) -> Tuple[bool, str]:
        """
        Produces a 1080x1920 30FPS cinematic video segment for a fact scene.
        Employs dynamic Ken Burns camera motion or real moving footage.
        """
        os.makedirs(os.path.dirname(os.path.abspath(output_clip_path)), exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)

        idx = scene_data.get("fact_number", 0)

        if scene_type == "hook":
            return self._render_hook_scene(scene_data, duration, output_clip_path, temp_dir)
        elif scene_type == "fact_card":
            return self._render_ken_burns_card(scene_data, duration, output_clip_path, temp_dir)
        elif scene_type == "footage_overlay":
            return self._render_footage_overlay(scene_data, duration, output_clip_path, temp_dir)
        elif scene_type == "outro":
            return self._render_outro_scene(scene_data, duration, output_clip_path, temp_dir)
        else:
            return self._render_ken_burns_card(scene_data, duration, output_clip_path, temp_dir)

    def _render_hook_scene(
        self,
        data: Dict[str, Any],
        duration: float,
        out_path: str,
        temp_dir: str
    ) -> Tuple[bool, str]:
        """Hook: Moving stadium night footage + Hero Title Card."""
        query = "cricket stadium floodlights night"
        _, bg_video, _ = self.pexels.fetch_footage_for_scene(query, target_duration=duration, scene_type="stadium")

        hook_png = os.path.join(temp_dir, "hook_card.png")
        PlayerAssetProvider.create_hook_card(
            title=data.get("hook_title", "TOP 3 CRICKET RECORDS"),
            subtitle=data.get("hook_subtitle", "3 सबसे अनसुने क्रिकेट रिकॉर्ड्स"),
            output_path=hook_png
        )

        # Composite background moving video with hook card overlay
        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "eq=contrast=1.08:saturation=1.15[bg];"
            "[1:v]scale=1080:1920[ov];"
            "[bg][ov]overlay=0:0,format=yuv420p[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", bg_video,
            "-i", hook_png,
            "-filter_complex", vf,
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-r", "30",
            "-t", f"{duration:.2f}",
            "-an",
            out_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return (res.returncode == 0), out_path

    def _render_ken_burns_card(
        self,
        fact: Dict[str, Any],
        duration: float,
        out_path: str,
        temp_dir: str
    ) -> Tuple[bool, str]:
        """
        Renders a broadcast fact card with smooth Ken Burns dynamic zoom (1.0 -> 1.08).
        """
        idx = fact.get("fact_number", 1)
        card_png = os.path.join(temp_dir, f"fact_{idx}_card.png")

        accent = "red" if idx == 3 else ("amber" if idx == 2 else "cyan")
        PlayerAssetProvider.create_cinematic_fact_card(
            badge_text=fact.get("badge", f"FACT {idx}"),
            player_name=fact.get("player_name") or fact.get("player_or_subject", "CRICKET RECORD"),
            headline=fact.get("headline", ""),
            subheadline=fact.get("subheadline", ""),
            stat_callout=fact.get("stat_callout", ""),
            output_path=card_png,
            accent_color=accent,
            country=fact.get("country", "INDIA"),
            player_role=fact.get("player_role") or fact.get("role", "International Cricketer"),
            tournament_header=fact.get("tournament_header") or fact.get("tournament_year") or fact.get("badge", "CRICKET RECORD"),
            stats_table=fact.get("stats_table"),
            achievement_tag=fact.get("achievement_tag", "HISTORIC RECORD"),
            player_img_path=fact.get("player_img_path"),
            fact_index=idx
        )

        total_frames = int(duration * 30) + 5
        # Ken Burns slow push-in zoompan filter
        vf = (
            f"zoompan=z='min(zoom+0.0006,1.08)':d={total_frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30,"
            f"format=yuv420p"
        )

        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", card_png,
            "-vf", vf,
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-r", "30",
            "-t", f"{duration:.2f}",
            "-pix_fmt", "yuv420p",
            "-an",
            out_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return (res.returncode == 0), out_path

    def _render_footage_overlay(
        self,
        fact: Dict[str, Any],
        duration: float,
        out_path: str,
        temp_dir: str
    ) -> Tuple[bool, str]:
        """
        Renders moving cricket footage clip with a sleek lower-third player/stat overlay.
        """
        idx = fact.get("fact_number", 1)
        query = fact.get("footage_query", "cricket match action")
        _, bg_video, _ = self.pexels.fetch_footage_for_scene(query, target_duration=duration, scene_type=fact.get("scene_type", "general"))

        # Generate lower-third transparent card
        lt_png = os.path.join(temp_dir, f"fact_{idx}_lowerthird.png")
        self._create_lower_third_png(fact, lt_png)

        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "eq=contrast=1.06:saturation=1.12[bg];"
            "[1:v]scale=1080:1920[ov];"
            "[bg][ov]overlay=0:0,format=yuv420p[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", bg_video,
            "-i", lt_png,
            "-filter_complex", vf,
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-r", "30",
            "-t", f"{duration:.2f}",
            "-an",
            out_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return (res.returncode == 0), out_path

    def _create_lower_third_png(self, fact: Dict[str, Any], out_path: str):
        from PIL import Image, ImageDraw
        img = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Draw subtle vignette at top & bottom
        for y in range(0, 200):
            draw.line([(0, y), (1080, y)], fill=(6, 12, 22, int(160 * (1 - y / 200.0))))
        for y in range(1920 - 360, 1920):
            draw.line([(0, y), (1080, y)], fill=(6, 10, 18, int(225 * ((y - (1920 - 360)) / 360.0))))

        # Top Badge (y = 80)
        f_brand = PlayerAssetProvider.get_font(22, "bold")
        draw.text((70, 80), f"🏏  CRICKET RAAZ  •  {fact.get('badge', 'FACT')}", font=f_brand, fill=(234, 179, 8))

        # Floating lower-third broadcast card (y = 1260 to 1480)
        card_w = 980
        card_h = 210
        card_x = (1080 - card_w) // 2
        card_y = 1265
        draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=24, fill=(12, 22, 42, 235), outline=(56, 189, 248), width=2)

        # Team Crest Emblem on left
        crest = PlayerAssetProvider.draw_cricket_crest(size=80)
        img.alpha_composite(crest, (card_x + 25, card_y + 65))

        # Player Full Name (Bold White)
        pname = fact.get("player_name") or fact.get("player_or_subject", "").upper()
        f_title = PlayerAssetProvider.get_font(40, "bold")
        draw.text((card_x + 120, card_y + 36), pname, font=f_title, fill=(255, 255, 255))

        # Headline (Neon Cyan)
        f_desc = PlayerAssetProvider.get_font(28, "bold")
        draw.text((card_x + 120, card_y + 92), fact.get("headline", ""), font=f_desc, fill=(56, 189, 248))

        # Context subheadline (Gold)
        f_sub = PlayerAssetProvider.get_font(22, "semi")
        draw.text((card_x + 120, card_y + 140), fact.get("subheadline", ""), font=f_sub, fill=(234, 179, 8))

        # Stat capsule on right
        stat = fact.get("stat_callout", "")
        if stat:
            f_stat = PlayerAssetProvider.get_font(28, "bold")
            bbox = draw.textbbox((0, 0), stat, font=f_stat)
            sw = (bbox[2] - bbox[0]) + 36
            sx = card_x + card_w - sw - 30
            sy = card_y + 40
            draw.rounded_rectangle([sx, sy, sx + sw, sy + 64], radius=14, fill=(225, 29, 72), outline=(255, 255, 255), width=2)
            draw.text((sx + 18, sy + 15), stat, font=f_stat, fill=(255, 255, 255))

        img.save(out_path, "PNG")

    def _render_outro_scene(
        self,
        data: Dict[str, Any],
        duration: float,
        out_path: str,
        temp_dir: str
    ) -> Tuple[bool, str]:
        """Outro: Stadium crowd cheering moving footage + CTA Card."""
        query = "cricket stadium crowd cheering excitement"
        _, bg_video, _ = self.pexels.fetch_footage_for_scene(query, target_duration=duration, scene_type="stadium")

        outro_png = os.path.join(temp_dir, "outro_card.png")
        PlayerAssetProvider.create_outro_card(
            cta_heading="WHICH FACT SHOCKED YOU?",
            cta_subheading="कमेंट्स में अपनी राय जरूर बताइए!",
            output_path=outro_png
        )

        vf = (
            "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,"
            "crop=1080:1920,"
            "eq=contrast=1.06:saturation=1.12[bg];"
            "[1:v]scale=1080:1920[ov];"
            "[bg][ov]overlay=0:0,format=yuv420p[v]"
        )

        cmd = [
            "ffmpeg", "-y",
            "-stream_loop", "-1",
            "-i", bg_video,
            "-i", outro_png,
            "-filter_complex", vf,
            "-map", "[v]",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "18",
            "-r", "30",
            "-t", f"{duration:.2f}",
            "-an",
            out_path
        ]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        return (res.returncode == 0), out_path
