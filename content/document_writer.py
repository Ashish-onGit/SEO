"""Document writer: formats and saves Markdown drafts, briefs, and HTML artifacts."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from config.settings import settings
from storage.models import BlogDraft, SEOBrief, QAReport, PipelineRun


class DocumentWriter:
    """Manages serialization of drafts and briefs to local filesystem."""

    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or settings.output_dir
        self.drafts_dir = self.output_dir / "drafts"
        self.briefs_dir = self.output_dir / "briefs"
        self.drafts_dir.mkdir(parents=True, exist_ok=True)
        self.briefs_dir.mkdir(parents=True, exist_ok=True)

    def write_draft_markdown(self, draft: BlogDraft, brief: SEOBrief) -> Path:
        """Save the blog draft with YAML frontmatter to a Markdown file."""
        filename = f"{draft.run_id}_{draft.slug}.md"
        file_path = self.drafts_dir / filename

        frontmatter = (
            "---\n"
            f"run_id: \"{draft.run_id}\"\n"
            f"title: \"{draft.title.replace('\"', '\\\"')}\"\n"
            f"slug: \"{draft.slug}\"\n"
            f"meta_description: \"{draft.meta_description.replace('\"', '\\\"')}\"\n"
            f"primary_keyword: \"{brief.primary_keyword}\"\n"
            f"word_count: {draft.word_count}\n"
            f"version: {draft.version}\n"
            f"generated_at: \"{datetime.now().isoformat()}\"\n"
            "---\n\n"
        )

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(frontmatter + draft.content_markdown)

        return file_path

    def write_brief_markdown(self, brief: SEOBrief) -> Path:
        """Save the structured SEO brief to a Markdown file."""
        filename = f"{brief.run_id}_{brief.suggested_slug}_brief.md"
        file_path = self.briefs_dir / filename

        content = [
            f"# SEO Brief: {brief.topic}",
            "",
            f"**Run ID**: `{brief.run_id}`  ",
            f"**Primary Keyword**: `{brief.primary_keyword}`  ",
            f"**Secondary Keywords**: {', '.join(brief.secondary_keywords)}  ",
            f"**Search Intent**: {brief.search_intent.value}  ",
            f"**Target Audience**: {brief.target_audience}  ",
            f"**Geographic Focus**: {brief.geographic_focus}  ",
            "",
            "## Meta Specifications",
            f"- **SEO Title**: {brief.suggested_title}",
            f"- **H1 Tag**: {brief.suggested_h1}",
            f"- **Meta Description**: {brief.suggested_meta_description}",
            f"- **URL Slug**: `/{brief.suggested_slug}`",
            f"- **Word Count Guidance**: {brief.word_count_guidance}",
            "",
            "## Content Outline",
        ]

        for sec in brief.outline:
            content.append(f"### {sec.get('h2')}")
            for sub in sec.get("h3s", []):
                content.append(f"- {sub}")
            content.append("")

        content.extend([
            "## Grounded FAQs",
            "",
        ])
        for idx, faq in enumerate(brief.target_faqs, 1):
            content.append(f"**Q{idx}: {faq.get('question')}**")
            content.append(f"*Guidance*: {faq.get('guidance')}\n")

        content.extend([
            "## Recommended Verified Internal Links",
            "",
        ])
        for link in brief.recommended_internal_links:
            content.append(f"- [{link.get('anchor_text')}]({link.get('url')}) - *{link.get('context')}*")

        content.extend([
            "",
            "## Suggested External Authorities",
            "",
        ])
        for src in brief.suggested_external_sources:
            content.append(f"- [{src.get('name')}]({src.get('url')}) ({src.get('topic')})")

        content.extend([
            "",
            "## Editorial Cautions",
            "",
        ])
        for caution in brief.editorial_cautions:
            content.append(f"- {caution}")

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content))

        return file_path


document_writer = DocumentWriter()
