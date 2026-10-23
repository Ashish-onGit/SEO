"""Brand configuration and verified internal URLs catalog."""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from config.settings import BASE_DIR


class InternalUrlEntry(BaseModel):
    """Represents a verified internal link for the brand."""
    url: str
    anchor_text: str
    target_topic: str


class StudentZone(BaseModel):
    """University city zone and institutions."""
    city: str
    zones: List[str]
    institutions: List[str]


class TargetMarket(BaseModel):
    """Geographic focus details."""
    country: str = "India"
    state: str = "Uttar Pradesh"
    priority_cities: List[str] = Field(default_factory=list)
    major_student_zones: List[StudentZone] = Field(default_factory=list)


class BrandConfig(BaseModel):
    """Complete brand and editorial guidelines configuration."""
    brand_name: str = "CampusNest UP"
    tagline: str = "Curated, Safe & Affordable Student Accommodation Across Uttar Pradesh"
    website_domain: str = "campusnest-up.example.com"
    base_url: str = "https://campusnest-up.example.com"
    target_market: TargetMarket = Field(default_factory=TargetMarket)
    brand_pillars: List[str] = Field(default_factory=list)
    brand_voice: str = "Empathetic, practical, student-centric, honest, informative, and engaging"
    forbidden_claims: List[str] = Field(default_factory=list)
    verified_internal_urls: List[InternalUrlEntry] = Field(default_factory=list)

    @classmethod
    def load_from_file(cls, path: Optional[Path] = None) -> "BrandConfig":
        """Load brand configuration from a JSON file."""
        config_path = path or (BASE_DIR / "config" / "brand_config.json")
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                # Return default if parsing fails
                return cls()
        return cls()

    def get_matching_internal_links(self, topic: str, max_links: int = 3) -> List[InternalUrlEntry]:
        """Find the most relevant verified internal URLs for a topic."""
        topic_lower = topic.lower()
        scored_links = []
        for item in self.verified_internal_urls:
            score = 0
            # City match
            for city in self.target_market.priority_cities:
                if city.lower() in topic_lower and city.lower() in item.target_topic.lower():
                    score += 5
            # Word overlap
            topic_words = set(topic_lower.split())
            target_words = set(item.target_topic.lower().split())
            score += len(topic_words.intersection(target_words))
            scored_links.append((score, item))

        scored_links.sort(key=lambda x: x[0], reverse=True)
        # Always return at least some verified links up to max_links
        return [item for _, item in scored_links[:max_links]]


brand_config = BrandConfig.load_from_file()
