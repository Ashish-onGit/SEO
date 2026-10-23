"""SQLite Database connection and table initialization."""

import sqlite3
from pathlib import Path
from typing import Generator
from contextlib import contextmanager
from config.settings import settings


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;

CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    status TEXT NOT NULL,
    current_stage TEXT NOT NULL,
    selected_topic TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS topic_candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    related_queries TEXT,
    trend_direction TEXT,
    trend_period TEXT,
    source TEXT,
    market TEXT,
    seasonal_relevance TEXT,
    accommodation_relevance REAL,
    provenance TEXT,
    is_selected BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS keyword_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    keyword TEXT NOT NULL,
    search_volume INTEGER,
    measurement_period TEXT,
    trend_direction TEXT,
    difficulty INTEGER,
    search_intent TEXT,
    geographic_relevance TEXT,
    business_relevance REAL,
    source TEXT,
    provenance TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS competitor_articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    title TEXT,
    url TEXT,
    domain TEXT,
    search_query TEXT,
    search_position INTEGER,
    headings TEXT,
    content_summary TEXT,
    freshness TEXT,
    coverage_gaps TEXT,
    traffic_estimate TEXT,
    word_count INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS topic_scores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    accommodation_relevance_score REAL,
    trend_opportunity_score REAL,
    ranking_opportunity_score REAL,
    business_value_score REAL,
    total_score REAL,
    rationale TEXT,
    evidence_breakdown TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS seo_briefs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    primary_keyword TEXT,
    secondary_keywords TEXT,
    search_intent TEXT,
    target_audience TEXT,
    geographic_focus TEXT,
    suggested_title TEXT,
    suggested_h1 TEXT,
    suggested_meta_description TEXT,
    suggested_slug TEXT,
    outline TEXT,
    word_count_guidance TEXT,
    target_faqs TEXT,
    competitor_insights TEXT,
    content_gaps TEXT,
    recommended_internal_links TEXT,
    suggested_external_sources TEXT,
    required_factual_claims TEXT,
    editorial_cautions TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blog_drafts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    title TEXT,
    slug TEXT,
    meta_description TEXT,
    content_markdown TEXT,
    word_count INTEGER,
    version INTEGER DEFAULT 1,
    citations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS qa_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    overall_status TEXT,
    deterministic_passed BOOLEAN,
    ai_review_passed BOOLEAN,
    critical_failures TEXT,
    major_warnings TEXT,
    minor_warnings TEXT,
    all_checks TEXT,
    originality_status TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS email_deliveries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    recipient TEXT NOT NULL,
    subject TEXT NOT NULL,
    status TEXT NOT NULL,
    delivery_method TEXT,
    message_id TEXT,
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(run_id) REFERENCES pipeline_runs(run_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_runs_date ON pipeline_runs(date);
CREATE INDEX IF NOT EXISTS idx_candidates_run ON topic_candidates(run_id);
CREATE INDEX IF NOT EXISTS idx_scores_total ON topic_scores(total_score);
CREATE INDEX IF NOT EXISTS idx_deliveries_run ON email_deliveries(run_id);
"""


class DatabaseManager:
    """Manages SQLite connections and schema initialization."""

    def __init__(self, db_path: Path = None):
        self.db_path = db_path or settings.database_path

    def initialize(self) -> None:
        """Create tables and indexes if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self.get_connection() as conn:
            conn.executescript(SCHEMA_SQL)

    @contextmanager
    def get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """Context manager yielding a SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


db_manager = DatabaseManager()
