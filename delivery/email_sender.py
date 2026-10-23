"""Email delivery interface and templating utilities."""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path
from storage.models import BlogDraft, SEOBrief, QAReport, PipelineRun, TopicScore


class EmailDeliveryProvider(ABC):
    """Abstract interface for dispatching the daily morning SEO report and draft."""

    @abstractmethod
    def send_daily_report(
        self,
        run: PipelineRun,
        topic_score: Optional[TopicScore],
        brief: Optional[SEOBrief],
        draft: Optional[BlogDraft],
        qa_report: Optional[QAReport],
        attachment_path: Optional[Path],
    ) -> bool:
        """Send daily report email."""
        pass

    @abstractmethod
    def send_failure_alert(
        self,
        run: PipelineRun,
        error_stage: str,
        error_message: str,
    ) -> bool:
        """Send immediate pipeline failure alert."""
        pass
