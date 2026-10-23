"""Base interfaces and utilities for research providers."""

from abc import ABC, abstractmethod
from typing import List, Optional
from storage.models import TopicCandidate, KeywordMetric, CompetitorArticle


class TopicDiscoveryProvider(ABC):
    """Abstract interface for discovering candidate topics."""

    @abstractmethod
    def discover_topics(self, run_id: str, count: int = 8) -> List[TopicCandidate]:
        """Discover candidate topics."""
        pass


class KeywordResearchProvider(ABC):
    """Abstract interface for keyword research."""

    @abstractmethod
    def research_keywords(self, run_id: str, topic: str) -> List[KeywordMetric]:
        """Collect keyword metrics for a candidate topic."""
        pass


class CompetitorSearchProvider(ABC):
    """Abstract interface for competitor discovery and page analysis."""

    @abstractmethod
    def analyze_competitors(self, run_id: str, topic: str, max_count: int = 5) -> List[CompetitorArticle]:
        """Find and analyze competing articles for a topic."""
        pass
