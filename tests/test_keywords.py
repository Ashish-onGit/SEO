"""Unit tests for keyword research, intent classification, and business scoring."""

import pytest
from research.keywords import GoogleSuggestKeywordProvider
from storage.models import SearchIntent


@pytest.fixture
def keyword_provider():
    return GoogleSuggestKeywordProvider()


def test_intent_classification(keyword_provider):
    """Test classification of keyword search intents."""
    # Transactional
    assert keyword_provider.classify_intent("book student hostel in lucknow") == SearchIntent.TRANSACTIONAL
    assert keyword_provider.classify_intent("pg rent price in greater noida") == SearchIntent.TRANSACTIONAL

    # Commercial Investigation
    assert keyword_provider.classify_intent("best pgs near amity university noida") == SearchIntent.COMMERCIAL_INVESTIGATION
    assert keyword_provider.classify_intent("hostels vs flats in kanpur comparison") == SearchIntent.COMMERCIAL_INVESTIGATION

    # Navigational
    assert keyword_provider.classify_intent("galgotias hostel login portal") == SearchIntent.NAVIGATIONAL

    # Informational
    assert keyword_provider.classify_intent("how to pack for college hostel") == SearchIntent.INFORMATIONAL
    assert keyword_provider.classify_intent("cost of living for students in uttar pradesh") == SearchIntent.INFORMATIONAL


def test_business_relevance_scoring(keyword_provider):
    """Test business relevance heuristic scoring."""
    high_rel = keyword_provider.calculate_business_relevance("girls pg in knowledge park 2 greater noida")
    assert high_rel >= 85.0

    low_rel = keyword_provider.calculate_business_relevance("luxury resort for couples in goa")
    assert low_rel <= 30.0


def test_difficulty_heuristic(keyword_provider):
    """Test difficulty estimation based on length and competitive terms."""
    short_head = keyword_provider.estimate_difficulty("pg room")
    long_tail = keyword_provider.estimate_difficulty("budget friendly boys pg near aktu campus lucknow")

    assert short_head > long_tail
    assert long_tail <= 35
