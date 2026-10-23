"""Topic discovery provider combining Google Trends, search suggestions, and UP student seeds."""

import logging
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Optional
import requests

from config.settings import settings
from config.brand_config import brand_config
from storage.models import TopicCandidate, MetricProvenance
from research.base import TopicDiscoveryProvider

logger = logging.getLogger(__name__)

# Core seed patterns for Uttar Pradesh student accommodation
UP_CORE_TOPIC_TEMPLATES = [
    {
        "template": "Affordable Student Hostels and PGs in Greater Noida Knowledge Park",
        "city": "Greater Noida",
        "category": "Core Accommodation",
        "base_relevance": 95.0,
        "queries": [
            "pg in knowledge park 2 greater noida",
            "hostels near galgotias and sharda university",
            "greater noida student accommodation with food",
            "boys pg in knowledge park 3",
            "girls hostel in greater noida near pari chowk",
        ],
        "seasonal": "high (college admissions & semester intake)",
    },
    {
        "template": "Student Accommodation Guide for Amity University Noida (Sector 125)",
        "city": "Noida",
        "category": "Core Accommodation",
        "base_relevance": 92.0,
        "queries": [
            "pg near amity university noida sector 125",
            "hostels near amity noida with single room",
            "student flat sharing in noida expressway",
            "best girls pg near amity gate 2",
            "noida sector 126 student housing cost",
        ],
        "seasonal": "high (summer to autumn session)",
    },
    {
        "template": "Budget Student Housing and PGs in Lucknow Near AKTU and BBD University",
        "city": "Lucknow",
        "category": "Core Accommodation",
        "base_relevance": 90.0,
        "queries": [
            "student pg in lucknow faizabad road",
            "hostels near aktu campus lucknow",
            "bbd university girls hostel off campus",
            "affordable student rooms in indira nagar lucknow",
            "lucknow university student living cost",
        ],
        "seasonal": "year-round (high in July-September)",
    },
    {
        "template": "Complete Student Hostel & PG Guide in Kakadeo Kanpur for Coaching Aspirants",
        "city": "Kanpur",
        "category": "Coaching & Accommodation",
        "base_relevance": 94.0,
        "queries": [
            "kakadeo kanpur hostels for neet students",
            "pg in kakadeo kanpur with mess",
            "iit kanpur kalyanpur student accommodation",
            "coaching student living expenses in kanpur",
            "safe girls pg in kakadeo kanpur",
        ],
        "seasonal": "high (coaching session commencements)",
    },
    {
        "template": "Student Hostels and Rooms Near BHU Varanasi: Area Guide & Living Costs",
        "city": "Varanasi",
        "category": "Core Accommodation",
        "base_relevance": 88.0,
        "queries": [
            "pg near bhu lanka varanasi",
            "student rooms near assi ghat varanasi",
            "hostel near iit bhu varanasi",
            "monthly living cost for students in varanasi",
            "varanasi student accommodation with wifi",
        ],
        "seasonal": "high (university entrance cycles)",
    },
    {
        "template": "Affordable Student Living in Prayagraj: PGs and Hostels in Katra & Civil Lines",
        "city": "Prayagraj",
        "category": "Coaching & Student Housing",
        "base_relevance": 89.0,
        "queries": [
            "pg in katra prayagraj for students",
            "hostels in civil lines prayagraj",
            "allahabad university student room rent",
            "upsc aspirant room sharing in prayagraj",
            "cheap student mess and lodging in prayagraj",
        ],
        "seasonal": "year-round",
    },
    {
        "template": "Cost of Student Living in Uttar Pradesh: Noida vs Lucknow Breakdown",
        "city": "Uttar Pradesh",
        "category": "Student Budgeting & Guides",
        "base_relevance": 82.0,
        "queries": [
            "student monthly budget in up colleges",
            "hostel rent vs flat sharing in noida and lucknow",
            "hidden accommodation costs in student pgs",
            "student food and transport expenses in uttar pradesh",
            "up student scholarship and housing allowance",
        ],
        "seasonal": "year-round",
    },
    {
        "template": "First-Time Student Hostel Checklist: Security, Food & Lease Guide for UP Universities",
        "city": "Uttar Pradesh",
        "category": "Moving & Safety",
        "base_relevance": 85.0,
        "queries": [
            "hostel agreement checklist for students in india",
            "security questions to ask pg owners in up",
            "what to pack for college hostel in uttar pradesh",
            "student rights when renting pg in noida",
            "how to verify pg safety for female students",
        ],
        "seasonal": "peak (freshman move-in months)",
    },
]


class GoogleTrendsDiscoveryProvider(TopicDiscoveryProvider):
    """Discovers topics using Google Trends RSS feeds and localized UP student seeds."""

    def __init__(self, geo: str = "IN"):
        self.geo = geo
        self.rss_url = f"https://trends.google.com/trending/rss?geo={geo}"

    def fetch_live_trending_queries(self) -> List[str]:
        """Fetch current trending search queries in India via Google Trends RSS."""
        queries = []
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            resp = requests.get(self.rss_url, headers=headers, timeout=6.0)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item"):
                    title = item.find("title")
                    if title is not None and title.text:
                        queries.append(title.text.strip())
        except Exception as e:
            logger.warning(f"Could not fetch live Google Trends RSS: {e}. Falling back to search suggestions.")
        return queries

    def fetch_google_suggestions(self, prefix: str) -> List[str]:
        """Fetch real-time auto-complete search suggestions from Google."""
        suggestions = []
        try:
            url = f"https://suggestqueries.google.com/complete/search?client=chrome&hl=en&gl=in&q={urllib.parse.quote(prefix)}"
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            resp = requests.get(url, headers=headers, timeout=4.0)
            if resp.status_code == 200:
                data = resp.json()
                if len(data) > 1 and isinstance(data[1], list):
                    suggestions = [s for s in data[1] if isinstance(s, str)]
        except Exception as e:
            logger.debug(f"Google Suggest query failed for '{prefix}': {e}")
        return suggestions

    def discover_topics(self, run_id: str, count: int = 8) -> List[TopicCandidate]:
        """Generate candidate topics enriched with related queries and trend signals."""
        candidates: List[TopicCandidate] = []
        live_trends = self.fetch_live_trending_queries()

        for idx, template_info in enumerate(UP_CORE_TOPIC_TEMPLATES[:count]):
            topic_title = template_info["template"]
            city = template_info["city"]
            base_rel = template_info["base_relevance"]
            initial_queries = list(template_info["queries"])

            # Query real-time Google Suggest to expand queries
            suggest_seed = f"pg in {city} for students" if city != "Uttar Pradesh" else "student accommodation uttar pradesh"
            live_suggestions = self.fetch_google_suggestions(suggest_seed)
            combined_queries = list(dict.fromkeys(initial_queries + live_suggestions[:4]))

            # Trend direction detection
            trend_direction = "stable"
            trend_period = "past_30_days"
            provenance = MetricProvenance.ESTIMATED

            # Check if any live trending query relates to education, exams, or UP
            for trend in live_trends:
                if any(k in trend.lower() for k in ["exam", "result", "neet", "jee", "counseling", "university", city.lower()]):
                    trend_direction = "rising"
                    trend_period = "recent_surge"
                    provenance = MetricProvenance.MEASURED
                    break

            candidate = TopicCandidate(
                run_id=run_id,
                topic=topic_title,
                related_queries=combined_queries,
                trend_direction=trend_direction,
                trend_period=trend_period,
                source="google_suggest_and_up_education_index",
                market=f"India ({city if city != 'Uttar Pradesh' else 'Uttar Pradesh'})",
                seasonal_relevance=template_info["seasonal"],
                accommodation_relevance=base_rel,
                provenance=provenance,
                is_selected=False,
            )
            candidates.append(candidate)

        logger.info(f"Discovered {len(candidates)} candidate topics for run {run_id}")
        return candidates
