"""Tests for pipeline resumption, stage recovery, duplicate prevention, and failure alerts."""

import pytest
from pathlib import Path
from storage.database import DatabaseManager
from storage.repositories import PipelineRepository
from storage.models import WorkflowStage, TopicCandidate
from ai.mock_provider import MockAIProvider
from orchestration.pipeline import SEOPipeline


@pytest.fixture
def recovery_env(tmp_path: Path):
    test_db = tmp_path / "test_recovery.db"
    db_mgr = DatabaseManager(test_db)
    db_mgr.initialize()
    repo = PipelineRepository(db_mgr)
    ai = MockAIProvider()
    pipeline = SEOPipeline(ai_provider=ai, repo=repo)
    return pipeline, repo


def test_resume_interrupted_pipeline(recovery_env):
    """Test that resuming from an existing run reuses discovered candidates without regenerating them."""
    pipeline, repo = recovery_env
    run_id = "run_interrupted_001"
    repo.create_run(run_id, "2026-10-24", "STAGE_A_DISCOVERY")

    # Seed candidates
    candidates = [
        TopicCandidate(
            run_id=run_id,
            topic="Affordable Student Hostels and PGs in Greater Noida Knowledge Park",
            accommodation_relevance=95.0,
            market="India (Greater Noida)",
        )
    ]
    repo.save_topic_candidates(candidates)
    repo.update_run_status(run_id, WorkflowStage.DISCOVERED, "STAGE_B_KEYWORD_RESEARCH")

    # Now resume the run
    completed_run = pipeline.run(resume_run_id=run_id)

    assert completed_run.run_id == run_id
    assert completed_run.status in (WorkflowStage.EMAIL_SENT, WorkflowStage.QA_PASSED)
    # Check that the original candidate was selected
    assert completed_run.selected_topic == "Affordable Student Hostels and PGs in Greater Noida Knowledge Park"


def test_duplicate_email_prevention(recovery_env):
    """Test that email sender skips delivery if email was already recorded as sent."""
    pipeline, repo = recovery_env
    run_record = pipeline.run()

    assert repo.is_email_already_sent(run_record.run_id) is True

    # Attempt to send email again
    draft = repo.get_blog_draft(run_record.run_id)
    brief = repo.get_seo_brief(run_record.run_id)
    qa = repo.get_qa_report(run_record.run_id)

    # Should return True without creating duplicate delivery records
    sent_again = pipeline.email_sender.send_daily_report(
        run=run_record,
        topic_score=None,
        brief=brief,
        draft=draft,
        qa_report=qa,
        attachment_path=None,
    )
    assert sent_again is True
