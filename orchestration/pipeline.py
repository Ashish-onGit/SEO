"""Main Pipeline Orchestrator: executes the end-to-end SEO workflow with stage resumption and error handling."""

import os
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

from config.settings import settings
from storage.database import db_manager
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
)
from storage.repositories import repository, PipelineRepository
from research.trends import GoogleTrendsDiscoveryProvider
from research.keywords import GoogleSuggestKeywordProvider
from research.competitor_analysis import WebCompetitorAnalysisProvider
from selection.topic_scorer import TopicScorer
from ai import get_ai_provider, AIProvider
from content.seo_brief import SEOBriefGenerator
from content.blog_generator import BlogGenerator
from content.document_writer import document_writer
from quality.qa_gate import QAGate
from delivery.gmail_sender import GmailDeliveryProvider
from orchestration.lock import SingleInstanceLock

logger = logging.getLogger(__name__)


class PipelineExecutionError(Exception):
    """Raised when a non-recoverable error stops the pipeline."""
    pass


class SEOPipeline:
    """End-to-end SEO research, brief creation, drafting, QA, and email delivery pipeline."""

    def __init__(
        self,
        ai_provider: Optional[AIProvider] = None,
        repo: Optional[PipelineRepository] = None,
    ):
        self.repo = repo or repository
        self.ai = ai_provider or get_ai_provider()
        self.discovery = GoogleTrendsDiscoveryProvider()
        self.keywords = GoogleSuggestKeywordProvider()
        self.competitors = WebCompetitorAnalysisProvider()
        self.scorer = TopicScorer()
        self.brief_generator = SEOBriefGenerator()
        self.blog_generator = BlogGenerator(self.ai)
        self.qa_gate = QAGate(self.ai)
        self.email_sender = GmailDeliveryProvider(repo=self.repo)

    def generate_run_id(self) -> str:
        """Generate a unique run ID based on date and timestamp."""
        now = datetime.now()
        return f"run_{now.strftime('%Y%m%d_%H%M%S')}"

    def run(self, resume_run_id: Optional[str] = None) -> PipelineRun:
        """Execute the daily SEO automation workflow."""
        # 1. Initialize Database
        db_manager.initialize()

        # 2. Acquire Single Instance Lock
        with SingleInstanceLock():
            if resume_run_id:
                run = self.repo.get_run(resume_run_id)
                if not run:
                    raise PipelineExecutionError(f"Run ID '{resume_run_id}' not found for resumption.")
                logger.info(f"Resuming pipeline run '{run.run_id}' from stage '{run.current_stage}'")
            else:
                run_id = self.generate_run_id()
                today_str = datetime.now().strftime("%Y-%m-%d")
                run = self.repo.create_run(run_id=run_id, date=today_str, current_stage="STAGE_A_DISCOVERY")
                logger.info(f"Initialized new pipeline run '{run.run_id}' for {today_str}")

            try:
                # -------------------------------------------------------------
                # Stage A: Topic Discovery
                # -------------------------------------------------------------
                candidates = self.repo.get_topic_candidates(run.run_id)
                if not candidates:
                    logger.info("Executing Stage A: Topic Discovery...")
                    candidates = self.discovery.discover_topics(run.run_id, count=8)
                    if not candidates:
                        raise PipelineExecutionError("Topic discovery returned zero candidates.")
                    self.repo.save_topic_candidates(candidates)
                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.DISCOVERED, "STAGE_B_KEYWORD_RESEARCH"
                    )

                # -------------------------------------------------------------
                # Stage B: Keyword Research
                # -------------------------------------------------------------
                keywords_by_topic: Dict[str, List[KeywordMetric]] = {}
                existing_kws = self.repo.get_keyword_metrics(run.run_id)
                if existing_kws:
                    for k in existing_kws:
                        keywords_by_topic.setdefault(k.topic, []).append(k)
                else:
                    logger.info("Executing Stage B: Keyword Research for candidates...")
                    for c in candidates:
                        topic_kws = self.keywords.research_keywords(run.run_id, c.topic)
                        self.repo.save_keyword_metrics(topic_kws)
                        keywords_by_topic[c.topic] = topic_kws

                # -------------------------------------------------------------
                # Stage C: Competitor Analysis
                # -------------------------------------------------------------
                competitors_by_topic: Dict[str, List[CompetitorArticle]] = {}
                existing_comps = self.repo.get_competitor_articles(run.run_id)
                if existing_comps:
                    for comp in existing_comps:
                        competitors_by_topic.setdefault(comp.topic, []).append(comp)
                else:
                    logger.info("Executing Stage C: Competitor Analysis for top candidates...")
                    # Analyze competitors for candidate topics
                    for c in candidates[:4]:
                        comps = self.competitors.analyze_competitors(run.run_id, c.topic, max_count=5)
                        self.repo.save_competitor_articles(comps)
                        competitors_by_topic[c.topic] = comps

                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.RESEARCHED, "STAGE_D_TOPIC_SELECTION"
                    )

                # -------------------------------------------------------------
                # Stage D: Topic Scoring and Selection
                # -------------------------------------------------------------
                logger.info("Executing Stage D: Topic Scoring & Selection...")
                previous_topics = self.repo.get_previously_covered_topics()
                best_candidate, best_score, all_scores = self.scorer.select_best_topic(
                    candidates=candidates,
                    keywords_by_topic=keywords_by_topic,
                    competitors_by_topic=competitors_by_topic,
                    previous_topics=previous_topics,
                )
                self.repo.save_topic_scores(all_scores)

                if not best_candidate or not best_score:
                    error_msg = "No discovered candidate met the minimum topic score or business relevance threshold."
                    logger.warning(error_msg)
                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.FAILED, "SELECTION_FAILED", error_message=error_msg
                    )
                    self.email_sender.send_failure_alert(run, "Stage D: Topic Selection", error_msg)
                    return self.repo.get_run(run.run_id)

                self.repo.mark_topic_selected(run.run_id, best_candidate.topic)
                self.repo.update_run_status(
                    run.run_id,
                    WorkflowStage.SELECTED,
                    "STAGE_E_BRIEF_GENERATION",
                    selected_topic=best_candidate.topic,
                )
                logger.info(f"Selected winning topic: '{best_candidate.topic}' (Score: {best_score.total_score:.1f})")

                # -------------------------------------------------------------
                # Stage E: SEO Brief Generation
                # -------------------------------------------------------------
                brief = self.repo.get_seo_brief(run.run_id)
                if not brief:
                    logger.info("Executing Stage E: Generating 20-point structured SEO Brief...")
                    selected_kws = keywords_by_topic.get(best_candidate.topic, [])
                    selected_comps = competitors_by_topic.get(best_candidate.topic, [])
                    brief = self.brief_generator.generate_brief(
                        best_candidate, best_score, selected_kws, selected_comps
                    )
                    self.repo.save_seo_brief(brief)
                    document_writer.write_brief_markdown(brief)
                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.BRIEF_GENERATED, "STAGE_F_BLOG_DRAFTING"
                    )

                # -------------------------------------------------------------
                # Stage F: Blog Draft Generation
                # -------------------------------------------------------------
                draft = self.repo.get_blog_draft(run.run_id)
                if not draft:
                    logger.info("Executing Stage F: Drafting complete blog post with AI...")
                    draft = self.blog_generator.generate_draft(brief, version=1)
                    self.repo.save_blog_draft(draft)
                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.DRAFT_GENERATED, "STAGE_G_QA_CHECK"
                    )

                # -------------------------------------------------------------
                # Stage G: Automated Quality Assurance Gate
                # -------------------------------------------------------------
                qa_report = self.repo.get_qa_report(run.run_id)
                if not qa_report:
                    logger.info("Executing Stage G: Multi-layer Quality Assurance Gate...")
                    qa_report = self.qa_gate.run_qa(draft, brief)
                    self.repo.save_qa_report(qa_report)

                # Handle Bounded Correction Cycle if Critical Failures occurred
                if qa_report.overall_status == "FAILED" and run.retry_count < settings.max_retries:
                    logger.warning(
                        f"Draft failed QA with {len(qa_report.critical_failures)} critical failures. "
                        f"Attempting bounded correction cycle (Attempt {run.retry_count + 1}/{settings.max_retries})..."
                    )
                    # Regenerate draft with corrective feedback
                    draft = self.blog_generator.generate_draft(brief, version=draft.version + 1)
                    self.repo.save_blog_draft(draft)
                    qa_report = self.qa_gate.run_qa(draft, brief)
                    self.repo.save_qa_report(qa_report)

                # Check if still failed
                if qa_report.overall_status == "FAILED":
                    error_msg = f"Draft failed mandatory QA checks: {[c.explanation for c in qa_report.critical_failures]}"
                    logger.error(error_msg)
                    self.repo.update_run_status(
                        run.run_id, WorkflowStage.QA_FAILED, "QA_FAILED", error_message=error_msg
                    )
                    self.email_sender.send_failure_alert(run, "Stage G: Quality Assurance", error_msg)
                    return self.repo.get_run(run.run_id)

                self.repo.update_run_status(
                    run.run_id, WorkflowStage.QA_PASSED, "STAGE_I_DELIVERY"
                )

                # -------------------------------------------------------------
                # Stage I: Output Serialization & Email Delivery
                # -------------------------------------------------------------
                logger.info("Executing Stage I: Writing Markdown artifact and dispatching email report...")
                draft_path = document_writer.write_draft_markdown(draft, brief)

                email_success = self.email_sender.send_daily_report(
                    run=run,
                    topic_score=best_score,
                    brief=brief,
                    draft=draft,
                    qa_report=qa_report,
                    attachment_path=draft_path,
                )

                final_status = WorkflowStage.EMAIL_SENT if email_success else WorkflowStage.QA_PASSED
                self.repo.update_run_status(
                    run.run_id, final_status, "COMPLETED"
                )
                logger.info(f"Pipeline Run '{run.run_id}' completed successfully with status: {final_status.value}")

                return self.repo.get_run(run.run_id)

            except Exception as e:
                logger.exception(f"Unhandled pipeline error during run '{run.run_id}': {e}")
                self.repo.update_run_status(
                    run.run_id, WorkflowStage.FAILED, "CRASHED", error_message=str(e)
                )
                self.email_sender.send_failure_alert(run, "Pipeline Execution Crash", str(e))
                return self.repo.get_run(run.run_id)
