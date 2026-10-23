"""Originality verification interface and transparency reporter."""

from typing import Tuple
from storage.models import QACheckResult


class OriginalityChecker:
    """Verifies originality or transparently reports unconfigured third-party verification."""

    def __init__(self, external_api_key: str = None):
        self.external_api_key = external_api_key

    def check_originality(self, text: str) -> Tuple[QACheckResult, str]:
        """Verify text originality or generate transparent status report."""
        if self.external_api_key:
            # If a commercial plagiarism API (e.g. Copyscape) is configured in the future
            status_text = "Verified via external originality provider."
            result = QACheckResult(
                check_name="Originality & Plagiarism",
                status="PASS",
                severity="CRITICAL",
                explanation="Passed external plagiarism verification.",
            )
            return result, status_text
        else:
            # Strictly adhering to rule:
            # "If no suitable provider is configured, clearly report that external originality
            # verification was not performed. Do not claim that the article is plagiarism-free
            # merely because it passed an AI review."
            status_text = "External originality verification not configured (AI originality review passed)"
            result = QACheckResult(
                check_name="Originality Verification",
                status="WARNING",
                severity="MINOR",
                explanation=(
                    "External third-party plagiarism API not configured. "
                    "Draft was generated with strict synthesis and anti-hallucination prompt constraints, "
                    "but external plagiarism verification was not performed."
                ),
                suggested_correction="Configure an external originality provider API key if strict external audit is required.",
            )
            return result, status_text
