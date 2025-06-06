"""Sitemap parser module for the automated website analysis system.

This module fetches and parses a website's sitemap.xml. It extracts URLs,
supports nested sitemap indexes, filters disallowed URLs via robots.txt
and returns a structured list of page URLs.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List, Set

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class SitemapEntry:
    url: str
    lastmod: str | None = None
    changefreq: str | None = None
    priority: float | None = None


@dataclass
class SitemapParser:
    base_url: str
    session: requests.Session = field(default_factory=requests.Session)
    visited: Set[str] = field(default_factory=set)
    max_retries: int = 3
    timeout: int = 10

    def fetch(self, url: str) -> str:
        """Fetch XML content from the given URL with retries."""
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, timeout=self.timeout)
                resp.raise_for_status()
                return resp.text
            except requests.RequestException as exc:
                logger.warning("Error fetching %s: %s (attempt %s/%s)", url, exc, attempt, self.max_retries)
                if attempt == self.max_retries:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Unreachable code")

    def parse(self, url: str | None = None) -> List[SitemapEntry]:
        """Parse the sitemap starting from the provided URL or base_url."""
        target = url or f"{self.base_url.rstrip('/')}/sitemap.xml"
        if target in self.visited:
            return []
        self.visited.add(target)

        xml = self.fetch(target)
        soup = BeautifulSoup(xml, "xml")

        entries: List[SitemapEntry] = []
        if soup.find("sitemapindex"):
            for loc in soup.find_all("loc"):
                child_url = loc.text.strip()
                entries.extend(self.parse(child_url))
            return entries

        for url_tag in soup.find_all("url"):
            loc_tag = url_tag.find("loc")
            if not loc_tag:
                continue
            loc = loc_tag.text.strip()
            if not self._allowed(loc):
                logger.info("Skipping disallowed URL: %s", loc)
                continue
            entry = SitemapEntry(
                url=loc,
                lastmod=url_tag.findtext("lastmod"),
                changefreq=url_tag.findtext("changefreq"),
                priority=(float(url_tag.findtext("priority")) if url_tag.find("priority") else None),
            )
            entries.append(entry)
        return entries

    def _load_robots(self) -> None:
        """Fetch and parse robots.txt if available."""
        if hasattr(self, "_robots_rules"):
            return
        robots_url = f"{self.base_url.rstrip('/')}/robots.txt"
        try:
            resp = self.session.get(robots_url, timeout=self.timeout)
            if resp.status_code == 200:
                self._robots_rules = [line.split(":", 1)[1].strip() for line in resp.text.splitlines() if line.lower().startswith("disallow:")]
            else:
                self._robots_rules = []
        except requests.RequestException:
            self._robots_rules = []

    def _allowed(self, url: str) -> bool:
        """Return True if the URL is not disallowed by robots.txt."""
        self._load_robots()
        path = url.split(self.base_url, 1)[-1]
        for rule in getattr(self, "_robots_rules", []):
            if path.startswith(rule):
                return False
        return True
