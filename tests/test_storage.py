"""Unit tests for SQLite database and repositories."""

import pytest
from pathlib import Path
from storage.database import DatabaseManager
from storage.repositories import PipelineRepository
from storage.models import (
    WorkflowStage,
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


@pytest.fixture
def temp_repo(tmp_path: Path):
    """Fixture providing a fresh in-memory or temp SQLite repository."""
    test_db = tmp_path / "test.db"
    db_mgr = DatabaseManager(test_db)
    db_mgr.initialize()
    return PipelineRepository(db_mgr)


def test_create_and_update_run(temp_repo):
    """Test creating and updating pipeline run."""
    run = temp_repo.create_run("run_20261024_01", "2026-10-24", "INIT")
    assert run.run_id == "run_20261024_01"
    assert run.status == WorkflowStage.INIT

    temp_repo.update_run_status(
        "run_20261024_01",
        WorkflowStage.SELECTED,
        "TOPIC_SELECTED",
        selected_topic="Affordable Student Housing in Greater Noida Knowledge Park",
    )
    updated = temp_repo.get_run("run_20261024_01")
    assert updated.status == WorkflowStage.SELECTED
    assert updated.selected_topic == "Affordable Student Housing in Greater Noida Knowledge Park"


def test_topic_candidates_and_deduplication(temp_repo):
    """Test persisting candidates, selecting, and deduplication history."""
    run_id = "run_test_candidates"
    temp_repo.create_run(run_id, "2026-10-24")

    candidates = [
        TopicCandidate(
            run_id=run_id,
            topic="Best Student PGs near Amity University Noida",
            related_queries=["amity noida hostel fees", "pg sector 125 noida"],
            accommodation_relevance=90.0,
            market="India (Uttar Pradesh)",
        ),
        TopicCandidate(
            run_id=run_id,
            topic="Budget Student Accommodation in Lucknow near AKTU",
            accommodation_relevance=85.0,
            market="India (Uttar Pradesh)",
        ),
    ]
    temp_repo.save_topic_candidates(candidates)
    loaded = temp_repo.get_topic_candidates(run_id)
    assert len(loaded) == 2
    assert loaded[0].related_queries == ["amity noida hostel fees", "pg sector 125 noida"]

    # Mark one selected
    temp_repo.mark_topic_selected(run_id, "Best Student PGs near Amity University Noida")
    temp_repo.update_run_status(run_id, WorkflowStage.SELECTED, "SELECTED", selected_topic="Best Student PGs near Amity University Noida")

    prev_topics = temp_repo.get_previously_covered_topics()
    assert "Best Student PGs near Amity University Noida" in prev_topics


def test_email_idempotency(temp_repo):
    """Test that email idempotency check correctly prevents duplicates."""
    run_id = "run_email_idempotency"
    temp_repo.create_run(run_id, "2026-10-24")

    assert not temp_repo.is_email_already_sent(run_id)

    temp_repo.record_email_delivery(
        run_id=run_id,
        recipient="test@example.com",
        subject="Daily Draft",
        status="SENT",
        message_id="msg_12345",
    )

    assert temp_repo.is_email_already_sent(run_id)
