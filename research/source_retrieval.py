"""Factual sources repository and verification for student living in Uttar Pradesh."""

from typing import List, Dict, Any


class SourceRegistry:
    """Registry of verified civic, educational, and transportation sources for UP."""

    UP_OFFICIAL_SOURCES = [
        {
            "name": "Noida Metro Rail Corporation (NMRC)",
            "url": "https://www.nmrcnoida.com",
            "topic": "Aqua Line metro connectivity for Knowledge Park and Sector 142/51 students",
            "category": "Transit",
        },
        {
            "name": "Uttar Pradesh Metro Rail Corporation (UPMRC - Lucknow Metro)",
            "url": "https://www.lmrcl.com",
            "topic": "Lucknow Metro routes connecting Hazratganj, Charbagh, and CCS Airport",
            "category": "Transit",
        },
        {
            "name": "Uttar Pradesh Police Citizen Services",
            "url": "https://uppolice.gov.in",
            "topic": "Mandatory tenant and student PG verification guidelines in UP",
            "category": "Safety & Civic",
        },
        {
            "name": "Dr. A.P.J. Abdul Kalam Technical University (AKTU)",
            "url": "https://aktu.ac.in",
            "topic": "Affiliated technical and engineering colleges housing guidelines",
            "category": "Education",
        },
        {
            "name": "University of Lucknow",
            "url": "https://www.lkouniv.ac.in",
            "topic": "Academic calendar and student hostel policies",
            "category": "Education",
        },
        {
            "name": "Banaras Hindu University (BHU)",
            "url": "https://www.bhu.ac.in",
            "topic": "BHU campus accommodation rules and university intake",
            "category": "Education",
        },
        {
            "name": "IIT Kanpur Official Portal",
            "url": "https://www.iitk.ac.in",
            "topic": "Campus housing and research scholar visitor guidelines",
            "category": "Education",
        },
    ]

    @classmethod
    def get_sources_for_topic(cls, topic: str, max_sources: int = 3) -> List[Dict[str, str]]:
        """Return credible official external reference sources matching the topic."""
        topic_lower = topic.lower()
        matched = []
        for src in cls.UP_OFFICIAL_SOURCES:
            src_topic_lower = src["topic"].lower()
            if any(word in topic_lower for word in ["noida", "greater noida", "knowledge park"]) and "nmrc" in src["name"].lower():
                matched.append(src)
            elif "lucknow" in topic_lower and "lucknow" in src_topic_lower:
                matched.append(src)
            elif "kanpur" in topic_lower and "kanpur" in src_topic_lower:
                matched.append(src)
            elif "varanasi" in topic_lower and "bhu" in src_topic_lower:
                matched.append(src)
            elif any(w in topic_lower for w in ["checklist", "security", "safe", "verification"]) and "police" in src["name"].lower():
                matched.append(src)

        # Fallback to general UP safety/transit if specific match is low
        if len(matched) < max_sources:
            for src in cls.UP_OFFICIAL_SOURCES:
                if src not in matched:
                    matched.append(src)
                if len(matched) >= max_sources:
                    break

        return matched[:max_sources]
