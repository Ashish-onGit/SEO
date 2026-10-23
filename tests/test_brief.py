"""Unit tests for SEO brief generation and adherence to editorial specifications."""

import pytest
from storage.models import TopicCandidate, TopicScore, KeywordMetric, CompetitorArticle, SearchIntent
from content.seo_brief import SEOBriefGenerator
from config.brand_config import brand_config


@pytest.fixture
def brief_generator():
    return SEOBriefGenerator()


def test_brief_contains_all_required_fields(brief_generator):
    """Test that generated brief contains all 20 required points."""
    candidate = TopicCandidate(
        run_id="run_brief_01",
        topic="Student Hostels and PGs in Greater Noida Knowledge Park",
        market="India (Greater Noida)",
        accommodation_relevance=95.0,
    )
    score = TopicScore(
        run_id="run_brief_01",
        topic=candidate.topic,
        accommodation_relevance_score=95.0,
        trend_opportunity_score=80.0,
        ranking_opportunity_score=75.0,
        business_value_score=90.0,
        total_score=86.5,
        rationale="Strong market demand",
    )
    keywords = [
        KeywordMetric(
            run_id="run_brief_01",
            topic=candidate.topic,
            keyword="pg in knowledge park greater noida",
            search_intent=SearchIntent.TRANSACTIONAL,
        ),
        KeywordMetric(
            run_id="run_brief_01",
            topic=candidate.topic,
            keyword="hostels near galgotias university",
            search_intent=SearchIntent.COMMERCIAL_INVESTIGATION,
        ),
    ]
    competitors = [
        CompetitorArticle(
            run_id="run_brief_01",
            topic=candidate.topic,
            title="Knowledge park hostels",
            url="https://example.com/pgs",
            domain="example.com",
            search_query="test",
            headings=["Overview", "Hostel Fees"],
            coverage_gaps=["Lacks metro details"],
            word_count=1000,
        )
    ]

    brief = brief_generator.generate_brief(candidate, score, keywords, competitors)

    assert brief.topic == candidate.topic
    assert brief.primary_keyword == "pg in knowledge park greater noida"
    assert len(brief.target_faqs) == 10
    assert len(brief.outline) >= 5
    assert len(brief.recommended_internal_links) > 0

    # Ensure internal links match verified catalog
    verified_urls = {item.url for item in brand_config.verified_internal_urls}
    for link in brief.recommended_internal_links:
        assert link["url"] in verified_urls

    # Check meta lengths
    assert len(brief.suggested_title) <= 70
    assert len(brief.suggested_meta_description) <= 165
    assert len(brief.suggested_slug) > 5
