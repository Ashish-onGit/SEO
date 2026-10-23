"""End-to-end integration test for the SEO automation pipeline."""

import pytest
from pathlib import Path
from storage.database import DatabaseManager
from storage.repositories import PipelineRepository
from storage.models import WorkflowStage
from ai.mock_provider import MockAIProvider
from orchestration.pipeline import SEOPipeline


@pytest.fixture
def isolated_pipeline(tmp_path: Path):
    """Create an isolated pipeline with temporary database and output paths."""
    test_db = tmp_path / "test_pipeline.db"
    db_mgr = DatabaseManager(test_db)
    db_mgr.initialize()
    repo = PipelineRepository(db_mgr)
    ai = MockAIProvider()

    pipeline = SEOPipeline(ai_provider=ai, repo=repo)
    return pipeline, repo


def test_end_to_end_pipeline_execution(isolated_pipeline):
    """Verify that the pipeline runs end-to-end and satisfies all milestones."""
    pipeline, repo = isolated_pipeline

    run_record = pipeline.run()

    assert run_record is not None
    assert run_record.status in (WorkflowStage.EMAIL_SENT, WorkflowStage.QA_PASSED)
    assert run_record.selected_topic is not None
    assert run_record.current_stage == "COMPLETED"

    # Verify database persistence
    brief = repo.get_seo_brief(run_record.run_id)
    assert brief is not None
    assert len(brief.target_faqs) == 10

    draft = repo.get_blog_draft(run_record.run_id)
    assert draft is not None
    assert draft.word_count >= 800
    assert "# " in draft.content_markdown
    assert "## Frequently Asked Questions" in draft.content_markdown

    qa = repo.get_qa_report(run_record.run_id)
    assert qa is not None
    assert qa.deterministic_passed is True

    # Verify email delivery recorded
    assert repo.is_email_already_sent(run_record.run_id) is True
