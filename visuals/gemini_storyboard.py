"""
Intelligent Gemini AI Storyboard & Scene Planning Engine
Converts verified cricket facts and timed narration boundaries into a
detailed 6-to-10 segment cinematic visual storyboard with Pexels search keywords,
camera motion directions, minimal floating graphics, and SFX cue points.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("cricket_shorts.storyboard")


class GeminiStoryboardPlanner:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key and len(self.api_key) > 10:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                logger.info("Google Gemini API client initialized successfully.")
            except Exception as e:
                logger.warning(f"Could not initialize Google GenAI Client: {e}")

    def create_storyboard(
        self,
        fact_data: Dict[str, Any],
        script_data: Dict[str, Any],
        audio_boundaries: List[Dict[str, Any]],
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Creates a synchronized 6-to-10 scene visual plan based on narration timing.
        """
        # If Gemini API client is active, attempt AI storyboard generation
        if self.client:
            ai_scenes = self._generate_gemini_storyboard(fact_data, script_data, audio_boundaries, total_duration)
            if ai_scenes and len(ai_scenes) >= 5:
                logger.info(f"Gemini API planned {len(ai_scenes)} cinematic scenes.")
                return ai_scenes

        # Fallback to intelligent rule-based scene planning
        logger.info("Using intelligent rule-based storyboard planner (6-8 visual segments).")
        return self._generate_rule_based_storyboard(fact_data, script_data, audio_boundaries, total_duration)

    def _generate_gemini_storyboard(
        self,
        fact: Dict[str, Any],
        script: Dict[str, Any],
        boundaries: List[Dict[str, Any]],
        total_duration: float
    ) -> Optional[List[Dict[str, Any]]]:
        prompt = f"""
Act as a Senior Cricket Documentary Director.
Create a scene-by-scene visual storyboard for a 9:16 YouTube Short (duration: {total_duration:.1f} seconds).

FACT: {fact.get('topic')}
CATEGORY: {fact.get('category')}
MAIN FACT: {fact.get('main_fact')}
SCRIPT: {script.get('full_script')}

Plan exactly 6 to 8 visual segments. For each segment, output a JSON array of objects with:
- "scene_index" (int 1 to 8)
- "start_sec" (float)
- "end_sec" (float)
- "duration" (float)
- "visual_description" (concise visual description)
- "footage_search_queries" (list of 2-3 specific Pexels video search queries e.g. "cricket fast bowler", "cricket stadium crowd", "batsman hitting ball")
- "camera_motion" ("slow zoom in", "dynamic push", "tracking shot", "subtle pan")
- "overlay_headline" (short 2-4 word English/Hindi lower-third headline e.g. "MCC LAW 31", "WORLD RECORD")
- "overlay_metric" (short stat e.g. "APPEAL MANDATORY", "35 RUNS")
- "sfx_trigger" (one of: "transition_whoosh", "bat_hit", "stadium_cheer", "dramatic_boom", "umpire_whistle")

Return ONLY valid JSON array. No markdown codeblocks.
"""
        try:
            # Prefer free-tier gemini-2.5-flash or gemini-1.5-flash
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            text = response.text.strip()
            # Clean possible markdown formatting
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
            scenes = json.loads(text)
            if isinstance(scenes, list) and len(scenes) >= 5:
                return scenes
        except Exception as e:
            logger.warning(f"Gemini storyboard generation failed: {e}. Falling back to rule planner.")

        return None

    def _generate_rule_based_storyboard(
        self,
        fact: Dict[str, Any],
        script: Dict[str, Any],
        boundaries: List[Dict[str, Any]],
        total_duration: float
    ) -> List[Dict[str, Any]]:
        """
        Partitions the video into 6 to 8 synchronized visual scenes matching the narration.
        """
        topic = fact.get("topic", "")
        category = fact.get("category", "")
        main_fact = fact.get("main_fact", "")

        # Define 7 scene timestamps across the total duration
        # Target ~4.5 to 5.5s per scene
        num_scenes = 7
        dur_step = total_duration / num_scenes

        scenes_spec = [
            # Scene 1: Hook / High Curiosity Opening
            {
                "index": 1,
                "scene_type": "hook",
                "queries": ["cricket stadium night match", "cricket stadium lights", "cricket crowd cheering"],
                "camera": "dramatic push in",
                "headline": category.upper()[:28],
                "metric": "CRICKET FACTS FACTORY",
                "sfx": "transition_whoosh"
            },
            # Scene 2: Bowler / Action Setup
            {
                "index": 2,
                "scene_type": "action_setup",
                "queries": ["fast bowling action cricket", "cricket bowler run up", "cricket bowling"],
                "camera": "tracking shot",
                "headline": "THE UNSEEN INCIDENT",
                "metric": "DECISIVE OVER",
                "sfx": "bat_hit"
            },
            # Scene 3: Ball / Delivery / Rule In Play
            {
                "index": 3,
                "scene_type": "delivery",
                "queries": ["cricket ball close up", "cricket spin bowling", "cricket ball spin"],
                "camera": "slow zoom in",
                "headline": "OFFICIAL MATCH LAW",
                "metric": "BALL IN PLAY",
                "sfx": "transition_whoosh"
            },
            # Scene 4: Batsman / Crease Moment
            {
                "index": 4,
                "scene_type": "batsman",
                "queries": ["cricket batsman facing fast bowling", "cricket batsman hitting six", "cricket match action"],
                "camera": "cinematic zoom",
                "headline": "CRITICAL MOMENT",
                "metric": "CREASE DECISION",
                "sfx": "bat_hit"
            },
            # Scene 5: Umpire / Wicket / Impact Twist
            {
                "index": 5,
                "scene_type": "twist",
                "queries": ["cricket umpire decision", "cricket wicketkeeper catching ball", "cricket stumps bails"],
                "camera": "dramatic zoom",
                "headline": "SHOCKING TWIST",
                "metric": "100% VERIFIED RECORD",
                "sfx": "dramatic_boom"
            },
            # Scene 6: Historic Milestone / Record Context
            {
                "index": 6,
                "scene_type": "record",
                "queries": ["cricket world cup stadium", "cricket stadium crowd celebration", "cricket trophy match"],
                "camera": "smooth pan",
                "headline": "WISDEN & ICC ARCHIVE",
                "metric": "HISTORIC FACT",
                "sfx": "umpire_whistle"
            },
            # Scene 7: CTA / Outro
            {
                "index": 7,
                "scene_type": "outro",
                "queries": ["cricket stadium celebration", "cricket crowd cheering", "cricket stadium night match"],
                "camera": "slow zoom out",
                "headline": "SUBSCRIBE FOR DAILY FACTS",
                "metric": "WHAT'S YOUR OPINION?",
                "sfx": "stadium_cheer"
            }
        ]

        # Customize headlines/metrics based on specific fact
        if "penalty" in topic.lower() or "helmet" in topic.lower() or "हेलमेट" in main_fact:
            scenes_spec[2]["headline"] = "MCC LAW 28.3"
            scenes_spec[2]["metric"] = "+5 PENALTY RUNS"
            scenes_spec[4]["headline"] = "BALL IS DEAD"
            scenes_spec[4]["metric"] = "IMMEDIATE PENALTY"
        elif "timed out" in topic.lower() or "mathews" in topic.lower():
            scenes_spec[2]["headline"] = "ICC CWC CLAUSE 40.1"
            scenes_spec[2]["metric"] = "2 MINUTES LIMIT"
            scenes_spec[4]["headline"] = "TIMED OUT APPEAL"
            scenes_spec[4]["metric"] = "FIRST TIME IN 146 YEARS"
        elif "appealing" in topic.lower() or "law 31" in topic.lower():
            scenes_spec[2]["headline"] = "MCC LAW 31.1"
            scenes_spec[2]["metric"] = "APPEAL MANDATORY"
            scenes_spec[4]["headline"] = "NO APPEAL = NOT OUT"
            scenes_spec[4]["metric"] = "CLEAN BOWLED RULE"
        elif "bumrah" in topic.lower() or "बुमराह" in main_fact:
            scenes_spec[1]["headline"] = "EDGBASTON 2022"
            scenes_spec[1]["metric"] = "84TH OVER HISTORIC"
            scenes_spec[2]["headline"] = "STUART BROAD"
            scenes_spec[2]["metric"] = "4, 5w, 6nb, 4, 4, 4, 6, 1"
            scenes_spec[3]["headline"] = "JASPRIT BUMRAH"
            scenes_spec[3]["metric"] = "35 RUNS WORLD RECORD"
            scenes_spec[4]["headline"] = "TEST CRICKET RECORD"
            scenes_spec[4]["metric"] = "MOST RUNS IN ONE OVER"
            scenes_spec[5]["headline"] = "BROAD VS BUMRAH"
            scenes_spec[5]["metric"] = "15 YEARS AFTER YUVRAJ"
        elif "gavaskar" in topic.lower() or "गावस्कर" in main_fact:
            scenes_spec[1]["headline"] = "1975 WORLD CUP"
            scenes_spec[1]["metric"] = "LORD'S CRICKET GROUND"
            scenes_spec[2]["headline"] = "SUNIL GAVASKAR"
            scenes_spec[2]["metric"] = "174 BALLS FACED"
            scenes_spec[3]["headline"] = "36 NOT OUT"
            scenes_spec[3]["metric"] = "60 OVERS 1 BOUNDARY"
            scenes_spec[4]["headline"] = "MYSTERIOUS INNINGS"
            scenes_spec[4]["metric"] = "INDIA LOST BY 202 RUNS"
        elif "muralitharan" in topic.lower() or "मुरलीधरन" in main_fact:
            scenes_spec[1]["headline"] = "GALLE 2010"
            scenes_spec[1]["metric"] = "FAREWELL TEST MATCH"
            scenes_spec[2]["headline"] = "PRAGYAN OJHA"
            scenes_spec[2]["metric"] = "FINAL WICKET NEEDED"
            scenes_spec[3]["headline"] = "MUTTIAH MURALITHARAN"
            scenes_spec[3]["metric"] = "800 TEST WICKETS"
            scenes_spec[4]["headline"] = "FINAL BALL OF CAREER"
            scenes_spec[4]["metric"] = "ALL-TIME WORLD RECORD"

        storyboard = []
        for i, spec in enumerate(scenes_spec):
            s_start = round(i * dur_step, 2)
            s_end = round(total_duration if i == len(scenes_spec) - 1 else (i + 1) * dur_step, 2)
            storyboard.append({
                "scene_index": spec["index"],
                "start_sec": s_start,
                "end_sec": s_end,
                "duration": round(s_end - s_start, 2),
                "scene_type": spec["scene_type"],
                "footage_search_queries": spec["queries"],
                "camera_motion": spec["camera"],
                "overlay_headline": spec["headline"],
                "overlay_metric": spec["metric"],
                "sfx_trigger": spec["sfx"]
            })

        return storyboard
