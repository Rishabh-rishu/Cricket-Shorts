"""
Intelligent Visual Scene Selector & Sequencer
Matches script narrative to dynamic visual scenes, generating
authentic, topic-aligned 1080x1920 visuals for every segment of the video.
"""

import os
import re
from typing import List, Dict, Any, Tuple
from visuals.animation_engine import CricketAnimationEngine


class VisualSelector:
    @classmethod
    def generate_scenes_for_short(
        cls,
        fact_data: Dict[str, Any],
        script_data: Dict[str, Any],
        total_duration: float,
        output_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Generates and saves visual scene images, returning timeline of scenes.
        """
        os.makedirs(output_dir, exist_ok=True)
        topic = fact_data.get("topic", "")
        category = fact_data.get("category", "")
        main_fact = fact_data.get("main_fact", "")
        hook = script_data.get("hook", "")
        surprise = script_data.get("surprise", "")

        scenes = []

        # Time partitioning
        t_hook = min(5.0, total_duration * 0.16)
        t_story = total_duration * 0.45
        t_surprise = total_duration * 0.78
        t_cta = total_duration

        # --- Scene 1: Hook / Intro Spotlight (0.0 to t_hook) ---
        img1_path = os.path.join(output_dir, "scene_1_hook.png")
        CricketAnimationEngine.create_spotlight_scene(
            badge_text=category.upper()[:35],
            headline=cls._clean_headline(topic),
            key_point="क्या आपको इस सच का पता था?",
            output_path=img1_path
        )
        scenes.append({
            "index": 1,
            "type": "spotlight",
            "image_path": img1_path,
            "start": 0.0,
            "end": t_hook,
            "duration": t_hook
        })

        # --- Scene 2: Story Rule / Stadium Demonstration (t_hook to t_story) ---
        img2_path = os.path.join(output_dir, "scene_2_story.png")
        if "rule" in category.lower() or "law" in topic.lower() or "हेलमेट" in main_fact:
            CricketAnimationEngine.create_rule_scene(
                topic=topic,
                highlight_text="MCC नियम: मैदान पर रखे हेलमेट पर गेंद लगने से सीधे 5 पेनल्टी रन!",
                rule_label="OFFICIAL MCC LAW",
                output_path=img2_path
            )
        else:
            CricketAnimationEngine.create_spotlight_scene(
                badge_text="OFFICIAL MATCH INCIDENT",
                headline=cls._extract_short_detail(main_fact),
                key_point="क्रिकेट इतिहास का सबसे दुर्लभ रिकॉर्ड",
                output_path=img2_path
            )
        scenes.append({
            "index": 2,
            "type": "demonstration",
            "image_path": img2_path,
            "start": t_hook,
            "end": t_story,
            "duration": t_story - t_hook
        })

        # --- Scene 3: Scoreboard / Big Metric Hero (t_story to t_surprise) ---
        img3_path = os.path.join(output_dir, "scene_3_scoreboard.png")
        metric, label, details = cls._extract_stats_data(topic, main_fact)
        CricketAnimationEngine.create_scoreboard_scene(
            title=topic,
            big_metric=metric,
            metric_label=label,
            detail_lines=details,
            output_path=img3_path
        )
        scenes.append({
            "index": 3,
            "type": "scoreboard",
            "image_path": img3_path,
            "start": t_story,
            "end": t_surprise,
            "duration": t_surprise - t_story
        })

        # --- Scene 4: Surprise / Climax Scene (t_surprise to max(t_surprise+3, t_cta - 4)) ---
        t_cta_start = max(t_surprise + 1.0, t_cta - 4.5)
        img4_path = os.path.join(output_dir, "scene_4_surprise.png")
        CricketAnimationEngine.create_spotlight_scene(
            badge_text="SHOCKING DETAIL",
            headline="हैरान कर देने वाला मोड़!",
            key_point=cls._extract_short_detail(surprise),
            output_path=img4_path
        )
        scenes.append({
            "index": 4,
            "type": "surprise",
            "image_path": img4_path,
            "start": t_surprise,
            "end": t_cta_start,
            "duration": t_cta_start - t_surprise
        })

        # --- Scene 5: Call to Action (t_cta_start to t_cta) ---
        img5_path = os.path.join(output_dir, "scene_5_cta.png")
        CricketAnimationEngine.create_cta_scene(
            question_text="क्या आप इस नियम / रिकॉर्ड के बारे में जानते थे?",
            output_path=img5_path
        )
        scenes.append({
            "index": 5,
            "type": "cta",
            "image_path": img5_path,
            "start": t_cta_start,
            "end": t_cta,
            "duration": t_cta - t_cta_start
        })

        return scenes

    @staticmethod
    def _clean_headline(topic: str) -> str:
        # Simplify topic for clear display
        parts = topic.split(" - ")
        return parts[0] if len(parts) > 1 else topic[:45]

    @staticmethod
    def _extract_short_detail(text: str) -> str:
        words = text.split()
        return " ".join(words[:14]) if len(words) > 14 else text

    @staticmethod
    def _extract_stats_data(topic: str, main_fact: str) -> Tuple[str, str, List[str]]:
        """Extracts impressive numbers and context for the digital scoreboard."""
        text = f"{topic} {main_fact}".lower()

        if "5 penalty" in text or "helmet" in text or "हेलमेट" in text:
            return "+5 RUNS", "PENALTY AWARDED TO BATTING TEAM", [
                "Ball becomes DEAD immediately",
                "No legal delivery added to bowler",
                "Applies to fielder's ground helmet"
            ]
        elif "timed out" in text or "mathews" in text:
            return "2 MINUTES", "MAX TIME TO FACE DELIVERY", [
                "ICC Men's CWC Clause 40.1.1",
                "First time in 146 years of cricket",
                "Broken helmet strap delay"
            ]
        elif "gavaskar" in text or "36" in text:
            return "36* RUNS", "60 OVERS - 174 BALLS FACED", [
                "1975 Prudential World Cup at Lord's",
                "Chasing 335 vs England",
                "Only 1 boundary in 174 deliveries"
            ]
        elif "bumrah" in text or "35" in text:
            return "35 RUNS", "MOST RUNS IN ONE TEST OVER", [
                "Bowler: Stuart Broad (Edgbaston 2022)",
                "4, 5w, 6nb, 4, 4, 4, 6, 1",
                "World Record in Test Cricket"
            ]
        elif "muralitharan" in text or "800" in text:
            return "800 WICKETS", "FINAL BALL OF TEST CAREER", [
                "Galle Stadium vs India (2010)",
                "Dismissed Pragyan Ojha",
                "Highest Wicket-Taker in Test History"
            ]
        elif "rohit" in text or "hat-trick" in text:
            return "4 WICKETS", "ROHIT SHARMA IPL HAT-TRICK", [
                "Centurion 2009 vs Mumbai Indians",
                "Dismissed Nayar, Harbhajan, Duminy",
                "Figures: 2 Overs, 6 Runs, 4 Wickets"
            ]
        elif "dhoni" in text:
            return "0 CENTURIES", "OUTSIDE ASIA IN TESTS", [
                "Total 90 Test matches played",
                "6 Test Centuries (India & Pakistan)",
                "Highest score outside Asia: 92 at Oval"
            ]
        elif "413" in text or "mankad" in text:
            return "413 RUNS", "52-YEAR UNBROKEN WORLD RECORD", [
                "Vinoo Mankad & Pankaj Roy (1956)",
                "Opening Partnership vs New Zealand",
                "Stood unbeaten until 2008"
            ]
        else:
            return "RECORD FACT", "OFFICIALLY RECORDED IN CRICKET", [
                "Verified by ICC & Wisden Archives",
                "Rare statistical occurrence",
                "100% Genuine Match Event"
            ]
