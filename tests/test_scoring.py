"""Unit tests for topic scoring, missing metrics, and deduplication penalties."""

import pytest
from storage.models import TopicCandidate, KeywordMetric, CompetitorArticle, SearchIntent, MetricProvenance
from selection.topic_scorer import TopicScorer


@pytest.fixture
def scorer():
    return TopicScorer(
        weight_relevance=0.35,
        weight_trend=0.20,
        weight_ranking=0.20,
        weight_business=0.25,
        min_topic_score=50.0,
        min_business_relevance=50.0,
    )


def test_calculate_topic_score_normal(scorer):
    """Test scoring a standard candidate topic."""
    candidate = TopicCandidate(
        run_id="run_1",
        topic="Affordable Student Hostels in Greater Noida Knowledge Park",
        trend_direction="rising",
        seasonal_relevance="high",
        accommodation_relevance=95.0,
    )
    keywords = [
        KeywordMetric(
            run_id="run_1",
            topic=candidate.topic,
            keyword="pg in knowledge park 2",
            difficulty=45,
            search_intent=SearchIntent.TRANSACTIONAL,
            business_relevance=90.0,
        )
    ]
    competitors = [
        CompetitorArticle(
            run_id="run_1",
            topic=candidate.topic,
            title="Knowledge park hostels",
            url="https://example.com/pg",
            domain="example.com",
            search_query="test",
            headings=["Overview", "Hostel Fees"],
            coverage_gaps=["Lacks metro details", "No electricity cost breakdown"],
            word_count=900,
        )
    ]

    score = scorer.calculate_topic_score(candidate, keywords, competitors, previous_topics=[])
    assert score.total_score >= 70.0
    assert score.accommodation_relevance_score == 95.0
    assert "Net score" in score.rationale


def test_deduplication_penalty(scorer):
    """Test that a topic too similar to past topics receives a heavy penalty."""
    candidate = TopicCandidate(
        run_id="run_1",
        topic="Affordable Student Hostels in Greater Noida Knowledge Park",
        trend_direction="stable",
        accommodation_relevance=90.0,
    )

    past_topics = [
        "Affordable Student Hostels and PGs in Greater Noida Knowledge Park",  # almost identical
    ]

    score = scorer.calculate_topic_score(candidate, [], [], previous_topics=past_topics)
    assert "deduplication_penalty" in score.evidence_breakdown
    assert score.total_score < 60.0


def test_missing_competitor_data_handling(scorer):
    """Test that missing competitor data is explicitly penalized, not rewarded."""
    candidate = TopicCandidate(
        run_id="run_1",
        topic="Student Housing in Uttar Pradesh",
        trend_direction="stable",
        accommodation_relevance=70.0,
    )
    score = scorer.calculate_topic_score(candidate, keywords=[], competitors=[], previous_topics=[])
    assert score.evidence_breakdown["competitor_count"] == 0
    assert score.ranking_opportunity_score <= 50.0


def test_min_threshold_rejection(scorer):
    """Test rejecting a topic that fails the minimum score threshold."""
    candidate = TopicCandidate(
        run_id="run_1",
        topic="Random Topic Without Accommodation Value",
        trend_direction="falling",
        seasonal_relevance="low",
        accommodation_relevance=10.0,
    )
    winner, best_score, all_scores = scorer.select_best_topic(
        [candidate],
        keywords_by_topic={},
        competitors_by_topic={},
        previous_topics=[],
    )
    assert winner is None
    assert len(all_scores) == 1
    assert all_scores[0].total_score < 50.0
