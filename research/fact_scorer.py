"""
Fact Quality Scoring System
Evaluates potential cricket facts based on 4 strict criteria:
- Reliability (40 pts)
- Uniqueness (25 pts)
- Viewer Curiosity (20 pts)
- Visual Storytelling Potential (15 pts)

Approval threshold: >= 80 points (with min 30/40 reliability).
"""

from typing import Dict, Any, Tuple


class FactScorer:
    MIN_TOTAL_SCORE = 80.0
    MIN_RELIABILITY_SCORE = 30.0

    @classmethod
    def score_fact(cls, fact_data: Dict[str, Any]) -> Tuple[Dict[str, float], bool, str]:
        """
        Evaluate and return score breakdown, approval bool, and explanation.
        """
        reliability = cls._calculate_reliability(fact_data)
        uniqueness = cls._calculate_uniqueness(fact_data)
        curiosity = cls._calculate_curiosity(fact_data)
        visual = cls._calculate_visual_potential(fact_data)

        total = reliability + uniqueness + curiosity + visual
        is_approved = (total >= cls.MIN_TOTAL_SCORE) and (reliability >= cls.MIN_RELIABILITY_SCORE)

        reasons = []
        if reliability < cls.MIN_RELIABILITY_SCORE:
            reasons.append(f"Reliability below minimum: {reliability}/40")
        if total < cls.MIN_TOTAL_SCORE:
            reasons.append(f"Total score {total}/100 is below threshold of {cls.MIN_TOTAL_SCORE}")
        if is_approved:
            reasons.append("High quality, fully verified, engaging fact passed all criteria.")

        scores = {
            "reliability_score": round(reliability, 1),
            "uniqueness_score": round(uniqueness, 1),
            "curiosity_score": round(curiosity, 1),
            "visual_score": round(visual, 1),
            "total_score": round(total, 1)
        }

        return scores, is_approved, " | ".join(reasons)

    @classmethod
    def _calculate_reliability(cls, fact: Dict[str, Any]) -> float:
        score = 0.0
        p_src = fact.get("source_primary", "").lower()
        s_src = fact.get("source_secondary", "").lower()

        # Primary source credibility (up to 25 pts)
        official_domains = ["icc-cricket.com", "bcci.tv", "iplt20.com", "espncricinfo.com", "wisden.com", "cricbuzz.com", "lords.org/mcc"]
        if any(d in p_src for d in official_domains):
            score += 25.0
        elif p_src.startswith("http"):
            score += 18.0
        elif len(p_src) > 5:
            score += 12.0

        # Cross-verification / secondary source (up to 15 pts)
        if any(d in s_src for d in official_domains):
            score += 15.0
        elif len(s_src) > 5:
            score += 10.0

        # Verification notes with specific match date or rule citation
        vnotes = fact.get("verification_notes", "").lower()
        if any(kw in vnotes for kw in ["law ", "scorecard", "match date", "icc rule", "verified on"]):
            score = min(40.0, score + 5.0)

        return min(40.0, max(0.0, score))

    @classmethod
    def _calculate_uniqueness(cls, fact: Dict[str, Any]) -> float:
        # Base uniqueness (20 pts)
        score = 20.0
        category = fact.get("category", "")
        fact_text = (fact.get("main_fact", "") + " " + fact.get("topic", "")).lower()

        # Penalize overdone / generic cricket trivia
        cliche_keywords = ["sachin 100 centuries", "rohit 264", "yuvi 6 sixes", "dhoni 2011 six", "kapil dev 175"]
        if any(kw in fact_text for kw in cliche_keywords):
            score -= 12.0

        # Boost niche categories
        if any(kw in category.lower() for kw in ["hidden cricket rules", "unusual incidents", "forgotten cricket history", "lesser-known"]):
            score += 5.0

        return min(25.0, max(0.0, score))

    @classmethod
    def _calculate_curiosity(cls, fact: Dict[str, Any]) -> float:
        score = 16.0
        fact_text = (fact.get("main_fact", "") + " " + fact.get("topic", "")).lower()
        # High curiosity triggers
        triggers = ["penalty", "helmet", "timed out", "without facing a ball", "banned", "law", "never", "only player", "first time in 140 years"]
        if any(t in fact_text for t in triggers):
            score += 4.0
        return min(20.0, max(0.0, score))

    @classmethod
    def _calculate_visual_potential(cls, fact: Dict[str, Any]) -> float:
        score = 12.0
        fact_text = (fact.get("main_fact", "") + " " + fact.get("topic", "")).lower()
        # Visual cues: numbers, specific field positions, umpire signals, equipment
        if any(v in fact_text for v in ["runs", "overs", "pitch", "wicket", "boundary", "stump", "ball", "signal"]):
            score += 3.0
        return min(15.0, max(0.0, score))
