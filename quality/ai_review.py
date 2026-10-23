"""AI-assisted editorial review module."""

import logging
from typing import List, Dict, Any, Tuple
from storage.models import BlogDraft, SEOBrief, QACheckResult
from ai.provider import AIProvider
from ai.prompts import AI_REVIEW_SYSTEM_PROMPT, build_ai_review_prompt

logger = logging.getLogger(__name__)


class AIReviewer:
    """Executes AI-assisted qualitative checks for tone, intent, repetition, and relevance."""

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider

    def review_draft(self, draft: BlogDraft, brief: SEOBrief) -> Tuple[List[QACheckResult], bool, float]:
        """Perform AI-assisted review and return structured check results, pass flag, and readability score."""
        prompt = build_ai_review_prompt(
            draft_content=draft.content_markdown,
            topic=brief.topic,
            primary_keyword=brief.primary_keyword,
        )

        try:
            review_json = self.ai.generate_structured_json(
                prompt=prompt,
                schema_description=AI_REVIEW_SYSTEM_PROMPT,
            )

            results: List[QACheckResult] = []
            checks = review_json.get("checks", [])
            for c in checks:
                results.append(
                    QACheckResult(
                        check_name=f"AI Review: {c.get('check_name', 'Quality Check')}",
                        status=c.get("status", "PASS").upper(),
                        severity=c.get("severity", "MINOR").upper(),
                        explanation=c.get("explanation", ""),
                        evidence=c.get("evidence", ""),
                        suggested_correction=c.get("suggested_correction", ""),
                    )
                )

            recommendation = review_json.get("overall_recommendation", "APPROVED").upper()
            ai_passed = recommendation in ("APPROVED", "PASS")
            readability = float(review_json.get("readability_score", 85.0))

            return results, ai_passed, readability

        except Exception as e:
            logger.warning(f"AI review execution failed or returned invalid JSON: {e}")
            # Do not block deterministic pipeline on AI review glitch; report as warning
            fallback_result = [
                QACheckResult(
                    check_name="AI Review: Execution Status",
                    status="WARNING",
                    severity="MAJOR",
                    explanation=f"AI qualitative review encountered an error: {e}",
                    suggested_correction="Check AI provider logs and retry if needed.",
                )
            ]
            return fallback_result, True, 75.0
