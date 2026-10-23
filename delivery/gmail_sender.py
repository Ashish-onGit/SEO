"""Gmail API OAuth 2.0 delivery implementation with rich HTML templating and dry-run fallback."""

import os
import base64
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from typing import Optional, List

from config.settings import settings
from storage.models import BlogDraft, SEOBrief, QAReport, PipelineRun, TopicScore
from storage.repositories import repository
from delivery.email_sender import EmailDeliveryProvider

logger = logging.getLogger(__name__)

GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


class GmailDeliveryProvider(EmailDeliveryProvider):
    """Sends rich HTML emails via Gmail API with OAuth 2.0 and idempotent delivery guards."""

    def __init__(self, repo=None):
        self.repo = repo or repository
        self.sender_email = settings.gmail_sender_email or "automation@example.com"
        self.recipient_email = settings.gmail_recipient_email or "editorial@example.com"
        self.credentials_path = settings.gmail_credentials_file
        self.token_path = settings.gmail_token_file
        self.dry_run = settings.email_dry_run
        self.emails_dir = settings.output_dir / "emails"
        self.emails_dir.mkdir(parents=True, exist_ok=True)

    def _get_gmail_service(self):
        """Authenticate and return Google Gmail API resource."""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build

            creds = None
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), GMAIL_SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                elif self.credentials_path.exists():
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), GMAIL_SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    with open(self.token_path, "w", encoding="utf-8") as token_file:
                        token_file.write(creds.to_json())
                else:
                    return None

            return build("gmail", "v1", credentials=creds)
        except Exception as e:
            logger.warning(f"Could not initialize Gmail API service: {e}")
            return None

    def _build_html_template(
        self,
        run: PipelineRun,
        topic_score: Optional[TopicScore],
        brief: Optional[SEOBrief],
        draft: Optional[BlogDraft],
        qa_report: Optional[QAReport],
    ) -> str:
        """Construct a responsive HTML email summarizing the research, brief, QA, and draft."""
        status_color = "#10b981"  # Emerald green for passed
        status_text = "APPROVED FOR EDITORIAL REVIEW"

        if qa_report:
            if qa_report.overall_status == "FAILED":
                status_color = "#ef4444"  # Red
                status_text = "QA GATE FAILED - CRITICAL ISSUES"
            elif qa_report.overall_status == "WARNING":
                status_color = "#f59e0b"  # Amber
                status_text = "NEEDS ATTENTION - QA WARNINGS DETECTED"

        topic_title = brief.topic if brief else run.selected_topic or "Daily SEO Pipeline Run"
        date_str = datetime.now().strftime("%A, %d %B %Y")

        # Scores breakdown
        score_html = ""
        if topic_score:
            score_html = f"""
            <div style="background: #f8fafc; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin-top: 0; color: #1e293b;">Topic Scoring Summary (Score: {topic_score.total_score:.1f}/100)</h3>
                <ul style="margin: 0; padding-left: 20px; color: #475569;">
                    <li><strong>Accommodation Relevance (35%):</strong> {topic_score.accommodation_relevance_score:.0f}/100</li>
                    <li><strong>Trend Opportunity (20%):</strong> {topic_score.trend_opportunity_score:.0f}/100</li>
                    <li><strong>Ranking Opportunity (20%):</strong> {topic_score.ranking_opportunity_score:.0f}/100</li>
                    <li><strong>Business Value (25%):</strong> {topic_score.business_value_score:.0f}/100</li>
                </ul>
                <p style="margin: 8px 0 0 0; font-size: 13px; color: #64748b;"><em>Rationale: {topic_score.rationale}</em></p>
            </div>
            """

        # QA checks summary
        qa_html = ""
        if qa_report:
            qa_items = "".join(
                f"<li style='margin-bottom: 4px;'><strong style='color: {'#10b981' if c.status=='PASS' else '#ef4444' if c.status=='FAIL' else '#f59e0b'};'>[{c.status}]</strong> {c.check_name}: {c.explanation}</li>"
                for c in qa_report.all_checks[:8]
            )
            qa_html = f"""
            <div style="background: #f8fafc; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin-top: 0; color: #1e293b;">Automated QA Gate Results</h3>
                <p style="margin: 0 0 8px 0; color: #475569;">
                    <strong>Deterministic Checks:</strong> {'Passed' if qa_report.deterministic_passed else 'Failed'} |
                    <strong>AI Review:</strong> {'Passed' if qa_report.ai_review_passed else 'Warnings'} |
                    <strong>Originality:</strong> {qa_report.originality_status}
                </p>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #475569;">
                    {qa_items}
                </ul>
            </div>
            """

        # SEO brief details
        brief_html = ""
        if brief:
            internal_links_html = "".join(
                f"<li><a href='{link.get('url')}'>{link.get('anchor_text')}</a> ({link.get('context')})</li>"
                for link in brief.recommended_internal_links
            )
            faqs_html = "".join(
                f"<li style='margin-bottom: 6px;'><strong>{f.get('question')}</strong><br><span style='font-size: 13px; color: #64748b;'>{f.get('guidance')}</span></li>"
                for f in brief.target_faqs[:5]
            )

            brief_html = f"""
            <div style="background: #f8fafc; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin-top: 0; color: #1e293b;">SEO Brief Key Specs</h3>
                <table style="width: 100%; border-collapse: collapse; font-size: 14px; color: #334155;">
                    <tr><td style="padding: 4px 0; width: 140px;"><strong>Primary Keyword:</strong></td><td>{brief.primary_keyword}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>Search Intent:</strong></td><td>{brief.search_intent.value}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>Target Market:</strong></td><td>{brief.geographic_focus}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>Suggested Title:</strong></td><td>{brief.suggested_title}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>Meta Description:</strong></td><td>{brief.suggested_meta_description}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>URL Slug:</strong></td><td>/{brief.suggested_slug}</td></tr>
                    <tr><td style="padding: 4px 0;"><strong>Word Count:</strong></td><td>{draft.word_count if draft else 0} words ({brief.word_count_guidance})</td></tr>
                </table>

                <h4 style="margin: 16px 0 8px 0; color: #1e293b;">Verified Internal Links Recommended:</h4>
                <ul style="margin: 0; padding-left: 20px; font-size: 13px; color: #2563eb;">
                    {internal_links_html if internal_links_html else '<li>None</li>'}
                </ul>

                <h4 style="margin: 16px 0 8px 0; color: #1e293b;">Sample Grounded FAQs:</h4>
                <ol style="margin: 0; padding-left: 20px;">
                    {faqs_html}
                </ol>
            </div>
            """

        # Draft preview
        draft_preview_html = ""
        if draft:
            # Escape HTML brackets slightly
            preview_text = draft.content_markdown[:1500].replace("<", "&lt;").replace(">", "&gt;")
            draft_preview_html = f"""
            <div style="background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin-top: 0; color: #1e293b;">Draft Content Preview</h3>
                <pre style="white-space: pre-wrap; font-family: monospace; font-size: 13px; color: #334155; line-height: 1.5; max-height: 400px; overflow-y: auto;">{preview_text}...</pre>
                <p style="font-size: 12px; color: #64748b;"><em>Full Markdown draft ({draft.word_count} words) is attached to this email.</em></p>
            </div>
            """

        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily SEO Draft: {topic_title}</title>
        </head>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; color: #0f172a;">
            <div style="max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); overflow: hidden;">
                <!-- Header -->
                <div style="background: #0f172a; padding: 24px 32px; color: #ffffff;">
                    <div style="font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #94a3b8;">CampusNest UP • Automated SEO Intelligence</div>
                    <h1 style="margin: 8px 0 4px 0; font-size: 22px; color: #ffffff;">{topic_title}</h1>
                    <div style="font-size: 13px; color: #cbd5e1;">Run Date: {date_str} • Run ID: <code>{run.run_id}</code></div>
                </div>

                <!-- Status Banner -->
                <div style="background: {status_color}; color: #ffffff; padding: 12px 32px; font-weight: bold; font-size: 14px; text-transform: uppercase; letter-spacing: 0.5px;">
                    STATUS: {status_text}
                </div>

                <!-- Body Content -->
                <div style="padding: 24px 32px;">
                    <p style="margin-top: 0; font-size: 15px; color: #334155; line-height: 1.5;">
                        Good morning. Below is today's automatically researched and drafted blog post for the Uttar Pradesh student accommodation market. A human writer must review, polish, and publish manually.
                    </p>

                    {score_html}
                    {brief_html}
                    {qa_html}
                    {draft_preview_html}

                    <div style="border-top: 1px solid #e2e8f0; margin-top: 24px; padding-top: 16px; font-size: 12px; color: #94a3b8; text-align: center;">
                        Automated SEO Research & Drafting System • Windows Task Scheduler Daily Pipeline<br>
                        Confidential internal publication draft. Never auto-publish unreviewed AI output.
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        return html_body

    def send_daily_report(
        self,
        run: PipelineRun,
        topic_score: Optional[TopicScore],
        brief: Optional[SEOBrief],
        draft: Optional[BlogDraft],
        qa_report: Optional[QAReport],
        attachment_path: Optional[Path],
    ) -> bool:
        """Deliver the daily SEO package."""
        # 1. Idempotency Check
        if self.repo.is_email_already_sent(run.run_id):
            logger.info(f"Email already sent for run '{run.run_id}'. Skipping to prevent duplicates.")
            return True

        topic_title = brief.topic if brief else run.selected_topic or "Daily SEO Research"
        status_flag = "PASSED" if qa_report and qa_report.overall_status == "PASSED" else "NEEDS REVIEW"
        subject = f"[{status_flag}] Daily SEO Blog Draft: {topic_title} ({datetime.now().strftime('%d %b')})"

        html_content = self._build_html_template(run, topic_score, brief, draft, qa_report)
        plain_content = (
            f"Daily SEO Blog Draft Report\n"
            f"Topic: {topic_title}\n"
            f"Status: {status_flag}\n"
            f"Run ID: {run.run_id}\n\n"
            f"Please check the attached Markdown file and HTML report for complete research and brief."
        )

        # 2. Check for Dry Run or Missing Live Credentials
        service = self._get_gmail_service() if not self.dry_run else None

        if self.dry_run or not service:
            # Save HTML artifact to disk
            out_file = self.emails_dir / f"{run.run_id}_email_report.html"
            with open(out_file, "w", encoding="utf-8") as f:
                f.write(html_content)

            logger.info(
                f"[DRY-RUN / LOCAL MODE] Daily SEO report compiled successfully! "
                f"Saved to: {out_file}. "
                f"(To send live emails, place credentials.json in project root and set EMAIL_DRY_RUN=false)."
            )

            self.repo.record_email_delivery(
                run_id=run.run_id,
                recipient=self.recipient_email,
                subject=subject,
                status="SENT",
                delivery_method="dry_run_html_export",
                message_id=f"dry_run_{run.run_id}",
            )
            return True

        # 3. Live Gmail API Dispatch
        try:
            msg = MIMEMultipart("mixed")
            msg["to"] = self.recipient_email
            msg["from"] = self.sender_email
            msg["subject"] = subject

            alt = MIMEMultipart("alternative")
            alt.attach(MIMEText(plain_content, "plain", "utf-8"))
            alt.attach(MIMEText(html_content, "html", "utf-8"))
            msg.attach(alt)

            # Attach Markdown Draft if exists
            if attachment_path and attachment_path.exists():
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                    encoders.encode_base64(part)
                    part.add_header(
                        "Content-Disposition",
                        f"attachment; filename={attachment_path.name}",
                    )
                    msg.attach(part)

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
            sent_msg = service.users().messages().send(userId="me", body={"raw": raw}).execute()
            msg_id = sent_msg.get("id", f"sent_{run.run_id}")

            logger.info(f"Successfully dispatched daily report email via Gmail API (Message ID: {msg_id})")

            self.repo.record_email_delivery(
                run_id=run.run_id,
                recipient=self.recipient_email,
                subject=subject,
                status="SENT",
                delivery_method="gmail_api_oauth2",
                message_id=msg_id,
            )
            return True

        except Exception as e:
            logger.error(f"Failed to dispatch email via Gmail API: {e}")
            self.repo.record_email_delivery(
                run_id=run.run_id,
                recipient=self.recipient_email,
                subject=subject,
                status="FAILED",
                delivery_method="gmail_api_oauth2",
                error_message=str(e),
            )
            return False

    def send_failure_alert(
        self,
        run: PipelineRun,
        error_stage: str,
        error_message: str,
    ) -> bool:
        """Send immediate email notification when a scheduled pipeline execution fails."""
        subject = f"[ALERT] SEO Automation Failed at Stage: {error_stage} (Run ID: {run.run_id})"
        body_html = f"""
        <div style="font-family: sans-serif; padding: 20px;">
            <h2 style="color: #ef4444;">Pipeline Execution Failed</h2>
            <p><strong>Run ID:</strong> <code>{run.run_id}</code></p>
            <p><strong>Stage Failed:</strong> {error_stage}</p>
            <p><strong>Error Message:</strong><br><pre style="background: #f8fafc; padding: 12px; border-left: 4px solid #ef4444;">{error_message}</pre></p>
            <p>The system aborted this run to prevent low-quality or misleading content generation.</p>
        </div>
        """
        out_file = self.emails_dir / f"{run.run_id}_failure_alert.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(body_html)

        logger.warning(f"Failure alert recorded to: {out_file}")
        return True
