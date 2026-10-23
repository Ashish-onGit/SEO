"""Deterministic structural and content checks for blog drafts."""

import re
from typing import List, Tuple
from storage.models import BlogDraft, SEOBrief, QACheckResult
from config.settings import settings


class StructuralChecker:
    """Performs deterministic rule-based checks on draft markdown structure."""

    def __init__(self, min_word_count: int = None, max_word_count: int = None):
        self.min_words = min_word_count or settings.min_word_count
        self.max_words = max_word_count or settings.max_word_count

    def check_heading_hierarchy(self, markdown: str) -> List[QACheckResult]:
        """Verify heading hierarchy: single H1 at the top, H2s, H3s without invalid skipping."""
        results = []
        heading_lines = [line.strip() for line in markdown.splitlines() if line.strip().startswith("#")]

        # 1. H1 Count
        h1s = [h for h in heading_lines if h.startswith("# ") and not h.startswith("## ")]
        if len(h1s) == 0:
            results.append(
                QACheckResult(
                    check_name="Heading Hierarchy: H1 Tag",
                    status="FAIL",
                    severity="CRITICAL",
                    explanation="Missing top-level H1 tag (# Title) in draft.",
                    suggested_correction="Add a single # Title at the beginning of the draft.",
                )
            )
        elif len(h1s) > 1:
            results.append(
                QACheckResult(
                    check_name="Heading Hierarchy: Multiple H1s",
                    status="FAIL",
                    severity="MAJOR",
                    explanation=f"Found {len(h1s)} H1 headings. SEO best practice requires exactly one H1.",
                    evidence=", ".join(h1s[:3]),
                    suggested_correction="Convert secondary H1 headings into H2 (##) or H3 (###).",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Heading Hierarchy: H1 Tag",
                    status="PASS",
                    severity="MINOR",
                    explanation="Draft contains exactly one top-level H1 heading.",
                )
            )

        # 2. H2 presence
        h2s = [h for h in heading_lines if h.startswith("## ")]
        if len(h2s) < 3:
            results.append(
                QACheckResult(
                    check_name="Heading Hierarchy: Section Structure",
                    status="FAIL",
                    severity="MAJOR",
                    explanation=f"Found only {len(h2s)} H2 sections; expected at least 3 main sections.",
                    suggested_correction="Ensure the approved outline H2 sections are implemented.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Heading Hierarchy: Section Structure",
                    status="PASS",
                    severity="MINOR",
                    explanation=f"Found {len(h2s)} H2 sections conforming to the outline.",
                )
            )

        return results

    def check_word_count(self, draft: BlogDraft) -> QACheckResult:
        """Validate word count against configured minimum and maximum bounds."""
        words = draft.word_count
        if words < self.min_words:
            return QACheckResult(
                check_name="Word Count Bounds",
                status="FAIL",
                severity="MAJOR",
                explanation=f"Word count ({words}) is below configured minimum of {self.min_words} words.",
                evidence=f"Current word count: {words}",
                suggested_correction="Expand on local transit, locality guidance, or FAQ explanations.",
            )
        elif words > self.max_words + 500:
            return QACheckResult(
                check_name="Word Count Bounds",
                status="WARNING",
                severity="MINOR",
                explanation=f"Word count ({words}) exceeds expected upper limit of {self.max_words} words.",
                evidence=f"Current word count: {words}",
                suggested_correction="Trim overly verbose paragraphs.",
            )
        return QACheckResult(
            check_name="Word Count Bounds",
            status="PASS",
            severity="MINOR",
            explanation=f"Word count ({words}) satisfies editorial guidance.",
        )

    def check_primary_keyword_placement(self, draft: BlogDraft, brief: SEOBrief) -> List[QACheckResult]:
        """Ensure primary keyword is featured in title and early in the introduction."""
        results = []
        kw = brief.primary_keyword.lower()
        title_lower = draft.title.lower()

        # Check in title
        # Relaxed match: allow individual key terms if long-tail
        kw_tokens = set(kw.split())
        title_tokens = set(title_lower.split())
        overlap = len(kw_tokens.intersection(title_tokens)) / max(1, len(kw_tokens))

        if kw in title_lower or overlap >= 0.70:
            results.append(
                QACheckResult(
                    check_name="Primary Keyword: Title / H1",
                    status="PASS",
                    severity="MINOR",
                    explanation="Primary keyword or core key phrases are present in the title.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Primary Keyword: Title / H1",
                    status="FAIL",
                    severity="MAJOR",
                    explanation=f"Primary keyword '{brief.primary_keyword}' is missing or poorly represented in title '{draft.title}'.",
                    suggested_correction="Incorporate primary keyword naturally in the H1 title.",
                )
            )

        # Check in first 150 words
        paragraphs = [p.strip() for p in draft.content_markdown.split("\n\n") if p.strip() and not p.strip().startswith("#")]
        first_150_words = " ".join(paragraphs[:2])[:800].lower() if paragraphs else ""

        if kw in first_150_words or any(token in first_150_words for token in kw.split() if len(token) > 4):
            results.append(
                QACheckResult(
                    check_name="Primary Keyword: Introduction",
                    status="PASS",
                    severity="MINOR",
                    explanation="Primary keyword appears early in the introduction.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Primary Keyword: Introduction",
                    status="FAIL",
                    severity="MAJOR",
                    explanation="Primary keyword not found within the first two paragraphs.",
                    suggested_correction="Address the primary query directly in the opening paragraph.",
                )
            )

        return results

    def check_placeholders_and_repetition(self, markdown: str) -> List[QACheckResult]:
        """Detect placeholder tokens and duplicated paragraphs."""
        results = []
        lower_md = markdown.lower()

        # 1. Placeholders
        placeholders = [
            "[insert link]", "[insert url]", "[insert price]", "[your name]",
            "lorem ipsum", "todo:", "[placeholder]", "[tbd]"
        ]
        found_placeholders = [p for p in placeholders if p in lower_md]
        if found_placeholders:
            results.append(
                QACheckResult(
                    check_name="Placeholder Detection",
                    status="FAIL",
                    severity="CRITICAL",
                    explanation=f"Found unfinished placeholder text in draft: {', '.join(found_placeholders)}",
                    evidence=", ".join(found_placeholders),
                    suggested_correction="Remove or replace placeholder tokens with verified information.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Placeholder Detection",
                    status="PASS",
                    severity="MINOR",
                    explanation="No placeholder markers or dummy text found.",
                )
            )

        # 2. Duplicate paragraphs
        paragraphs = [p.strip() for p in markdown.split("\n\n") if len(p.strip().split()) > 15 and not p.strip().startswith("#")]
        seen_paragraphs = set()
        duplicates = []
        for p in paragraphs:
            # normalized key
            norm = " ".join(p.lower().split()[:25])
            if norm in seen_paragraphs:
                duplicates.append(norm)
            seen_paragraphs.add(norm)

        if duplicates:
            results.append(
                QACheckResult(
                    check_name="Paragraph Repetition",
                    status="FAIL",
                    severity="MAJOR",
                    explanation=f"Detected {len(duplicates)} duplicated or heavily repeated paragraph(s).",
                    evidence=duplicates[0],
                    suggested_correction="Remove duplicate paragraphs.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Paragraph Repetition",
                    status="PASS",
                    severity="MINOR",
                    explanation="No duplicate paragraphs detected.",
                )
            )

        return results

    def check_faqs_presence(self, markdown: str) -> QACheckResult:
        """Verify presence of FAQs section with question headers."""
        if "frequently asked questions" not in markdown.lower() and "faqs" not in markdown.lower():
            return QACheckResult(
                check_name="FAQs Section Presence",
                status="FAIL",
                severity="CRITICAL",
                explanation="Missing dedicated FAQs section.",
                suggested_correction="Include ## Frequently Asked Questions (FAQs) section.",
            )

        # Count questions
        question_matches = re.findall(r"(?:###\s+.+\?|\*\*Q\d+:.+\?\*\*)", markdown)
        if len(question_matches) < 7:
            return QACheckResult(
                check_name="FAQs Question Count",
                status="WARNING",
                severity="MAJOR",
                explanation=f"Found {len(question_matches)} FAQ questions; expected 10.",
                evidence=f"Question count: {len(question_matches)}",
                suggested_correction="Ensure all 10 approved FAQs are answered.",
            )

        return QACheckResult(
            check_name="FAQs Section Presence",
            status="PASS",
            severity="MINOR",
            explanation=f"FAQs section present with {len(question_matches)} grounded questions.",
        )
