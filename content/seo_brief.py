"""SEO Brief Generator: produces structured, evidence-grounded 20-point briefs."""

import re
import logging
from typing import List, Dict, Any, Optional
from storage.models import TopicCandidate, KeywordMetric, CompetitorArticle, TopicScore, SEOBrief, SearchIntent
from config.brand_config import brand_config
from research.source_retrieval import SourceRegistry

logger = logging.getLogger(__name__)


class SEOBriefGenerator:
    """Generates comprehensive, structured SEO briefs adhering to editorial and business rules."""

    def slugify(self, text: str) -> str:
        """Create a clean URL slug from text."""
        text = text.lower()
        text = re.sub(r"[^\w\s-]", "", text)
        return re.sub(r"[-\s]+", "-", text).strip("-")

    def generate_brief(
        self,
        candidate: TopicCandidate,
        score: TopicScore,
        keywords: List[KeywordMetric],
        competitors: List[CompetitorArticle],
    ) -> SEOBrief:
        """Build the full 20-point SEO brief."""
        topic = candidate.topic

        # 1. Primary Keyword: Most relevant high-intent keyword or the topic itself
        primary_kw = keywords[0].keyword if keywords else topic
        # Sort secondary keywords excluding primary
        secondary_kws = [k.keyword for k in keywords if k.keyword.lower() != primary_kw.lower()][:6]

        # 2. Search Intent
        intent = keywords[0].search_intent if keywords else SearchIntent.COMMERCIAL_INVESTIGATION

        # 3. Audience & Geography
        target_audience = (
            "University students, college freshers, coaching aspirants (NEET/JEE/UPSC), "
            "and outstation parents seeking verified, secure, and budget-friendly accommodation."
        )
        geo_focus = candidate.market

        # 4. SEO Titles, H1, Meta Description, Slug
        # Keep title within ~60 characters where practical
        clean_title_seed = topic.replace("Affordable ", "").replace("Guide ", "")
        suggested_title = f"{primary_kw.title()}: Complete Student Living Guide"
        if len(suggested_title) > 65:
            suggested_title = f"{primary_kw.title()} Guide"

        suggested_h1 = f"{topic}: The Ultimate Student Living & PG Guide"

        suggested_meta_description = (
            f"Looking for student accommodation or PGs in {geo_focus}? Explore verified rooms, "
            f"realistic monthly costs, safety checklist, and local student transit tips."
        )[:158]

        suggested_slug = self.slugify(primary_kw)

        # 5. Outlines (H2 & H3 hierarchy)
        outline = [
            {
                "h2": f"Overview: Student Living in {geo_focus}",
                "h3s": [
                    "Why Location Matters for University Students",
                    "Key Student Zones and Campus Proximity",
                ],
            },
            {
                "h2": "Hostel vs PG vs Flat Sharing: Finding Your Fit",
                "h3s": [
                    "Budget and Rent Breakdown",
                    "Food, Mess, and Tiffin Services",
                    "Wi-Fi, Power Backup & Study Amenities",
                ],
            },
            {
                "h2": "Local Transit & Daily Commute Guide",
                "h3s": [
                    "Metro & Shared Auto Route Connectivity",
                    "Estimated Monthly Commute Expenses",
                ],
            },
            {
                "h2": "Safety, Legal Agreements & Inspection Checklist",
                "h3s": [
                    "Security Features to Check (CCTV, Biometric, Wardens)",
                    "Rental Agreement & Security Deposit Rules",
                    "Local Police Tenant Verification in Uttar Pradesh",
                ],
            },
            {
                "h2": "Frequently Asked Questions (FAQs)",
                "h3s": [],
            },
            {
                "h2": "Next Steps: Securing Your Student Room Without Hassle",
                "h3s": [],
            },
        ]

        # 6. Word-count guidance
        avg_comp_words = (
            sum(c.word_count or 1100 for c in competitors) // len(competitors)
            if competitors
            else 1100
        )
        target_words = max(1200, min(1800, avg_comp_words + 300))
        word_count_guidance = f"{target_words - 150} to {target_words + 200} words (Target: ~{target_words} words)"

        # 7. Grounded 10 FAQs
        faqs = [
            {
                "question": f"What is the average monthly rent for a student PG in {geo_focus}?",
                "guidance": "Provide indicative ranges (e.g. ₹6,000 - ₹14,000/month depending on sharing vs single room) with clear disclaimer.",
            },
            {
                "question": "Are meals and Wi-Fi usually included in student hostels here?",
                "guidance": "Explain that most private student hostels include breakfast, dinner, and Wi-Fi, but check laundry and AC electricity meter policies.",
            },
            {
                "question": "How early before the academic session starts should students book accommodation?",
                "guidance": "Advise booking 4-6 weeks prior to semester start (June-July or December) to secure top spots near colleges.",
            },
            {
                "question": "What documents are required for student tenant verification in Uttar Pradesh?",
                "guidance": "Mention college ID/admission letter, Aadhaar card, passport photos, and parent contact details required by local police norms.",
            },
            {
                "question": "Is public transport readily available near major university zones?",
                "guidance": "Highlight metro lines (Aqua Line/Lucknow Metro) or e-rickshaws/autos connecting campuses and student clusters.",
            },
            {
                "question": "What is the typical security deposit asked by PG owners in UP?",
                "guidance": "Usually 1 to 2 months' rent; emphasize getting written deposit refund terms in the lease agreement.",
            },
            {
                "question": "Can college freshers find single occupancy rooms, or is sharing mandatory?",
                "guidance": "Both are available; double/triple sharing is popular for budget savings, whereas single rooms offer quiet study space.",
            },
            {
                "question": "How do student accommodations manage summer electricity and AC power cuts?",
                "guidance": "Stress the necessity of asking about dedicated DG generators vs inverter backups before booking.",
            },
            {
                "question": "Are female student hostels strictly secure with curfews?",
                "guidance": "Discuss standard 24/7 CCTV, female wardens, biometric entry, and typical 8:30 PM - 9:30 PM entry timings.",
            },
            {
                "question": "How can students avoid fraudulent broker listings in Uttar Pradesh?",
                "guidance": "Advise against paying non-refundable token money before verified in-person/virtual tour and speaking with current student residents.",
            },
        ]

        # 8. Competitor Insights & Gaps
        comp_domains = ", ".join(list(dict.fromkeys(c.domain for c in competitors))) if competitors else "Limited"
        gaps_collected = []
        for c in competitors:
            gaps_collected.extend(c.coverage_gaps)
        gaps_unique = list(dict.fromkeys(gaps_collected))[:4]
        if not gaps_unique:
            gaps_unique = [
                "Detailed electricity and meal surcharge transparency",
                "Metro station distance and shared auto commute tips",
                "Tenant verification and lease checklist for UP colleges",
            ]

        # 9. Internal Links: MUST ONLY refer to verified URLs from brand_config
        matched_internal = brand_config.get_matching_internal_links(topic, max_links=3)
        recommended_internal = [
            {
                "url": link.url,
                "anchor_text": link.anchor_text,
                "context": f"Link when discussing {link.target_topic}",
            }
            for link in matched_internal
        ]

        # 10. Suggested External Sources
        external_sources = SourceRegistry.get_sources_for_topic(topic, max_sources=3)

        # 11. Required Factual Claims & Editorial Cautions
        required_claims = [
            "All pricing and cost figures must be stated as indicative ranges, not guaranteed fixed rates.",
            "Include mention of UP Police tenant verification guidelines for student safety.",
            "Reference specific verified local transit or campus proximity details.",
        ]

        editorial_cautions = [
            "DO NOT invent specific room rates or claim 100% room availability.",
            "DO NOT claim personal physical inspection of rooms.",
            "Preserve a welcoming, student-first tone without overly corporate sales jargon.",
            "Verify that internal links use only the approved company domain URLs.",
        ]

        brief = SEOBrief(
            run_id=candidate.run_id,
            topic=topic,
            primary_keyword=primary_kw,
            secondary_keywords=secondary_kws,
            search_intent=intent,
            target_audience=target_audience,
            geographic_focus=geo_focus,
            suggested_title=suggested_title,
            suggested_h1=suggested_h1,
            suggested_meta_description=suggested_meta_description,
            suggested_slug=suggested_slug,
            outline=outline,
            word_count_guidance=word_count_guidance,
            target_faqs=faqs,
            competitor_insights=f"Analyzed competitors from: {comp_domains}. Competitors focus on generic listings with thin editorial guidance.",
            content_gaps=gaps_unique,
            recommended_internal_links=recommended_internal,
            suggested_external_sources=external_sources,
            required_factual_claims=required_claims,
            editorial_cautions=editorial_cautions,
        )

        logger.info(f"Generated complete SEO brief for topic '{topic}'")
        return brief
