"""Domain models for storage and pipeline data exchange."""

from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class WorkflowStage(str, Enum):
    """Pipeline execution stages and statuses."""
    INIT = "INIT"
    DISCOVERED = "DISCOVERED"
    RESEARCHED = "RESEARCHED"
    SELECTED = "SELECTED"
    BRIEF_GENERATED = "BRIEF_GENERATED"
    DRAFT_GENERATED = "DRAFT_GENERATED"
    QA_PASSED = "QA_PASSED"
    QA_FAILED = "QA_FAILED"
    EMAIL_SENT = "EMAIL_SENT"
    FAILED = "FAILED"


class SearchIntent(str, Enum):
    """Keyword search intent classifications."""
    INFORMATIONAL = "Informational"
    COMMERCIAL_INVESTIGATION = "Commercial Investigation"
    TRANSACTIONAL = "Transactional"
    NAVIGATIONAL = "Navigational"


class MetricProvenance(str, Enum):
    """Data provenance tag for metrics."""
    MEASURED = "measured"
    ESTIMATED = "estimated"
    UNAVAILABLE = "unavailable"


class TopicCandidate(BaseModel):
    """A topic candidate discovered from trends, search console, or seeds."""
    id: Optional[int] = None
    run_id: str
    topic: str
    related_queries: List[str] = Field(default_factory=list)
    trend_direction: str = "stable"  # rising, falling, stable, seasonal
    trend_period: str = "past_30_days"
    source: str = "google_trends"
    market: str = "India (Uttar Pradesh)"
    seasonal_relevance: str = "year-round"
    accommodation_relevance: float = 70.0  # 0 to 100
    provenance: MetricProvenance = MetricProvenance.ESTIMATED
    is_selected: bool = False
    created_at: Optional[datetime] = None


class KeywordMetric(BaseModel):
    """Keyword metric entry."""
    id: Optional[int] = None
    run_id: str
    topic: str
    keyword: str
    search_volume: Optional[int] = None
    measurement_period: str = "recent_monthly_estimate"
    trend_direction: str = "stable"
    difficulty: Optional[int] = None  # 0 to 100
    search_intent: SearchIntent = SearchIntent.INFORMATIONAL
    geographic_relevance: str = "Uttar Pradesh"
    business_relevance: float = 70.0  # 0 to 100
    source: str = "google_suggest_expanded"
    provenance: MetricProvenance = MetricProvenance.ESTIMATED
    created_at: Optional[datetime] = None


class CompetitorArticle(BaseModel):
    """Scraped / analyzed competitor article."""
    id: Optional[int] = None
    run_id: str
    topic: str
    title: str
    url: str
    domain: str
    search_query: str
    search_position: Optional[int] = None  # None if not verified SERP position
    headings: List[str] = Field(default_factory=list)
    content_summary: str = ""
    freshness: str = "unknown"  # recent, dated, unknown
    coverage_gaps: List[str] = Field(default_factory=list)
    traffic_estimate: Optional[str] = None
    word_count: Optional[int] = None
    created_at: Optional[datetime] = None


class TopicScore(BaseModel):
    """Calculated score and rationales for a candidate topic."""
    id: Optional[int] = None
    run_id: str
    topic: str
    accommodation_relevance_score: float  # 0-100
    trend_opportunity_score: float       # 0-100
    ranking_opportunity_score: float     # 0-100
    business_value_score: float          # 0-100
    total_score: float                   # 0-100
    rationale: str = ""
    evidence_breakdown: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None


class SEOBrief(BaseModel):
    """Structured SEO brief produced for the approved topic."""
    id: Optional[int] = None
    run_id: str
    topic: str
    primary_keyword: str
    secondary_keywords: List[str] = Field(default_factory=list)
    search_intent: SearchIntent
    target_audience: str
    geographic_focus: str
    suggested_title: str
    suggested_h1: str
    suggested_meta_description: str
    suggested_slug: str
    outline: List[Dict[str, Any]] = Field(default_factory=list)  # H2/H3 hierarchy
    word_count_guidance: str
    target_faqs: List[Dict[str, str]] = Field(default_factory=list)  # 10 questions and answer briefs
    competitor_insights: str = ""
    content_gaps: List[str] = Field(default_factory=list)
    recommended_internal_links: List[Dict[str, str]] = Field(default_factory=list)
    suggested_external_sources: List[Dict[str, str]] = Field(default_factory=list)
    required_factual_claims: List[str] = Field(default_factory=list)
    editorial_cautions: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class BlogDraft(BaseModel):
    """Generated blog draft."""
    id: Optional[int] = None
    run_id: str
    topic: str
    title: str
    slug: str
    meta_description: str
    content_markdown: str
    word_count: int = 0
    version: int = 1
    citations: List[Dict[str, str]] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class QACheckResult(BaseModel):
    """Individual QA check result."""
    check_name: str
    status: str  # PASS, FAIL, WARNING
    severity: str  # CRITICAL, MAJOR, MINOR
    explanation: str
    evidence: str = ""
    suggested_correction: str = ""


class QAReport(BaseModel):
    """Aggregated QA report."""
    id: Optional[int] = None
    run_id: str
    overall_status: str  # PASSED, FAILED, WARNING
    deterministic_passed: bool
    ai_review_passed: bool
    critical_failures: List[QACheckResult] = Field(default_factory=list)
    major_warnings: List[QACheckResult] = Field(default_factory=list)
    minor_warnings: List[QACheckResult] = Field(default_factory=list)
    all_checks: List[QACheckResult] = Field(default_factory=list)
    originality_status: str = "External originality verification not configured (AI originality review passed)"
    created_at: Optional[datetime] = None


class PipelineRun(BaseModel):
    """Execution status record for a single automated run."""
    run_id: str
    date: str
    status: WorkflowStage
    current_stage: str
    selected_topic: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
