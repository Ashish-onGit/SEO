"""Research module package."""

from research.base import TopicDiscoveryProvider, KeywordResearchProvider, CompetitorSearchProvider
from research.trends import GoogleTrendsDiscoveryProvider
from research.keywords import GoogleSuggestKeywordProvider
from research.competitor_analysis import WebCompetitorAnalysisProvider
from research.source_retrieval import SourceRegistry

__all__ = [
    "TopicDiscoveryProvider",
    "KeywordResearchProvider",
    "CompetitorSearchProvider",
    "GoogleTrendsDiscoveryProvider",
    "GoogleSuggestKeywordProvider",
    "WebCompetitorAnalysisProvider",
    "SourceRegistry",
]
