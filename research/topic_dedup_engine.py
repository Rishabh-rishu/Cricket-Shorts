"""
Multi-Layer Topic Deduplication & Semantic Validation Engine
Guarantees that previously published cricket topics, player milestones,
laws, and match feats are NEVER repeated, even if phrased with different wording.
"""

import os
import re
import json
import hashlib
import uuid
import logging
from difflib import SequenceMatcher
from typing import Dict, Any, List, Tuple, Optional, Set

logger = logging.getLogger("cricket_shorts.dedup_engine")

# Stopwords to filter out when calculating lexical and concept similarity
CRICKET_STOPWORDS = {
    "ke", "ki", "ka", "ko", "se", "aur", "par", "mein", "me", "hain", "hai",
    "jo", "ye", "yeh", "woh", "ek", "kya", "sabse", "top", "unbelievable",
    "shocking", "record", "records", "cricket", "shorts", "cricketraaz",
    "history", "facts", "fact", "the", "in", "and", "of", "a", "an", "to",
    "for", "with", "by", "at", "3", "5", "10", "best", "greatest", "rare"
}

# Known key player entities to detect collisions
CRICKET_PLAYER_ENTITIES = [
    "sunil gavaskar", "gavaskar", "rohit sharma", "rohit", "glenn mcgrath", "mcgrath",
    "anil kumble", "kumble", "jasprit bumrah", "bumrah", "muttiah muralitharan", "muralitharan",
    "sachin tendulkar", "sachin", "rahul dravid", "dravid", "ms dhoni", "dhoni",
    "kapil dev", "yuvraj singh", "yuvraj", "virat kohli", "kohli", "chris gayle", "gayle",
    "ab de villiers", "de villiers", "brian lara", "lara", "alzarri joseph",
    "angelo mathews", "mathews", "ravichandran ashwin", "ashwin", "ricky ponting", "ponting",
    "sourav ganguly", "ganguly", "bapu nadkarni", "nadkarni", "shoaib akhtar",
    "stuart broad", "broad", "imran khan", "mithali raj", "jhulan goswami", "belinda clark"
]

# Core record and rule concepts
CRICKET_RULE_ENTITIES = [
    "timed out", "helmet penalty", "penalty runs", "mankad", "non-striker run out",
    "law 28", "law 38", "law 31", "law 40", "appealing mandatory", "dead ball",
    "underarm bowling", "handled the ball", "obstructing the field"
]


class TopicDedupEngine:
    SIMILARITY_REJECTION_THRESHOLD = 0.38
    CONCEPT_RATIO_THRESHOLD = 0.55

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Normalizes title/concept string: lowercases, removes emojis, punctuation,
        and replaces synonymous variations.
        """
        if not text:
            return ""
        # Remove hashtags and handles
        text = re.sub(r'#\w+', '', text)
        text = re.sub(r'@\w+', '', text)
        # Remove emojis and non-alphanumeric except spaces
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        # Standardize synonyms
        replacements = {
            "world cup": "wc",
            "century": "100",
            "centuries": "100",
            "hundred": "100",
            "hundreds": "100",
            "wicket": "wkt",
            "wickets": "wkt",
            "over": "ovr",
            "overs": "ovr",
            "hat trick": "hattrick",
            "hat-trick": "hattrick",
            "captaincy": "captain"
        }
        for k, v in replacements.items():
            text = re.sub(rf'\b{k}\b', v, text)
        return " ".join(text.split())

    @classmethod
    def extract_entities(cls, topic_data: Dict[str, Any]) -> Dict[str, Set[str]]:
        """
        Extracts key players, records, match laws, and numeric stats from topic bundle.
        """
        full_text = " ".join([
            str(topic_data.get("topic", "")),
            str(topic_data.get("topic_title", "")),
            str(topic_data.get("hook_narration", "")),
            str(topic_data.get("hook_title", "")),
            str(topic_data.get("core_concept", ""))
        ]).lower()

        # If 3-connected-facts list is present
        facts = topic_data.get("facts", [])
        for f in facts:
            full_text += " " + str(f.get("player_name", "")).lower()
            full_text += " " + str(f.get("headline", "")).lower()
            full_text += " " + str(f.get("stat_callout", "")).lower()
            full_text += " " + str(f.get("narration", "")).lower()

        found_players = set()
        for p in CRICKET_PLAYER_ENTITIES:
            if re.search(rf'\b{p}\b', full_text):
                found_players.add(p)

        found_rules = set()
        for r in CRICKET_RULE_ENTITIES:
            if r in full_text:
                found_rules.add(r)

        # Extract specific numbers (e.g. 36, 174, 5, 175, 800, 10, 183, 973, 501, 21)
        found_numbers = set(re.findall(r'\b\d{2,4}\b', full_text))

        return {
            "players": found_players,
            "rules": found_rules,
            "numbers": found_numbers
        }

    @classmethod
    def get_content_tokens(cls, text: str) -> Set[str]:
        """Extracts content words filtered of stopwords."""
        norm = cls.normalize_text(text)
        tokens = {w for w in norm.split() if w not in CRICKET_STOPWORDS and len(w) > 2}
        return tokens

    @classmethod
    def calculate_jaccard(cls, set1: Set[str], set2: Set[str]) -> float:
        """Calculates Jaccard similarity between two token sets."""
        if not set1 or not set2:
            return 0.0
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        return intersection / union if union > 0 else 0.0

    @classmethod
    def compare_candidate_against_item(
        cls,
        candidate: Dict[str, Any],
        historical: Dict[str, Any]
    ) -> Tuple[float, str, str]:
        """
        Performs multi-layer comparison between candidate topic and a historical topic.
        Returns: (similarity_score, match_type, reason)
        """
        # 1. Exact Fingerprint / Key Match
        c_key = candidate.get("id") or candidate.get("topic_key")
        h_key = historical.get("topic_key") or historical.get("id")
        if c_key and h_key and c_key == h_key:
            return 1.0, "EXACT_KEY_MATCH", f"Topic key '{c_key}' was already published."

        c_norm_title = cls.normalize_text(candidate.get("topic") or candidate.get("topic_title", ""))
        h_norm_title = cls.normalize_text(historical.get("topic_title") or historical.get("topic", ""))

        if c_norm_title and h_norm_title and c_norm_title == h_norm_title:
            return 1.0, "EXACT_TITLE_MATCH", f"Title '{c_norm_title}' exactly matches published topic."

        # 2. Entity & Record Collision Check
        c_ent = cls.extract_entities(candidate)
        h_ent = cls.extract_entities(historical)

        common_players = c_ent["players"].intersection(h_ent["players"])
        common_rules = c_ent["rules"].intersection(h_ent["rules"])
        common_numbers = c_ent["numbers"].intersection(h_ent["numbers"])

        # Collision rule 1: Same rule incident (e.g. Timed Out, Helmet Penalty, Mankad)
        if common_rules:
            matched_rule = list(common_rules)[0]
            return 1.0, "RULE_COLLISION", f"Cricket rule '{matched_rule}' is already covered in published short."

        # Collision rule 2: Shares 2 or more distinct cricketers
        if len(common_players) >= 2:
            return 0.95, "MULTI_PLAYER_COLLISION", f"Shares multiple players {list(common_players)} with published short."

        # Collision rule 3: Shares 1 cricketer AND specific record numbers
        if len(common_players) >= 1 and len(common_numbers) >= 1:
            return 0.90, "PLAYER_RECORD_COLLISION", f"Shares player {list(common_players)} and stat {list(common_numbers)} with published short."

        # 3. Lexical Token Overlap (Jaccard)
        c_tokens = cls.get_content_tokens(
            f"{candidate.get('topic', '')} {candidate.get('hook_narration', '')} {candidate.get('core_concept', '')}"
        )
        h_tokens = cls.get_content_tokens(
            f"{historical.get('topic_title', '')} {historical.get('core_concept', '')}"
        )
        jaccard = cls.calculate_jaccard(c_tokens, h_tokens)

        # 4. SequenceMatcher Concept Similarity
        c_concept = cls.normalize_text(candidate.get("core_concept") or candidate.get("hook_narration") or candidate.get("topic", ""))
        h_concept = cls.normalize_text(historical.get("core_concept") or historical.get("topic_title", ""))
        concept_ratio = SequenceMatcher(None, c_concept, h_concept).ratio() if c_concept and h_concept else 0.0

        max_score = max(jaccard, concept_ratio)

        if jaccard >= cls.SIMILARITY_REJECTION_THRESHOLD:
            return jaccard, "LEXICAL_SIMILARITY", f"High keyword overlap ({jaccard:.2f}) with topic '{historical.get('topic_title')}'."

        if concept_ratio >= cls.CONCEPT_RATIO_THRESHOLD:
            return concept_ratio, "CONCEPT_SIMILARITY", f"Concept narrative similarity ({concept_ratio:.2f}) with topic '{historical.get('topic_title')}'."

        return max_score, "ACCEPTABLE", "Distinct topic."

    @classmethod
    def validate_candidate(
        cls,
        candidate_topic: Dict[str, Any],
        historical_registry: List[Dict[str, Any]]
    ) -> Tuple[bool, str, float, Optional[Dict[str, Any]]]:
        """
        Validates candidate topic against 100% of historical topics.
        Returns: (is_valid, rejection_reason, highest_similarity, matched_item)
        """
        highest_score = 0.0
        worst_match = None
        worst_reason = "No matches."

        for item in historical_registry:
            score, match_type, reason = cls.compare_candidate_against_item(candidate_topic, item)
            if score > highest_score:
                highest_score = score
                worst_match = item
                worst_reason = f"[{match_type}] {reason}"

            # Fast rejection on high confidence collision
            if score >= 0.85:
                logger.warning(f"Topic '{candidate_topic.get('topic')}' REJECTED: {worst_reason}")
                return False, worst_reason, score, item

        if highest_score >= cls.SIMILARITY_REJECTION_THRESHOLD:
            logger.warning(f"Topic '{candidate_topic.get('topic')}' REJECTED: {worst_reason}")
            return False, worst_reason, highest_score, worst_match

        logger.info(f"Topic '{candidate_topic.get('topic')}' PASSED duplicate check (Max similarity: {highest_score:.2f}).")
        return True, "Unique topic verified.", highest_score, None

    @classmethod
    def select_and_reserve_topic(
        cls,
        db_manager,
        curated_collections: Dict[str, Dict[str, Any]],
        worker_id: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Master topic selection function:
        1. Checks curated collections against complete historical topic registry.
        2. Filters out any published or reserved topics.
        3. Validates candidate for semantic uniqueness.
        4. Atomically reserves the topic.
        5. If curated collections are exhausted, returns (None, None) so AI generator can create a new topic.
        """
        worker_id = worker_id or str(uuid.uuid4())
        historical_topics = db_manager.get_all_registered_topics()
        published_keys = {t["topic_key"] for t in historical_topics if t.get("status") == "PUBLISHED"}
        reserved_keys = {t["topic_key"] for t in historical_topics if t.get("status") == "RESERVED"}

        logger.info(f"Deduplication Engine: {len(published_keys)} published topics, {len(reserved_keys)} reserved.")

        # Pass 1: Look for unreserved, unpublished curated collection
        for t_key, bundle in curated_collections.items():
            if t_key in published_keys or t_key in reserved_keys:
                continue

            # Check semantic validity against all published topics
            is_valid, reason, score, match = cls.validate_candidate(bundle, historical_topics)
            if not is_valid:
                continue

            # Ensure registered in DB
            db_manager.register_topic({
                "topic_key": t_key,
                "topic_title": bundle.get("topic", t_key),
                "normalized_title": cls.normalize_text(bundle.get("topic", t_key)),
                "category": bundle.get("category", "Curated"),
                "core_concept": bundle.get("hook_narration", ""),
                "key_entities": list(cls.extract_entities(bundle)["players"]),
                "key_facts": [f.get("stat_callout", "") for f in bundle.get("facts", [])],
                "status": "AVAILABLE",
                "sha256_fingerprint": hashlib.sha256(f"{t_key}::{bundle.get('topic')}".encode()).hexdigest(),
                "source": "CURATED"
            })

            # Attempt atomic reservation
            if db_manager.reserve_topic(t_key, worker_id):
                logger.info(f"✓ Atomically reserved curated topic '{t_key}' with worker token {worker_id[:8]}.")
                return t_key, bundle

        # Curated topics are completely exhausted or collided
        logger.info("All curated collections have been published or reserved. Triggering dynamic AI topic generator.")
        return None, None
