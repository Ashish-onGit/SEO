"""System configuration settings loaded from environment variables and defaults."""

import os
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseModel):
    """Application-wide configuration settings with validation."""

    # Project directories
    base_dir: Path = BASE_DIR
    data_dir: Path = BASE_DIR / "data"
    output_dir: Path = BASE_DIR / "output"
    logs_dir: Path = BASE_DIR / "logs"

    # AI Configuration
    gemini_api_key: Optional[str] = Field(default_factory=lambda: os.getenv("GEMINI_API_KEY"))
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-1.5-flash"))
    ai_provider: str = Field(default_factory=lambda: os.getenv("AI_PROVIDER", "gemini").lower())

    # Business & Market Scope (Uttar Pradesh focus)
    target_country: str = Field(default_factory=lambda: os.getenv("TARGET_COUNTRY", "India"))
    target_state: str = Field(default_factory=lambda: os.getenv("TARGET_STATE", "Uttar Pradesh"))
    target_cities: List[str] = Field(
        default_factory=lambda: [
            c.strip()
            for c in os.getenv(
                "TARGET_CITIES",
                "Greater Noida,Noida,Lucknow,Kanpur,Varanasi,Prayagraj,Ghaziabad",
            ).split(",")
            if c.strip()
        ]
    )
    company_name: str = Field(default_factory=lambda: os.getenv("COMPANY_NAME", "CampusNest UP"))
    company_website: str = Field(
        default_factory=lambda: os.getenv("COMPANY_WEBSITE", "https://campusnest-up.example.com")
    )
    brand_voice: str = Field(
        default_factory=lambda: os.getenv(
            "BRAND_VOICE",
            "Empathetic, practical, student-centric, honest, informative, and engaging",
        )
    )

    # Gmail Delivery Configuration
    gmail_sender_email: Optional[str] = Field(default_factory=lambda: os.getenv("GMAIL_SENDER_EMAIL"))
    gmail_recipient_email: Optional[str] = Field(default_factory=lambda: os.getenv("GMAIL_RECIPIENT_EMAIL"))
    gmail_credentials_file: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
    )
    gmail_token_file: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("GMAIL_TOKEN_FILE", "token.json")
    )
    email_dry_run: bool = Field(
        default_factory=lambda: os.getenv("EMAIL_DRY_RUN", "true").lower() in ("1", "true", "yes")
    )

    # Scoring Weights
    weight_accommodation_relevance: float = Field(
        default_factory=lambda: float(os.getenv("WEIGHT_ACCOMMODATION_RELEVANCE", "0.35"))
    )
    weight_trend_opportunity: float = Field(
        default_factory=lambda: float(os.getenv("WEIGHT_TREND_OPPORTUNITY", "0.20"))
    )
    weight_ranking_opportunity: float = Field(
        default_factory=lambda: float(os.getenv("WEIGHT_RANKING_OPPORTUNITY", "0.20"))
    )
    weight_business_value: float = Field(
        default_factory=lambda: float(os.getenv("WEIGHT_BUSINESS_VALUE", "0.25"))
    )

    # Quality and Search Thresholds
    min_topic_score: float = Field(
        default_factory=lambda: float(os.getenv("MIN_TOPIC_SCORE", "55.0"))
    )
    min_business_relevance: float = Field(
        default_factory=lambda: float(os.getenv("MIN_BUSINESS_RELEVANCE", "50.0"))
    )
    max_competitors: int = Field(
        default_factory=lambda: int(os.getenv("MAX_COMPETITORS", "5"))
    )
    min_competitors: int = Field(
        default_factory=lambda: int(os.getenv("MIN_COMPETITORS", "2"))
    )

    # Content Parameters
    draft_language: str = Field(default_factory=lambda: os.getenv("DRAFT_LANGUAGE", "English"))
    min_word_count: int = Field(default_factory=lambda: int(os.getenv("MIN_WORD_COUNT", "1000")))
    max_word_count: int = Field(default_factory=lambda: int(os.getenv("MAX_WORD_COUNT", "2200")))

    # Database and Reliability
    timezone: str = Field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Kolkata"))
    database_path: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("DATABASE_PATH", "data/seo_automation.db")
    )
    max_retries: int = Field(default_factory=lambda: int(os.getenv("MAX_RETRIES", "3")))
    retry_backoff_factor: float = Field(
        default_factory=lambda: float(os.getenv("RETRY_BACKOFF_FACTOR", "2.0"))
    )
    log_level: str = Field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))

    def ensure_directories(self) -> None:
        """Ensure runtime directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "drafts").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "briefs").mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()
settings.ensure_directories()
