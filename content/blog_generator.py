"""Blog draft generator utilizing AIProvider and approved SEO brief."""

import re
import logging
from typing import Optional
from storage.models import SEOBrief, BlogDraft
from ai.provider import AIProvider
from ai.prompts import BLOG_GENERATOR_SYSTEM_PROMPT, build_blog_draft_prompt

logger = logging.getLogger(__name__)


class BlogGenerator:
    """Generates complete first drafts strictly adhering to the approved SEO brief."""

    def __init__(self, ai_provider: AIProvider):
        self.ai = ai_provider

    def generate_draft(self, brief: SEOBrief, version: int = 1) -> BlogDraft:
        """Call AI provider and construct the BlogDraft model."""
        prompt = build_blog_draft_prompt(brief)
        logger.info(f"Generating blog draft for topic '{brief.topic}' via {self.ai.__class__.__name__}...")

        raw_content = self.ai.generate_text(
            prompt=prompt,
            system_instruction=BLOG_GENERATOR_SYSTEM_PROMPT,
        )

        # Clean markdown code fences if output was wrapped
        content = raw_content.strip()
        if content.startswith("```markdown"):
            content = content[11:]
        elif content.startswith("```md") or content.startswith("```"):
            content = content[content.find("\n") + 1 :]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()

        # Extract title from H1 or fallback to suggested_title
        h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
        title = h1_match.group(1).strip() if h1_match else brief.suggested_title

        # Calculate word count
        words = content.split()
        word_count = len(words)

        # Extract citations / external sources mentioned
        citations = []
        for ext in brief.suggested_external_sources:
            if ext.get("url") and ext.get("url") in content:
                citations.append({"name": ext.get("name", "Source"), "url": ext.get("url", "")})

        draft = BlogDraft(
            run_id=brief.run_id,
            topic=brief.topic,
            title=title,
            slug=brief.suggested_slug,
            meta_description=brief.suggested_meta_description,
            content_markdown=content,
            word_count=word_count,
            version=version,
            citations=citations,
        )

        logger.info(f"Successfully generated draft '{title}' ({word_count} words)")
        return draft
