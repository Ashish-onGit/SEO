"""Factual integrity and forbidden claim checks."""

from typing import List
from storage.models import BlogDraft, SEOBrief, QACheckResult
from config.brand_config import brand_config


class FactualChecker:
    """Verifies that the draft adheres to factual integrity and brand claim boundaries."""

    FORBIDDEN_PHRASES = [
        ("i personally visited", "Author claiming personal physical inspection"),
        ("guaranteed 100% refund", "Unsupported absolute financial guarantee"),
        ("free luxury accommodation", "Misleading promotional claim"),
        ("official government partner", "Unsubstantiated government affiliation"),
        ("guaranteed 1st rank on google", "Unsupported SEO ranking guarantee"),
    ]

    def check_claims_and_integrity(self, draft: BlogDraft) -> List[QACheckResult]:
        """Check for forbidden claims, ungrounded guarantees, and price framing."""
        results = []
        md_lower = draft.content_markdown.lower()

        # 1. Forbidden phrase scan
        violations = []
        for phrase, reason in self.FORBIDDEN_PHRASES:
            if phrase in md_lower:
                violations.append(f"'{phrase}' ({reason})")

        if violations:
            results.append(
                QACheckResult(
                    check_name="Forbidden Claims & Personal Statements",
                    status="FAIL",
                    severity="CRITICAL",
                    explanation=f"Draft contains forbidden claims: {'; '.join(violations)}",
                    evidence=violations[0],
                    suggested_correction="Remove personal visit claims or unsubstantiated guarantees.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Forbidden Claims & Personal Statements",
                    status="PASS",
                    severity="MINOR",
                    explanation="No forbidden personal claims or false guarantees detected.",
                )
            )

        # 2. Price disclaimer check
        # If rent numbers (₹) appear, ensure indicative/disclaimer language is present
        if "₹" in draft.content_markdown or "rs." in md_lower or "rupees" in md_lower:
            disclaimer_words = ["indicative", "typical", "range", "subject to", "varies", "approximate", "depending on"]
            has_disclaimer = any(d in md_lower for d in disclaimer_words)

            if has_disclaimer:
                results.append(
                    QACheckResult(
                        check_name="Pricing Integrity & Disclaimer",
                        status="PASS",
                        severity="MINOR",
                        explanation="Rental figures are framed with appropriate indicative ranges and disclaimers.",
                    )
                )
            else:
                results.append(
                    QACheckResult(
                        check_name="Pricing Integrity & Disclaimer",
                        status="WARNING",
                        severity="MAJOR",
                        explanation="Prices are mentioned without clear indicative disclaimers.",
                        suggested_correction="Add a note stating that prices are indicative and subject to room availability.",
                    )
                )

        return results
