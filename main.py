"""Command Line Interface (CLI) entry point for the Automated SEO Research & Drafting System."""

import sys
import logging
import argparse
from datetime import datetime
from config.settings import settings
from orchestration.pipeline import SEOPipeline
from ai.mock_provider import MockAIProvider
from storage.database import db_manager
from storage.repositories import repository


def setup_logging(verbose: bool = False) -> None:
    """Configure structured console and file logging."""
    settings.ensure_directories()
    today_str = datetime.now().strftime("%Y-%m-%d")
    log_file = settings.logs_dir / f"seo_pipeline_{today_str}.log"

    level = logging.DEBUG if verbose else getattr(logging, settings.log_level.upper(), logging.INFO)

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(str(log_file), encoding="utf-8"),
    ]

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
    )


def print_banner():
    """Print startup banner."""
    print("=" * 80)
    print("  CAMPUSNEST UP • Automated SEO Research & Blog Drafting System")
    print(f"  Target Market: {settings.target_country} ({settings.target_state})")
    print(f"  Priority Hubs: {', '.join(settings.target_cities[:5])}...")
    print(f"  AI Provider: {settings.ai_provider} | Database: {settings.database_path.name}")
    print("=" * 80)


def show_status():
    """Display recent pipeline runs and system status."""
    db_manager.initialize()
    print("\n--- Recent Pipeline Execution Runs ---")
    with db_manager.get_connection() as conn:
        rows = conn.execute(
            """
            SELECT run_id, date, status, current_stage, selected_topic, created_at
            FROM pipeline_runs
            ORDER BY created_at DESC
            LIMIT 5
            """
        ).fetchall()

        if not rows:
            print("No execution history found in database.")
            return

        for r in rows:
            print(f"- Run: {r['run_id']} | Date: {r['date']} | Status: {r['status']}")
            print(f"  Stage: {r['current_stage']} | Topic: {r['selected_topic'] or 'None'}")
            print()


def main():
    """Parse CLI arguments and dispatch pipeline."""
    parser = argparse.ArgumentParser(
        description="Automated SEO Research & Blog Drafting System for Uttar Pradesh Student Accommodation"
    )
    parser.add_argument(
        "--manual",
        action="store_true",
        help="Execute manual run immediately with console progress",
    )
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Run in automated scheduled mode (designed for Windows Task Scheduler)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute using Mock AI provider and HTML export without calling external APIs",
    )
    parser.add_argument(
        "--resume",
        metavar="RUN_ID",
        type=str,
        help="Resume an interrupted or failed execution by its Run ID",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show recent execution history and status",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )

    args = parser.parse_args()
    setup_logging(verbose=args.verbose)

    if args.status:
        show_status()
        return

    print_banner()

    ai_provider = None
    if args.dry_run:
        logging.info("Running in --dry-run mode (Mock AI + local email HTML export).")
        ai_provider = MockAIProvider()

    pipeline = SEOPipeline(ai_provider=ai_provider)

    try:
        run_record = pipeline.run(resume_run_id=args.resume)
        print("\n" + "=" * 80)
        print(f"  EXECUTION RESULT: {run_record.status.value}")
        print(f"  Run ID: {run_record.run_id}")
        print(f"  Selected Topic: {run_record.selected_topic}")
        print(f"  Final Stage: {run_record.current_stage}")
        if run_record.error_message:
            print(f"  Error Details: {run_record.error_message}")
        print("=" * 80 + "\n")

        # Exit code: 0 if success/warning, 1 if failed
        sys.exit(0 if run_record.status.value in ("EMAIL_SENT", "QA_PASSED") else 1)

    except Exception as e:
        logging.critical(f"Fatal error during CLI execution: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
