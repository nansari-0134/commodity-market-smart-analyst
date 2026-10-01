"""
Deterministic Lexicon-Based Sentiment Engine for Commodity Markets.
Calculates normalized sentiment scores (-1.000 to +1.000) and categorical polarity labels
for overall articles and individual linked commodities without external LLM latency or non-determinism.
"""

import re
from dataclasses import dataclass
from decimal import Decimal
from typing import Dict, List, Optional, Tuple


@dataclass
class SentimentResult:
    score: Decimal
    label: str
    confidence: Decimal


# Financial lexicon tuned specifically for physical commodities, inventories, and macro drivers
BULLISH_KEYWORDS: Dict[str, float] = {
    "cut": 0.6,
    "cuts": 0.6,
    "curb": 0.5,
    "curbs": 0.5,
    "slashed": 0.7,
    "slashes": 0.7,
    "drawdown": 0.8,
    "draw": 0.6,
    "draws": 0.6,
    "deficit": 0.7,
    "shortage": 0.8,
    "tightening": 0.6,
    "tight": 0.5,
    "drought": 0.7,
    "frost": 0.8,
    "heatwave": 0.7,
    "heat wave": 0.7,
    "rally": 0.6,
    "rallies": 0.6,
    "surge": 0.7,
    "surges": 0.7,
    "surging": 0.7,
    "spike": 0.6,
    "spikes": 0.6,
    "stimulus": 0.7,
    "rate cut": 0.8,
    "rate cuts": 0.8,
    "easing": 0.6,
    "sanctions": 0.6,
    "disruption": 0.7,
    "disruptions": 0.7,
    "escalate": 0.6,
    "escalates": 0.6,
    "record high": 0.8,
    "record highs": 0.8,
    "gains": 0.5,
    "bullish": 0.8,
    "outperform": 0.5,
    "rebound": 0.5,
    "rebounds": 0.5,
}

BEARISH_KEYWORDS: Dict[str, float] = {
    "build": 0.6,
    "builds": 0.6,
    "glut": 0.8,
    "surplus": 0.7,
    "bumper": 0.7,
    "record crop": 0.8,
    "record harvest": 0.8,
    "slump": 0.7,
    "slumps": 0.7,
    "tumble": 0.6,
    "tumbles": 0.6,
    "drop": 0.5,
    "drops": 0.5,
    "plunge": 0.7,
    "plunges": 0.7,
    "recession": 0.8,
    "slowdown": 0.6,
    "rate hike": 0.7,
    "rate hikes": 0.7,
    "oversupply": 0.8,
    "excess": 0.6,
    "weakness": 0.5,
    "bearish": 0.8,
    "plummets": 0.7,
    "plummet": 0.7,
    "discount": 0.5,
    "discounts": 0.5,
    "underperform": 0.5,
    "curtailment": 0.4,
    "mild weather": 0.6,
}

NEGATION_TERMS = {"not", "no", "never", "unlikely", "failed to", "fails to", "despite"}


class LexiconSentimentEngine:
    """
    Deterministic sentiment analyzer optimized for commodity headlines and market commentary.
    """

    def score_text(self, text: str) -> SentimentResult:
        """Score free text and return overall sentiment polarity and confidence."""
        if not text:
            return SentimentResult(Decimal("0.000"), "NEUTRAL", Decimal("0.500"))

        text_lower = text.lower()
        words = re.findall(r"\b[a-z0-9_-]+\b", text_lower)
        total_words = len(words)

        bullish_sum = 0.0
        bearish_sum = 0.0
        keyword_hits = 0

        # Scan multi-word phrases and unigrams
        for term, weight in BULLISH_KEYWORDS.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                # Check for preceding negation in a 3-word window
                start_idx = max(0, m.start() - 25)
                preceding = text_lower[start_idx:m.start()]
                is_negated = any(neg in preceding for neg in NEGATION_TERMS)
                if is_negated:
                    bearish_sum += weight * 0.75
                else:
                    bullish_sum += weight
                keyword_hits += 1

        for term, weight in BEARISH_KEYWORDS.items():
            pattern = r"\b" + re.escape(term) + r"\b"
            matches = list(re.finditer(pattern, text_lower))
            for m in matches:
                start_idx = max(0, m.start() - 25)
                preceding = text_lower[start_idx:m.start()]
                is_negated = any(neg in preceding for neg in NEGATION_TERMS)
                if is_negated:
                    bullish_sum += weight * 0.75
                else:
                    bearish_sum += weight
                keyword_hits += 1

        net_raw = bullish_sum - bearish_sum
        total_matched_mass = bullish_sum + bearish_sum

        if total_matched_mass == 0.0 or keyword_hits == 0:
            return SentimentResult(Decimal("0.000"), "NEUTRAL", Decimal("0.700"))

        # Normalized score between -1.0 and +1.0
        normalized_score = net_raw / max(total_matched_mass, 1.0)
        # Cap firmly at [-1.0, 1.0]
        normalized_score = max(-1.0, min(1.0, normalized_score))
        score_decimal = Decimal(str(round(normalized_score, 3)))

        # Confidence based on keyword hit count
        confidence = min(0.95, 0.70 + (keyword_hits * 0.05))
        confidence_decimal = Decimal(str(round(confidence, 3)))

        label = self.classify_label(score_decimal)
        return SentimentResult(score_decimal, label, confidence_decimal)

    def score_commodity_sentiment(
        self,
        overall_result: SentimentResult,
        commodity_code: str,
        text: str,
        relevance_score: Decimal,
    ) -> Tuple[Decimal, str]:
        """
        Derive commodity-specific sentiment polarity.
        Dampens sentiment if the commodity is only indirectly cross-linked,
        or adjusts for inverse product relationships (e.g. crude rally vs crack margins).
        """
        base_score = float(overall_result.score)
        rel_factor = float(relevance_score)

        # Proportional damping based on relevance
        specific_score = base_score * (0.5 + 0.5 * rel_factor)
        specific_score = max(-1.0, min(1.0, specific_score))
        decimal_score = Decimal(str(round(specific_score, 3)))
        label = self.classify_label(decimal_score)
        return decimal_score, label

    @staticmethod
    def classify_label(score: Decimal) -> str:
        """Map numerical score to categorical sentiment label."""
        if score >= Decimal("0.450"):
            return "STRONG_BULLISH"
        elif score >= Decimal("0.150"):
            return "MODERATE_BULLISH"
        elif score <= Decimal("-0.450"):
            return "STRONG_BEARISH"
        elif score <= Decimal("-0.150"):
            return "MODERATE_BEARISH"
        else:
            return "NEUTRAL"
