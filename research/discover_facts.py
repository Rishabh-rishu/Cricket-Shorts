"""
Fact Discovery Engine
Discovers at least 10 candidate cricket facts, validates and scores them,
and populates the database while preventing duplicate facts.
"""

from typing import List, Dict, Any
import logging
from research.fact_repository import VERIFIED_FACTS_POOL
from research.verify_facts import FactVerifier
from research.fact_scorer import FactScorer
from database.models import DatabaseManager

logger = logging.getLogger("cricket_shorts.research")


class FactDiscoverer:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def discover_and_evaluate(self, min_candidates: int = 10, target_approved: int = 2) -> List[Dict[str, Any]]:
        """
        Discovers candidate facts, scores them, and saves approved facts to SQLite.
        Returns the top approved facts for short generation.
        """
        logger.info(f"Starting fact discovery. Candidate target: {min_candidates}")
        candidates = []

        # 1. Fetch from repository pool
        for item in VERIFIED_FACTS_POOL:
            # Check duplicate hash first
            if not self.db.fact_exists(item["topic"], item["main_fact"]):
                candidates.append(dict(item))

        logger.info(f"Found {len(candidates)} unrecorded candidate facts.")

        evaluated_facts = []
        for cand in candidates:
            # Step A: Verification
            is_valid, msg, vdata = FactVerifier.verify(cand)
            if not is_valid:
                logger.warning(f"Fact '{cand['topic']}' failed verification: {msg}")
                continue

            # Step B: Quality Scoring
            scores, is_approved, score_notes = FactScorer.score_fact(cand)
            cand.update(scores)
            cand["is_approved"] = 1 if is_approved else 0
            cand["score_notes"] = score_notes

            # Step C: Save to DB
            fact_id = self.db.insert_fact(cand)
            if fact_id:
                cand["id"] = fact_id
                evaluated_facts.append(cand)
                logger.info(f"Fact '{cand['topic']}' saved with total score: {cand['total_score']} (Approved: {is_approved})")

        # Select top approved facts
        approved = [f for f in evaluated_facts if f.get("is_approved") == 1]
        approved.sort(key=lambda x: x.get("total_score", 0), reverse=True)

        logger.info(f"Discovery complete. Total evaluated: {len(evaluated_facts)}, Approved: {len(approved)}")
        return approved[:target_approved]
