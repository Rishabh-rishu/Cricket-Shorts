"""
Cricket Shorts Engine V3 - 3-Connected-Facts Script Generator
Generates high-retention 35-48s scripts with:
- Hook (0-3s): 10-14 words curiosity opener
- Fact 1 (3-14s): 24-32 words context & shock
- Fact 2 (14-27s): 24-32 words escalation
- Fact 3 (27-40s): 24-32 words ultimate climax
- Outro CTA (40-48s): 16-22 words comment prompt
Total Word Count: 105 - 130 words (~38-44s spoken audio at 1.10x pace).
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from research.v3_fact_topics import V3_COLLECTIONS

logger = logging.getLogger("cricket_shorts.script_v3")


class ScriptGeneratorV3:
    @classmethod
    def get_or_generate_topic(cls, topic_key: Optional[str] = None, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieves a verified 3-fact collection or generates one using Gemini API.
        """
        if topic_key and topic_key in V3_COLLECTIONS:
            logger.info(f"Using verified curated V3 collection: '{topic_key}'")
            return V3_COLLECTIONS[topic_key]

        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key and len(gemini_key) > 10 and custom_prompt:
            ai_data = cls._generate_with_gemini(gemini_key, custom_prompt)
            if ai_data:
                return ai_data

        # Fallback default
        default_key = topic_key if topic_key in V3_COLLECTIONS else "wc_records"
        return V3_COLLECTIONS[default_key]

    @classmethod
    def _generate_with_gemini(cls, api_key: str, topic_prompt: str) -> Optional[Dict[str, Any]]:
        """
        Invokes Gemini API (gemini-3.5-flash-lite) to research and structure 3 connected facts.
        """
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent?key={api_key}"
        system_instruction = """
Act as a Senior Cricket Documentary Scriptwriter.
Produce a structured 3-connected-facts cricket story for a 9:16 YouTube Short (35-48 seconds duration).
Total script word count in Hindi must be between 105 and 125 words.

Output strictly valid JSON with this exact schema:
{
  "id": "slug_id",
  "topic": "English Topic Title",
  "category": "Category Name",
  "hook_title": "BOLD ENGLISH HOOK TITLE",
  "hook_subtitle": "Hindi subtitle for hook",
  "hook_narration": "10-14 words Hindi hook",
  "facts": [
    {
      "fact_number": 1,
      "badge": "FACT 1 : SUBJECT",
      "player_or_subject": "Player Name",
      "headline": "SHORT HEADLINE",
      "subheadline": "Short context",
      "narration": "25-30 words Hindi narration for fact 1",
      "footage_query": "cricket footage search query",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "STAT (e.g. 50 RUNS)",
      "source_primary": "Primary record source"
    },
    {
      "fact_number": 2,
      "badge": "FACT 2 : SUBJECT",
      "player_or_subject": "Player Name",
      "headline": "SHORT HEADLINE",
      "subheadline": "Short context",
      "narration": "25-30 words Hindi narration for fact 2",
      "footage_query": "cricket footage search query",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "STAT",
      "source_primary": "Primary record source"
    },
    {
      "fact_number": 3,
      "badge": "FACT 3 : SUBJECT",
      "player_or_subject": "Player Name",
      "headline": "SHORT HEADLINE",
      "subheadline": "Short context",
      "narration": "25-30 words Hindi narration for fact 3",
      "footage_query": "cricket footage search query",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "STAT",
      "source_primary": "Primary record source"
    }
  ],
  "outro_narration": "15-20 words Hindi comment trigger and CTA",
  "seo_title": "Engaging YouTube Title under 70 chars with #Shorts #CricketRaaz",
  "seo_description": "SEO description under 300 chars",
  "tags": ["Cricket", "Shorts", "CricketRaaz"]
}
Only valid facts verified by ESPNCricinfo or ICC. No markdown backticks.
"""
        payload = {
            "contents": [
                {"parts": [{"text": f"Topic: {topic_prompt}\n{system_instruction}"}]}
            ]
        }

        try:
            r = requests.post(url, json=payload, timeout=12)
            if r.status_code == 200:
                resp_json = r.json()
                text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```"):
                    text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                data = json.loads(text)
                if "facts" in data and len(data["facts"]) == 3:
                    logger.info("Successfully generated 3-connected-facts script via Gemini 3.5 Flash Lite.")
                    return data
            else:
                logger.warning(f"Gemini API returned status {r.status_code}: {r.text[:200]}")
        except Exception as e:
            logger.warning(f"Gemini script generation failed: {e}. Falling back to curated facts.")

        return None

    @classmethod
    def assemble_full_narration(cls, bundle: Dict[str, Any]) -> str:
        """
        Combines hook, 3 facts, and outro into one contiguous narration script.
        """
        parts = [bundle["hook_narration"]]
        for f in bundle["facts"]:
            parts.append(f["narration"])
        parts.append(bundle["outro_narration"])
        return " ".join(parts)
