"""
Cricket Shorts Engine V3 - 3-Connected-Facts Script Generator & AI Researcher
Generates high-retention 35-48s scripts with multi-layer deduplication & negative exclusion prompting.
- Hook (0-3s): 10-14 words curiosity opener in energetic Hinglish
- Fact 1 (3-14s): 24-32 words context & shock
- Fact 2 (14-27s): 24-32 words escalation
- Fact 3 (27-40s): 24-32 words ultimate climax
- Outro CTA (40-48s): 16-22 words comment prompt
Total Word Count: 105 - 130 words (~38-44s spoken audio at 1.10x pace).
"""

import os
import re
import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from research.v3_fact_topics import V3_COLLECTIONS
from research.topic_dedup_engine import TopicDedupEngine

logger = logging.getLogger("cricket_shorts.script_v3")

CATEGORIES_POOL = [
    "Unusual incidents during international matches",
    "Hidden cricket rules and laws",
    "Unbelievable IPL records",
    "Forgotten cricket history",
    "Interesting facts about legendary cricketers",
    "Rare bowling and batting records",
    "Interesting facts about cricket stadiums",
    "Lesser-known umpiring decisions",
    "Surprising World Cup facts",
    "Rare player achievements and career milestones",
    "Cricket facts that sound unbelievable but are genuinely true"
]


class ScriptGeneratorV3:
    @classmethod
    def get_or_generate_topic(
        cls,
        topic_key: Optional[str] = None,
        custom_prompt: Optional[str] = None,
        excluded_topics: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves a verified 3-fact collection or generates a fresh one using Gemini AI.
        """
        if topic_key and topic_key in V3_COLLECTIONS:
            logger.info(f"Using verified curated V3 collection: '{topic_key}'")
            return V3_COLLECTIONS[topic_key]

        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key and len(gemini_key) > 10:
            ai_data = cls.generate_fresh_ai_topic(gemini_key, excluded_topics=excluded_topics, category_hint=custom_prompt)
            if ai_data:
                return ai_data

        # Fallback to an available curated topic if not excluded
        if excluded_topics:
            published_keys = {t.get("topic_key") for t in excluded_topics}
            for k, b in V3_COLLECTIONS.items():
                if k not in published_keys:
                    return b

        return None

    @classmethod
    def generate_fresh_ai_topic(
        cls,
        api_key: str,
        excluded_topics: Optional[List[Dict[str, Any]]] = None,
        category_hint: Optional[str] = None,
        max_attempts: int = 3
    ) -> Optional[Dict[str, Any]]:
        """
        Generates a 100% unique, verified 3-connected-facts documentary short
        using Gemini 3.8 Flash, strictly excluding all previously covered topics.
        """
        excluded_topics = excluded_topics or []
        # Build concise negative exclusion summary
        negatives = []
        for item in excluded_topics[:30]:
            title = item.get("topic_title") or item.get("topic", "")
            concept = item.get("core_concept", "")
            if title:
                negatives.append(f"- {title} ({concept[:60]})")

        negatives_prompt = "\n".join(negatives) if negatives else "None yet."

        import random
        category = category_hint or random.choice(CATEGORIES_POOL)

        system_instruction = f"""
Act as a Senior Cricket Documentary Scriptwriter and Cricket Historian.
Generate a structured 3-connected-facts cricket story for a 9:16 YouTube Short (35-48 seconds duration).
Category: {category}

CRITICAL RULES:
1. STRICT DEDUPLICATION: You must NEVER generate facts about any of these previously published topics:
{negatives_prompt}
Every fact must be 100% brand new, authentic, and historically verified (ESPNCricinfo/ICC/MCC).

2. SCRIPT STRUCTURE (Total spoken Hindi: 105 - 125 words):
- hook_narration (0-3s): 10-14 words energetic curiosity opener in Hinglish (Hindi with cricket English terms).
- Fact 1 (3-14s): 24-30 words shock and context.
- Fact 2 (14-27s): 24-30 words escalation.
- Fact 3 (27-40s): 24-30 words ultimate climax.
- outro_narration (40-48s): 16-20 words comment trigger & subscribe prompt.

3. OUTPUT FORMAT: Output strictly valid JSON with this exact schema (no markdown backticks):
{{
  "id": "slug_id_without_spaces",
  "topic": "English Topic Title Under 50 Chars",
  "category": "{category}",
  "hook_title": "BOLD ENGLISH HOOK TITLE",
  "hook_subtitle": "Hindi subtitle for hook",
  "hook_narration": "10-14 words Hindi hook",
  "facts": [
    {{
      "fact_number": 1,
      "badge": "FACT 1 : SUBJECT",
      "player_name": "Full Player Name",
      "player_or_subject": "Player Name",
      "country": "INDIA/AUSTRALIA/ENGLAND/etc",
      "player_role": "Right Hand Batsman / Fast Bowler",
      "tournament_header": "🏆 Tournament Name Year",
      "headline": "SHORT BOLD HEADLINE",
      "subheadline": "Short context",
      "narration": "24-30 words Hindi narration for fact 1",
      "footage_query": "cricket footage query for pexels",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "MAIN STAT (e.g. 50 RUNS)",
      "achievement_tag": "HISTORIC RECORD",
      "stats_table": [
        ["Metric 1", "Value 1"],
        ["Metric 2", "Value 2"],
        ["Metric 3", "Value 3"],
        ["Metric 4", "Value 4"]
      ],
      "source_primary": "ESPNCricinfo / ICC Official"
    }},
    {{
      "fact_number": 2,
      "badge": "FACT 2 : SUBJECT",
      "player_name": "Full Player Name",
      "player_or_subject": "Player Name",
      "country": "INDIA/AUSTRALIA/etc",
      "player_role": "Player Role",
      "tournament_header": "🏆 Tournament Name Year",
      "headline": "SHORT BOLD HEADLINE",
      "subheadline": "Short context",
      "narration": "24-30 words Hindi narration for fact 2",
      "footage_query": "cricket footage query for pexels",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "MAIN STAT",
      "achievement_tag": "HISTORIC RECORD",
      "stats_table": [
        ["Metric 1", "Value 1"],
        ["Metric 2", "Value 2"],
        ["Metric 3", "Value 3"],
        ["Metric 4", "Value 4"]
      ],
      "source_primary": "ESPNCricinfo / ICC Official"
    }},
    {{
      "fact_number": 3,
      "badge": "FACT 3 : SUBJECT",
      "player_name": "Full Player Name",
      "player_or_subject": "Player Name",
      "country": "INDIA/AUSTRALIA/etc",
      "player_role": "Player Role",
      "tournament_header": "🏆 Tournament Name Year",
      "headline": "SHORT BOLD HEADLINE",
      "subheadline": "Short context",
      "narration": "24-30 words Hindi narration for fact 3",
      "footage_query": "cricket footage query for pexels",
      "scene_type": "batsman/bowler/stadium/celebration",
      "stat_callout": "MAIN STAT",
      "achievement_tag": "HISTORIC RECORD",
      "stats_table": [
        ["Metric 1", "Value 1"],
        ["Metric 2", "Value 2"],
        ["Metric 3", "Value 3"],
        ["Metric 4", "Value 4"]
      ],
      "source_primary": "ESPNCricinfo / ICC Official"
    }}
  ],
  "outro_narration": "15-20 words Hindi comment trigger and CTA",
  "seo_title": "YouTube Title under 70 chars with #Shorts #CricketRaaz",
  "seo_description": "SEO description under 300 chars",
  "tags": ["Cricket", "Shorts", "CricketRaaz"]
}}
"""

        for attempt in range(1, max_attempts + 1):
            logger.info(f"Invoking Gemini 3.8 Flash for AI Topic Research (Attempt {attempt}/{max_attempts})...")
            candidate_data = cls._call_gemini_api(api_key, system_instruction)
            if not candidate_data:
                continue

            # Check candidate data against deduplication engine
            is_valid, reason, score, match = TopicDedupEngine.validate_candidate(candidate_data, excluded_topics)
            if is_valid:
                logger.info(f"✓ AI-generated topic '{candidate_data.get('topic')}' passed all deduplication checks!")
                return candidate_data
            else:
                logger.warning(f"Attempt {attempt} rejected by dedup engine: {reason} (similarity: {score:.2f}). Retrying...")

        logger.error(f"Failed to generate unique AI topic after {max_attempts} attempts.")
        return None

    @classmethod
    def _call_gemini_api(cls, api_key: str, prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini API via google-genai SDK or REST API fallback across resilient model endpoints."""
        candidate_models = ["gemini-3.8-flash"]

        # 1. Try google-genai SDK
        for model_name in candidate_models:
            for retry in range(2):
                try:
                    from google import genai
                    client = genai.Client(api_key=api_key)
                    resp = client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={"response_mime_type": "application/json"}
                    )
                    text = resp.text.strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                    data = json.loads(text)
                    if "facts" in data and len(data["facts"]) == 3:
                        logger.info(f"✓ Successfully generated topic using SDK ({model_name})")
                        return data
                except Exception as e:
                    logger.warning(f"google-genai SDK call for {model_name} (try {retry+1}/2) failed: {e}. Retrying with backoff...")
                    import time
                    time.sleep(2)

        # 2. REST API fallback
        import requests
        for model_name in candidate_models:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"response_mime_type": "application/json"}
                }
                r = requests.post(url, json=payload, timeout=25)
                if r.status_code == 200:
                    resp_json = r.json()
                    text = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```"):
                        text = text.split("\n", 1)[1].rsplit("\n", 1)[0].strip()
                    data = json.loads(text)
                    if "facts" in data and len(data["facts"]) == 3:
                        logger.info(f"✓ Successfully generated topic using REST ({model_name})")
                        return data
                else:
                    logger.warning(f"Gemini REST API error {r.status_code} on {model_name}: {r.text[:120]}")
            except Exception as e:
                logger.warning(f"Gemini REST fallback for {model_name} failed: {e}")

        return None

    @classmethod
    def assemble_full_narration(cls, bundle: Dict[str, Any]) -> str:
        """Combines hook, 3 facts, and outro into one contiguous narration script."""
        parts = [bundle["hook_narration"]]
        for f in bundle["facts"]:
            parts.append(f["narration"])
        parts.append(bundle["outro_narration"])
        return " ".join(parts)
