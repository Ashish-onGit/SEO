"""Data access layer / repositories for all pipeline entities."""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from storage.database import DatabaseManager, db_manager
from storage.models import (
    WorkflowStage,
    PipelineRun,
    TopicCandidate,
    KeywordMetric,
    CompetitorArticle,
    TopicScore,
    SEOBrief,
    BlogDraft,
    QAReport,
    QACheckResult,
    SearchIntent,
    MetricProvenance,
)


class PipelineRepository:
    """Repository handling database operations for the SEO pipeline."""

    def __init__(self, db: Optional[DatabaseManager] = None):
        self.db = db or db_manager

    # --- Pipeline Runs ---

    def create_run(self, run_id: str, date: str, current_stage: str = "INIT") -> PipelineRun:
        """Create a new pipeline run."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO pipeline_runs (run_id, date, status, current_stage, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                (run_id, date, WorkflowStage.INIT.value, current_stage),
            )
        return self.get_run(run_id)

    def update_run_status(
        self,
        run_id: str,
        status: WorkflowStage,
        current_stage: str,
        selected_topic: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update run status and progress."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE pipeline_runs
                SET status = ?, current_stage = ?,
                    selected_topic = COALESCE(?, selected_topic),
                    error_message = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE run_id = ?
                """,
                (status.value, current_stage, selected_topic, error_message, run_id),
            )

    def get_run(self, run_id: str) -> Optional[PipelineRun]:
        """Fetch a pipeline run by ID."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM pipeline_runs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row:
                return None
            return PipelineRun(
                run_id=row["run_id"],
                date=row["date"],
                status=WorkflowStage(row["status"]),
                current_stage=row["current_stage"],
                selected_topic=row["selected_topic"],
                error_message=row["error_message"],
                retry_count=row["retry_count"],
            )

    # --- Topic Candidates ---

    def save_topic_candidates(self, candidates: List[TopicCandidate]) -> None:
        """Persist a list of topic candidates."""
        with self.db.get_connection() as conn:
            for c in candidates:
                conn.execute(
                    """
                    INSERT INTO topic_candidates (
                        run_id, topic, related_queries, trend_direction, trend_period,
                        source, market, seasonal_relevance, accommodation_relevance,
                        provenance, is_selected
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        c.run_id,
                        c.topic,
                        json.dumps(c.related_queries),
                        c.trend_direction,
                        c.trend_period,
                        c.source,
                        c.market,
                        c.seasonal_relevance,
                        c.accommodation_relevance,
                        c.provenance.value if hasattr(c.provenance, "value") else str(c.provenance),
                        1 if c.is_selected else 0,
                    ),
                )

    def get_topic_candidates(self, run_id: str) -> List[TopicCandidate]:
        """Fetch all topic candidates for a run."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM topic_candidates WHERE run_id = ?", (run_id,)
            ).fetchall()
            candidates = []
            for r in rows:
                candidates.append(
                    TopicCandidate(
                        id=r["id"],
                        run_id=r["run_id"],
                        topic=r["topic"],
                        related_queries=json.loads(r["related_queries"] or "[]"),
                        trend_direction=r["trend_direction"],
                        trend_period=r["trend_period"],
                        source=r["source"],
                        market=r["market"],
                        seasonal_relevance=r["seasonal_relevance"],
                        accommodation_relevance=r["accommodation_relevance"],
                        provenance=MetricProvenance(r["provenance"] or "estimated"),
                        is_selected=bool(r["is_selected"]),
                    )
                )
            return candidates

    def mark_topic_selected(self, run_id: str, topic: str) -> None:
        """Mark a specific candidate as selected."""
        with self.db.get_connection() as conn:
            conn.execute(
                "UPDATE topic_candidates SET is_selected = 1 WHERE run_id = ? AND topic = ?",
                (run_id, topic),
            )

    def get_previously_covered_topics(self, limit: int = 100) -> List[str]:
        """Fetch historically selected or drafted topics for deduplication."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT DISTINCT topic FROM blog_drafts
                UNION
                SELECT DISTINCT selected_topic FROM pipeline_runs WHERE selected_topic IS NOT NULL
                ORDER BY 1 DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [r[0] for r in rows if r[0]]

    # --- Keyword Metrics ---

    def save_keyword_metrics(self, metrics: List[KeywordMetric]) -> None:
        """Persist keyword metrics."""
        with self.db.get_connection() as conn:
            for k in metrics:
                conn.execute(
                    """
                    INSERT INTO keyword_metrics (
                        run_id, topic, keyword, search_volume, measurement_period,
                        trend_direction, difficulty, search_intent, geographic_relevance,
                        business_relevance, source, provenance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        k.run_id,
                        k.topic,
                        k.keyword,
                        k.search_volume,
                        k.measurement_period,
                        k.trend_direction,
                        k.difficulty,
                        k.search_intent.value if hasattr(k.search_intent, "value") else str(k.search_intent),
                        k.geographic_relevance,
                        k.business_relevance,
                        k.source,
                        k.provenance.value if hasattr(k.provenance, "value") else str(k.provenance),
                    ),
                )

    def get_keyword_metrics(self, run_id: str, topic: Optional[str] = None) -> List[KeywordMetric]:
        """Fetch keyword metrics."""
        with self.db.get_connection() as conn:
            if topic:
                rows = conn.execute(
                    "SELECT * FROM keyword_metrics WHERE run_id = ? AND topic = ?",
                    (run_id, topic),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM keyword_metrics WHERE run_id = ?", (run_id,)
                ).fetchall()

            result = []
            for r in rows:
                result.append(
                    KeywordMetric(
                        id=r["id"],
                        run_id=r["run_id"],
                        topic=r["topic"],
                        keyword=r["keyword"],
                        search_volume=r["search_volume"],
                        measurement_period=r["measurement_period"],
                        trend_direction=r["trend_direction"],
                        difficulty=r["difficulty"],
                        search_intent=SearchIntent(r["search_intent"]),
                        geographic_relevance=r["geographic_relevance"],
                        business_relevance=r["business_relevance"],
                        source=r["source"],
                        provenance=MetricProvenance(r["provenance"] or "estimated"),
                    )
                )
            return result

    # --- Competitor Articles ---

    def save_competitor_articles(self, articles: List[CompetitorArticle]) -> None:
        """Persist competitor articles."""
        with self.db.get_connection() as conn:
            for art in articles:
                conn.execute(
                    """
                    INSERT INTO competitor_articles (
                        run_id, topic, title, url, domain, search_query, search_position,
                        headings, content_summary, freshness, coverage_gaps,
                        traffic_estimate, word_count
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        art.run_id,
                        art.topic,
                        art.title,
                        art.url,
                        art.domain,
                        art.search_query,
                        art.search_position,
                        json.dumps(art.headings),
                        art.content_summary,
                        art.freshness,
                        json.dumps(art.coverage_gaps),
                        art.traffic_estimate,
                        art.word_count,
                    ),
                )

    def get_competitor_articles(self, run_id: str, topic: Optional[str] = None) -> List[CompetitorArticle]:
        """Retrieve competitor articles for a run."""
        with self.db.get_connection() as conn:
            if topic:
                rows = conn.execute(
                    "SELECT * FROM competitor_articles WHERE run_id = ? AND topic = ?",
                    (run_id, topic),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM competitor_articles WHERE run_id = ?", (run_id,)
                ).fetchall()

            result = []
            for r in rows:
                result.append(
                    CompetitorArticle(
                        id=r["id"],
                        run_id=r["run_id"],
                        topic=r["topic"],
                        title=r["title"],
                        url=r["url"],
                        domain=r["domain"],
                        search_query=r["search_query"],
                        search_position=r["search_position"],
                        headings=json.loads(r["headings"] or "[]"),
                        content_summary=r["content_summary"] or "",
                        freshness=r["freshness"] or "unknown",
                        coverage_gaps=json.loads(r["coverage_gaps"] or "[]"),
                        traffic_estimate=r["traffic_estimate"],
                        word_count=r["word_count"],
                    )
                )
            return result

    # --- Topic Scores ---

    def save_topic_scores(self, scores: List[TopicScore]) -> None:
        """Persist topic scores."""
        with self.db.get_connection() as conn:
            for s in scores:
                conn.execute(
                    """
                    INSERT INTO topic_scores (
                        run_id, topic, accommodation_relevance_score, trend_opportunity_score,
                        ranking_opportunity_score, business_value_score, total_score,
                        rationale, evidence_breakdown
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        s.run_id,
                        s.topic,
                        s.accommodation_relevance_score,
                        s.trend_opportunity_score,
                        s.ranking_opportunity_score,
                        s.business_value_score,
                        s.total_score,
                        s.rationale,
                        json.dumps(s.evidence_breakdown),
                    ),
                )

    def get_topic_scores(self, run_id: str) -> List[TopicScore]:
        """Retrieve topic scores for a run."""
        with self.db.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM topic_scores WHERE run_id = ? ORDER BY total_score DESC",
                (run_id,),
            ).fetchall()
            result = []
            for r in rows:
                result.append(
                    TopicScore(
                        id=r["id"],
                        run_id=r["run_id"],
                        topic=r["topic"],
                        accommodation_relevance_score=r["accommodation_relevance_score"],
                        trend_opportunity_score=r["trend_opportunity_score"],
                        ranking_opportunity_score=r["ranking_opportunity_score"],
                        business_value_score=r["business_value_score"],
                        total_score=r["total_score"],
                        rationale=r["rationale"],
                        evidence_breakdown=json.loads(r["evidence_breakdown"] or "{}"),
                    )
                )
            return result

    # --- SEO Brief ---

    def save_seo_brief(self, brief: SEOBrief) -> None:
        """Persist an SEO brief."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO seo_briefs (
                    run_id, topic, primary_keyword, secondary_keywords, search_intent,
                    target_audience, geographic_focus, suggested_title, suggested_h1,
                    suggested_meta_description, suggested_slug, outline, word_count_guidance,
                    target_faqs, competitor_insights, content_gaps, recommended_internal_links,
                    suggested_external_sources, required_factual_claims, editorial_cautions
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brief.run_id,
                    brief.topic,
                    brief.primary_keyword,
                    json.dumps(brief.secondary_keywords),
                    brief.search_intent.value if hasattr(brief.search_intent, "value") else str(brief.search_intent),
                    brief.target_audience,
                    brief.geographic_focus,
                    brief.suggested_title,
                    brief.suggested_h1,
                    brief.suggested_meta_description,
                    brief.suggested_slug,
                    json.dumps(brief.outline),
                    brief.word_count_guidance,
                    json.dumps(brief.target_faqs),
                    brief.competitor_insights,
                    json.dumps(brief.content_gaps),
                    json.dumps(brief.recommended_internal_links),
                    json.dumps(brief.suggested_external_sources),
                    json.dumps(brief.required_factual_claims),
                    json.dumps(brief.editorial_cautions),
                ),
            )

    def get_seo_brief(self, run_id: str) -> Optional[SEOBrief]:
        """Fetch the SEO brief for a run."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM seo_briefs WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row:
                return None
            return SEOBrief(
                id=row["id"],
                run_id=row["run_id"],
                topic=row["topic"],
                primary_keyword=row["primary_keyword"],
                secondary_keywords=json.loads(row["secondary_keywords"] or "[]"),
                search_intent=SearchIntent(row["search_intent"]),
                target_audience=row["target_audience"],
                geographic_focus=row["geographic_focus"],
                suggested_title=row["suggested_title"],
                suggested_h1=row["suggested_h1"],
                suggested_meta_description=row["suggested_meta_description"],
                suggested_slug=row["suggested_slug"],
                outline=json.loads(row["outline"] or "[]"),
                word_count_guidance=row["word_count_guidance"],
                target_faqs=json.loads(row["target_faqs"] or "[]"),
                competitor_insights=row["competitor_insights"] or "",
                content_gaps=json.loads(row["content_gaps"] or "[]"),
                recommended_internal_links=json.loads(row["recommended_internal_links"] or "[]"),
                suggested_external_sources=json.loads(row["suggested_external_sources"] or "[]"),
                required_factual_claims=json.loads(row["required_factual_claims"] or "[]"),
                editorial_cautions=json.loads(row["editorial_cautions"] or "[]"),
            )

    # --- Blog Draft ---

    def save_blog_draft(self, draft: BlogDraft) -> None:
        """Persist a blog draft."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO blog_drafts (
                    run_id, topic, title, slug, meta_description,
                    content_markdown, word_count, version, citations
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    draft.run_id,
                    draft.topic,
                    draft.title,
                    draft.slug,
                    draft.meta_description,
                    draft.content_markdown,
                    draft.word_count,
                    draft.version,
                    json.dumps(draft.citations),
                ),
            )

    def get_blog_draft(self, run_id: str) -> Optional[BlogDraft]:
        """Fetch the blog draft for a run."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM blog_drafts WHERE run_id = ? ORDER BY version DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            if not row:
                return None
            return BlogDraft(
                id=row["id"],
                run_id=row["run_id"],
                topic=row["topic"],
                title=row["title"],
                slug=row["slug"],
                meta_description=row["meta_description"],
                content_markdown=row["content_markdown"],
                word_count=row["word_count"],
                version=row["version"],
                citations=json.loads(row["citations"] or "[]"),
            )

    # --- QA Report ---

    def save_qa_report(self, report: QAReport) -> None:
        """Persist a QA report."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO qa_reports (
                    run_id, overall_status, deterministic_passed, ai_review_passed,
                    critical_failures, major_warnings, minor_warnings, all_checks,
                    originality_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report.run_id,
                    report.overall_status,
                    1 if report.deterministic_passed else 0,
                    1 if report.ai_review_passed else 0,
                    json.dumps([c.model_dump() for c in report.critical_failures]),
                    json.dumps([c.model_dump() for c in report.major_warnings]),
                    json.dumps([c.model_dump() for c in report.minor_warnings]),
                    json.dumps([c.model_dump() for c in report.all_checks]),
                    report.originality_status,
                ),
            )

    def get_qa_report(self, run_id: str) -> Optional[QAReport]:
        """Fetch the QA report for a run."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM qa_reports WHERE run_id = ?", (run_id,)
            ).fetchone()
            if not row:
                return None
            return QAReport(
                id=row["id"],
                run_id=row["run_id"],
                overall_status=row["overall_status"],
                deterministic_passed=bool(row["deterministic_passed"]),
                ai_review_passed=bool(row["ai_review_passed"]),
                critical_failures=[QACheckResult(**c) for c in json.loads(row["critical_failures"] or "[]")],
                major_warnings=[QACheckResult(**c) for c in json.loads(row["major_warnings"] or "[]")],
                minor_warnings=[QACheckResult(**c) for c in json.loads(row["minor_warnings"] or "[]")],
                all_checks=[QACheckResult(**c) for c in json.loads(row["all_checks"] or "[]")],
                originality_status=row["originality_status"],
            )

    # --- Email Deliveries ---

    def is_email_already_sent(self, run_id: str) -> bool:
        """Check if email has already been successfully delivered for this run."""
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT id FROM email_deliveries WHERE run_id = ? AND status = 'SENT'",
                (run_id,),
            ).fetchone()
            return row is not None

    def record_email_delivery(
        self,
        run_id: str,
        recipient: str,
        subject: str,
        status: str,
        delivery_method: str = "gmail_api",
        message_id: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Record an email delivery attempt."""
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO email_deliveries (
                    run_id, recipient, subject, status, delivery_method, message_id, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (run_id, recipient, subject, status, delivery_method, message_id, error_message),
            )


repository = PipelineRepository()
