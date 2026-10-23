"""Central QA Gate: coordinates deterministic checks, factual review, and AI assessment."""

import logging
from typing import List, Tuple
from storage.models import BlogDraft, SEOBrief, QAReport, QACheckResult
from quality.structural_checks import StructuralChecker
from quality.link_checker import LinkChecker
from quality.factual_checks import FactualChecker
from quality.ai_review import AIReviewer
from quality.originality import OriginalityChecker
from ai.provider import AIProvider

logger = logging.getLogger(__name__)


class QAGate:
    """Multi-stage Quality Assurance Gate enforcing deterministic and AI quality standards."""

    def __init__(self, ai_provider: AIProvider):
        self.structural_checker = StructuralChecker()
        self.link_checker = LinkChecker()
        self.factual_checker = FactualChecker()
        self.ai_reviewer = AIReviewer(ai_provider)
        self.originality_checker = OriginalityChecker()

    def run_qa(self, draft: BlogDraft, brief: SEOBrief) -> QAReport:
        """Run all QA checks and compile structured QAReport."""
        all_checks: List[QACheckResult] = []

        # 1. Deterministic Structural Checks
        heading_checks = self.structural_checker.check_heading_hierarchy(draft.content_markdown)
        all_checks.extend(heading_checks)

        word_check = self.structural_checker.check_word_count(draft)
        all_checks.append(word_check)

        kw_checks = self.structural_checker.check_primary_keyword_placement(draft, brief)
        all_checks.extend(kw_checks)

        placeholder_checks = self.structural_checker.check_placeholders_and_repetition(draft.content_markdown)
        all_checks.extend(placeholder_checks)

        faqs_check = self.structural_checker.check_faqs_presence(draft.content_markdown)
        all_checks.append(faqs_check)

        # 2. Deterministic Link & Internal URL Checks
        link_checks = self.link_checker.validate_links(draft)
        all_checks.extend(link_checks)

        # 3. Factual & Forbidden Claim Checks
        factual_checks = self.factual_checker.check_claims_and_integrity(draft)
        all_checks.extend(factual_checks)

        # Evaluate deterministic pass status
        deterministic_passed = not any(c.status == "FAIL" and c.severity == "CRITICAL" for c in all_checks)

        # 4. Originality Transparency Check
        orig_check, originality_status = self.originality_checker.check_originality(draft.content_markdown)
        all_checks.append(orig_check)

        # 5. AI-assisted Qualitative Review
        ai_checks, ai_passed, _ = self.ai_reviewer.review_draft(draft, brief)
        all_checks.extend(ai_checks)

        # Segregate by severity
        critical_failures = [c for c in all_checks if c.status == "FAIL" and c.severity == "CRITICAL"]
        major_warnings = [c for c in all_checks if (c.status in ("FAIL", "WARNING")) and c.severity == "MAJOR"]
        minor_warnings = [c for c in all_checks if (c.status in ("FAIL", "WARNING")) and c.severity == "MINOR"]

        # Calculate overall status
        # Critical rule: AI-generated QA results must not override mandatory deterministic failures
        if critical_failures or not deterministic_passed:
            overall_status = "FAILED"
        elif major_warnings:
            overall_status = "WARNING"  # Requires human review
        else:
            overall_status = "PASSED"

        report = QAReport(
            run_id=draft.run_id,
            overall_status=overall_status,
            deterministic_passed=deterministic_passed,
            ai_review_passed=ai_passed,
            critical_failures=critical_failures,
            major_warnings=major_warnings,
            minor_warnings=minor_warnings,
            all_checks=all_checks,
            originality_status=originality_status,
        )

        logger.info(
            f"QA Gate completed for run '{draft.run_id}': Status={overall_status} "
            f"(Critical: {len(critical_failures)}, Major: {len(major_warnings)}, Minor: {len(minor_warnings)})"
        )
        return report
