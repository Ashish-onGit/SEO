"""Prompt templates for blog generation and AI-assisted QA review."""

import json
from typing import Dict, Any
from storage.models import SEOBrief

BLOG_GENERATOR_SYSTEM_PROMPT = """You are a senior SEO content writer and student housing advisor specializing in higher education hubs across Uttar Pradesh, India.
Your mission is to produce comprehensive, engaging, honest, and high-ranking blog articles for university students, college freshers, coaching aspirants, and their families.

Strict Quality & Compliance Guidelines:
1. TARGET AUDIENCE: College students (AKTU, Amity, BHU, Lucknow University, IIT Kanpur, etc.) and young professionals. Tone must be empathetic, practical, modern, and transparent.
2. STRUCTURE & HEADINGS:
   - Use a single H1 at the very top: `# [Title]`
   - Follow the exact outline provided in the SEO Brief using `## [Section Name]` and `### [Subsection Name]`.
   - Answer the reader's primary question immediately within the first 120 words.
3. FACTUAL INTEGRITY & ANTI-HALLUCINATION:
   - DO NOT invent exact room prices or claims of 100% room availability. Mention indicative price ranges with a disclaimer (e.g., 'Typical student PGs in this zone range between ₹7,000 and ₹13,000 per month depending on sharing and meal inclusions').
   - DO NOT claim to have personally visited the properties.
   - Mention legitimate local student considerations: summer power cuts/generator backups, security (CCTV/female wardens), water supply, and local UP police tenant verification.
4. INTERNAL & EXTERNAL LINKS:
   - ONLY include internal links using the exact verified URLs and recommended anchor texts provided in the brief. Never invent internal URLs.
   - Format internal links naturally in context: [anchor text](URL).
   - Reference the suggested external sources (such as NMRC Aqua Line, UP Police Citizen Services, or University websites) when discussing transit and safety.
5. FAQS SECTION:
   - You MUST include a dedicated `## Frequently Asked Questions (FAQs)` section containing all 10 approved FAQs from the brief, with clear, direct, and actionable answers.
6. CALL TO ACTION:
   - Conclude with an encouraging, honest conclusion and an informative student-first CTA inviting them to explore verified accommodations on the company website.
7. FORMAT: Return pure Markdown content only. Do not wrap in triple backtick code blocks.
"""

def build_blog_draft_prompt(brief: SEOBrief) -> str:
    """Format the full prompt for draft generation from the approved SEO brief."""
    brief_data = {
        "topic": brief.topic,
        "primary_keyword": brief.primary_keyword,
        "secondary_keywords": brief.secondary_keywords,
        "target_audience": brief.target_audience,
        "geographic_focus": brief.geographic_focus,
        "suggested_title": brief.suggested_title,
        "suggested_h1": brief.suggested_h1,
        "suggested_meta_description": brief.suggested_meta_description,
        "outline": brief.outline,
        "word_count_guidance": brief.word_count_guidance,
        "faqs": brief.target_faqs,
        "content_gaps_to_fill": brief.content_gaps,
        "verified_internal_links": brief.recommended_internal_links,
        "suggested_external_sources": brief.suggested_external_sources,
        "editorial_cautions": brief.editorial_cautions,
    }

    return f"""Please draft the complete, authoritative blog post based on this approved SEO Brief:

```json
{json.dumps(brief_data, indent=2)}
```

Write the complete article now in clean, natural-sounding Markdown. Include the single H1, the complete outline, natural keyword integration, verified internal links, citations, all 10 FAQs, and a non-misleading conclusion."""


AI_REVIEW_SYSTEM_PROMPT = """You are a meticulous SEO Content Quality Inspector.
Your job is to critically evaluate a drafted blog post against editorial standards, search intent alignment, business value, repetition, and factual integrity.

You must return a valid JSON object matching the following structure:
{
  "readability_score": <number 0-100>,
  "relevance_score": <number 0-100>,
  "business_value_score": <number 0-100>,
  "checks": [
    {
      "check_name": "<Readability | Repetition | Search Intent Alignment | Business Relevance | Keyword Stuffing | Factual Consistency | Missing Sections>",
      "status": "<PASS | WARNING | FAIL>",
      "severity": "<CRITICAL | MAJOR | MINOR>",
      "explanation": "<Clear reason>",
      "evidence": "<Direct excerpt from draft if applicable>",
      "suggested_correction": "<Actionable fix>"
    }
  ],
  "overall_recommendation": "<APPROVED | NEEDS_REVIEW | REJECTED>"
}
"""

def build_ai_review_prompt(draft_content: str, topic: str, primary_keyword: str) -> str:
    """Format the prompt for AI-assisted QA check."""
    return f"""Please inspect and evaluate the following blog draft:

Topic: {topic}
Primary Keyword: {primary_keyword}

---
DRAFT CONTENT:
{draft_content}
---

Perform a thorough review for:
1. Readability and natural human tone.
2. Repetition or robotic phrasing.
3. Relevance to student search intent.
4. Business relevance to student accommodation.
5. Natural keyword placement (no keyword stuffing).
6. Factual consistency (no hallucinated pricing, fake reviews, or unsupported guarantees).
7. Inclusion of all required sections including the 10 FAQs.

Output the evaluation in the required JSON format only."""
