"""Link validation: enforces verified internal URLs and valid external sources."""

import re
import urllib.parse
from typing import List, Tuple
from storage.models import BlogDraft, SEOBrief, QACheckResult
from config.brand_config import brand_config


class LinkChecker:
    """Verifies that internal links belong exclusively to approved domain paths and external links are valid."""

    def __init__(self):
        self.verified_urls = {item.url.rstrip("/") for item in brand_config.verified_internal_urls}
        self.brand_domain = brand_config.website_domain.lower()

    def extract_links(self, markdown: str) -> List[Tuple[str, str]]:
        """Extract all markdown links [anchor](url)."""
        pattern = r"\[([^\]]+)\]\((https?://[^\s\)]+)\)"
        return re.findall(pattern, markdown)

    def validate_links(self, draft: BlogDraft) -> List[QACheckResult]:
        """Perform comprehensive link audit."""
        results = []
        links = self.extract_links(draft.content_markdown)

        if not links:
            results.append(
                QACheckResult(
                    check_name="Link Presence",
                    status="WARNING",
                    severity="MAJOR",
                    explanation="No internal or external links found in the draft.",
                    suggested_correction="Include verified internal links and official transit/civic citations.",
                )
            )
            return results

        internal_links_found = []
        external_links_found = []
        unverified_internal_links = []
        malformed_external_links = []

        for anchor, url in links:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower()

            if self.brand_domain in domain:
                # Internal link
                clean_url = url.rstrip("/")
                internal_links_found.append(clean_url)
                if clean_url not in self.verified_urls:
                    unverified_internal_links.append(clean_url)
            else:
                # External link
                external_links_found.append(url)
                if not parsed.scheme or not parsed.netloc:
                    malformed_external_links.append(url)

        # 1. Internal Link Verification Gate
        if unverified_internal_links:
            results.append(
                QACheckResult(
                    check_name="Internal Link Verification",
                    status="FAIL",
                    severity="CRITICAL",
                    explanation=(
                        f"Draft contains {len(unverified_internal_links)} unverified internal link(s) "
                        f"not found in brand config catalog: {', '.join(unverified_internal_links[:3])}"
                    ),
                    evidence=", ".join(unverified_internal_links),
                    suggested_correction="Only use pre-approved URLs from the verified internal links catalog.",
                )
            )
        elif internal_links_found:
            results.append(
                QACheckResult(
                    check_name="Internal Link Verification",
                    status="PASS",
                    severity="MINOR",
                    explanation=f"Found {len(internal_links_found)} internal link(s), all matching verified catalog URLs.",
                )
            )
        else:
            results.append(
                QACheckResult(
                    check_name="Internal Link Verification",
                    status="WARNING",
                    severity="MAJOR",
                    explanation="No verified internal links to the accommodation website were included.",
                    suggested_correction="Add at least 1 verified internal link to a relevant location or guide page.",
                )
            )

        # 2. External Link Syntax Gate
        if malformed_external_links:
            results.append(
                QACheckResult(
                    check_name="External Source URL Validity",
                    status="FAIL",
                    severity="MAJOR",
                    explanation=f"Malformed external link URL syntax: {', '.join(malformed_external_links)}",
                    evidence=", ".join(malformed_external_links),
                    suggested_correction="Ensure external URLs include valid https:// schemes and domains.",
                )
            )
        elif external_links_found:
            results.append(
                QACheckResult(
                    check_name="External Source URL Validity",
                    status="PASS",
                    severity="MINOR",
                    explanation=f"Found {len(external_links_found)} syntactically valid external authority source citations.",
                )
            )

        return results
