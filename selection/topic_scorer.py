"""Topic scoring engine: calculates weighted multi-factor scores with deduplication penalties."""

import logging
from typing import List, Tuple, Optional, Dict, Any
from storage.models import TopicCandidate, KeywordMetric, CompetitorArticle, TopicScore, SearchIntent
from config.settings import settings

logger = logging.getLogger(__name__)


class TopicScorer:
    """Calculates weighted topic scores based on SEO potential, trend velocity, and business relevance."""

    def __init__(
        self,
        weight_relevance: Optional[float] = None,
        weight_trend: Optional[float] = None,
        weight_ranking: Optional[float] = None,
        weight_business: Optional[float] = None,
        min_topic_score: Optional[float] = None,
        min_business_relevance: Optional[float] = None,
    ):
        self.w_rel = weight_relevance if weight_relevance is not None else settings.weight_accommodation_relevance
        self.w_trend = weight_trend if weight_trend is not None else settings.weight_trend_opportunity
        self.w_rank = weight_ranking if weight_ranking is not None else settings.weight_ranking_opportunity
        self.w_biz = weight_business if weight_business is not None else settings.weight_business_value

        self.min_topic_score = min_topic_score if min_topic_score is not None else settings.min_topic_score
        self.min_business_relevance = min_business_relevance if min_business_relevance is not None else settings.min_business_relevance

    def compute_similarity(self, title_a: str, title_b: str) -> float:
        """Calculate Jaccard token similarity between two titles."""
        tokens_a = set(title_a.lower().replace(":", " ").replace("-", " ").split())
        tokens_b = set(title_b.lower().replace(":", " ").replace("-", " ").split())
        # Filter stop words
        stopwords = {"in", "and", "for", "the", "a", "of", "to", "on", "near", "with", "vs"}
        tokens_a -= stopwords
        tokens_b -= stopwords
        if not tokens_a or not tokens_b:
            return 0.0
        intersection = tokens_a.intersection(tokens_b)
        union = tokens_a.union(tokens_b)
        return len(intersection) / len(union)

    def calculate_topic_score(
        self,
        candidate: TopicCandidate,
        keywords: List[KeywordMetric],
        competitors: List[CompetitorArticle],
        previous_topics: List[str],
    ) -> TopicScore:
        """Compute the four factor scores, total weighted score, and evidence breakdown."""
        evidence: Dict[str, Any] = {}

        # 1. Accommodation Relevance Score (0-100)
        rel_score = float(candidate.accommodation_relevance)
        evidence["base_accommodation_relevance"] = rel_score

        # 2. Trend Opportunity Score (0-100)
        trend_score = 50.0  # default baseline for stable
        if candidate.trend_direction == "rising":
            trend_score = 85.0
        elif candidate.trend_direction == "seasonal_peak":
            trend_score = 90.0
        elif candidate.trend_direction == "falling":
            trend_score = 30.0

        if "high" in candidate.seasonal_relevance.lower():
            trend_score = min(100.0, trend_score + 10.0)

        evidence["trend_direction"] = candidate.trend_direction
        evidence["seasonal_relevance"] = candidate.seasonal_relevance
        evidence["calculated_trend_score"] = trend_score

        # 3. Ranking Opportunity Score (0-100)
        # Higher score if competitor content has identified coverage gaps and moderate keyword difficulty
        rank_score = 60.0
        if competitors:
            total_gaps = sum(len(c.coverage_gaps) for c in competitors)
            if total_gaps >= 5:
                rank_score += 15.0
            avg_word_count = sum(c.word_count or 1000 for c in competitors) / len(competitors)
            if avg_word_count < 1200:
                rank_score += 10.0  # Thin competitor content is easier to outrank
            evidence["competitor_count"] = len(competitors)
            evidence["competitor_gaps_identified"] = total_gaps
            evidence["avg_competitor_words"] = avg_word_count
        else:
            # Do NOT reward missing competitor data
            rank_score = 40.0
            evidence["competitor_count"] = 0
            evidence["warning"] = "Missing competitor data penalized."

        if keywords:
            avg_diff = sum(k.difficulty or 50 for k in keywords) / len(keywords)
            # Lower difficulty = higher opportunity to rank
            diff_factor = max(0.0, (100.0 - avg_diff) * 0.2)
            rank_score += diff_factor
            evidence["avg_keyword_difficulty"] = avg_diff

        rank_score = max(0.0, min(100.0, rank_score))
        evidence["calculated_ranking_opportunity"] = rank_score

        # 4. Business Value Score (0-100)
        biz_score = 65.0
        # Boost for Commercial Investigation or Transactional intent
        if keywords:
            intents = [k.search_intent for k in keywords]
            if SearchIntent.TRANSACTIONAL in intents:
                biz_score += 20.0
            elif SearchIntent.COMMERCIAL_INVESTIGATION in intents:
                biz_score += 15.0
            elif SearchIntent.INFORMATIONAL in intents:
                biz_score += 5.0

        # Check for core high-intent terms in topic
        topic_lower = candidate.topic.lower()
        if any(term in topic_lower for term in ["pg", "hostel", "accommodation", "rent", "housing"]):
            biz_score += 10.0

        biz_score = max(0.0, min(100.0, biz_score))
        evidence["calculated_business_value"] = biz_score

        # Deduplication / History Penalty
        max_similarity = 0.0
        similar_topic = None
        for prev in previous_topics:
            sim = self.compute_similarity(candidate.topic, prev)
            if sim > max_similarity:
                max_similarity = sim
                similar_topic = prev

        penalty = 0.0
        if max_similarity > 0.60:
            penalty = 35.0
            evidence["deduplication_penalty"] = f"Deduplication penalty of -{penalty} applied due to {max_similarity:.2f} similarity with '{similar_topic}'."
        elif max_similarity > 0.40:
            penalty = 15.0
            evidence["deduplication_penalty"] = f"Mild similarity penalty of -{penalty} applied due to '{similar_topic}'."

        # Total Weighted Calculation
        raw_total = (
            (rel_score * self.w_rel)
            + (trend_score * self.w_trend)
            + (rank_score * self.w_rank)
            + (biz_score * self.w_biz)
        )
        total_score = max(0.0, min(100.0, raw_total - penalty))

        rationale = (
            f"Rel: {rel_score:.0f} (wt {self.w_rel*100:.0f}%), "
            f"Trend: {trend_score:.0f} (wt {self.w_trend*100:.0f}%), "
            f"Rank: {rank_score:.0f} (wt {self.w_rank*100:.0f}%), "
            f"Biz: {biz_score:.0f} (wt {self.w_biz*100:.0f}%). "
            f"Net score: {total_score:.1f}/100."
        )

        return TopicScore(
            run_id=candidate.run_id,
            topic=candidate.topic,
            accommodation_relevance_score=rel_score,
            trend_opportunity_score=trend_score,
            ranking_opportunity_score=rank_score,
            business_value_score=biz_score,
            total_score=round(total_score, 2),
            rationale=rationale,
            evidence_breakdown=evidence,
        )

    def select_best_topic(
        self,
        candidates: List[TopicCandidate],
        keywords_by_topic: Dict[str, List[KeywordMetric]],
        competitors_by_topic: Dict[str, List[CompetitorArticle]],
        previous_topics: List[str],
    ) -> Tuple[Optional[TopicCandidate], Optional[TopicScore], List[TopicScore]]:
        """Score all candidates and select the winner meeting threshold requirements."""
        all_scores: List[TopicScore] = []

        for c in candidates:
            kws = keywords_by_topic.get(c.topic, [])
            comps = competitors_by_topic.get(c.topic, [])
            score = self.calculate_topic_score(c, kws, comps, previous_topics)
            all_scores.append(score)

        all_scores.sort(key=lambda s: s.total_score, reverse=True)

        if not all_scores:
            logger.warning("No candidate topics available to score.")
            return None, None, []

        best_score = all_scores[0]
        # Find corresponding candidate
        best_candidate = next((c for c in candidates if c.topic == best_score.topic), None)

        # Check quality / eligibility thresholds
        if best_score.total_score < self.min_topic_score:
            logger.warning(
                f"Top topic '{best_score.topic}' scored {best_score.total_score:.1f}, "
                f"failing minimum threshold of {self.min_topic_score}."
            )
            return None, None, all_scores

        if best_score.business_value_score < self.min_business_relevance:
            logger.warning(
                f"Top topic '{best_score.topic}' has business value {best_score.business_value_score:.1f}, "
                f"failing minimum threshold of {self.min_business_relevance}."
            )
            return None, None, all_scores

        logger.info(f"Selected winner topic: '{best_candidate.topic}' with score {best_score.total_score:.1f}")
        return best_candidate, best_score, all_scores
