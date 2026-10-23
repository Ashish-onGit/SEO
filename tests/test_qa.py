"""Unit tests for QA checks, deterministic rules, link validation, and quality gates."""

import pytest
from storage.models import BlogDraft, SEOBrief, SearchIntent
from quality.structural_checks import StructuralChecker
from quality.link_checker import LinkChecker
from quality.factual_checks import FactualChecker
from quality.qa_gate import QAGate
from ai.mock_provider import MockAIProvider


@pytest.fixture
def mock_brief():
    return SEOBrief(
        run_id="run_qa_test",
        topic="Student Hostels in Greater Noida",
        primary_keyword="student hostels in greater noida",
        secondary_keywords=["pg near knowledge park", "hostel rent greater noida"],
        search_intent=SearchIntent.TRANSACTIONAL,
        target_audience="Students",
        geographic_focus="Greater Noida",
        suggested_title="Student Hostels in Greater Noida: Complete Guide",
        suggested_h1="Student Hostels in Greater Noida: Complete Guide",
        suggested_meta_description="Find verified student hostels in Greater Noida with pricing, mess facilities, and metro access.",
        suggested_slug="student-hostels-greater-noida",
        word_count_guidance="1100 to 1600 words",
    )


def test_missing_h1_fails_critical():
    """Test that missing H1 is caught as a CRITICAL failure."""
    checker = StructuralChecker()
    bad_md = "## Section 1\nSome introductory text.\n### Sub 1\nDetails."
    results = checker.check_heading_hierarchy(bad_md)

    critical_fails = [r for r in results if r.status == "FAIL" and r.severity == "CRITICAL"]
    assert len(critical_fails) == 1
    assert "H1 Tag" in critical_fails[0].check_name


def test_unverified_internal_link_fails_critical(mock_brief):
    """Test that inventing an unverified internal link triggers CRITICAL failure."""
    checker = LinkChecker()
    draft = BlogDraft(
        run_id="run_qa_test",
        topic=mock_brief.topic,
        title="Student Hostels in Greater Noida",
        slug="student-hostels-greater-noida",
        meta_description="Test meta",
        content_markdown=(
            "# Student Hostels in Greater Noida\n\n"
            "Check our [invented secret page](https://campusnest-up.example.com/fake-hallucinated-property-page) for booking.\n"
        ),
        word_count=50,
    )

    results = checker.validate_links(draft)
    critical_fails = [r for r in results if r.status == "FAIL" and r.severity == "CRITICAL"]
    assert len(critical_fails) == 1
    assert "unverified internal link" in critical_fails[0].explanation.lower()


def test_forbidden_claims_detected(mock_brief):
    """Test detection of forbidden personal claims."""
    checker = FactualChecker()
    draft = BlogDraft(
        run_id="run_qa_test",
        topic=mock_brief.topic,
        title="Student Hostels in Greater Noida",
        slug="student-hostels-greater-noida",
        meta_description="Test meta",
        content_markdown=(
            "# Student Hostels in Greater Noida\n\n"
            "I personally visited all these properties yesterday and verified them.\n"
        ),
        word_count=50,
    )

    results = checker.check_claims_and_integrity(draft)
    critical_fails = [r for r in results if r.status == "FAIL" and r.severity == "CRITICAL"]
    assert len(critical_fails) == 1
    assert "Author claiming personal physical inspection" in critical_fails[0].explanation


def test_qa_gate_passes_valid_draft(mock_brief):
    """Test that a compliant draft passes the full QA Gate."""
    ai = MockAIProvider()
    gate = QAGate(ai)

    valid_md = ai.generate_text(f'{{"topic": "{mock_brief.topic}"}}')
    draft = BlogDraft(
        run_id="run_qa_test",
        topic=mock_brief.topic,
        title="Student Hostels in Greater Noida: The Ultimate Guide",
        slug=mock_brief.suggested_slug,
        meta_description=mock_brief.suggested_meta_description,
        content_markdown=valid_md,
        word_count=len(valid_md.split()),
    )

    report = gate.run_qa(draft, mock_brief)
    assert report.deterministic_passed is True
    assert len(report.critical_failures) == 0
    assert report.overall_status in ("PASSED", "WARNING")
