"""Fixture-driven Efficient Group public archive discovery."""
from __future__ import annotations
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from .source_base import MarketSource, SourceFetchResult

class _Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self._href=None; self._text=[]
    def handle_starttag(self, tag, attrs):
        if tag == "a": self._href = dict(attrs).get("href"); self._text=[]
    def handle_data(self, data):
        if self._href is not None: self._text.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self._href:
            self.links.append((" ".join(self._text).strip(), self._href)); self._href=None

class EfficientGroupSource(MarketSource):
    source_type = "html_pdf_archive"
    allowed_hosts = {"www.efgroup.co.za", "efgroup.co.za"}
    def discover(self, html: str, base_url: str = "https://www.efgroup.co.za/") -> list[dict]:
        parser = _Links(); parser.feed(html); results=[]
        for title, href in parser.links:
            url=urljoin(base_url, href); host=urlsplit(url).hostname
            if host not in self.allowed_hosts: continue
            is_pdf=url.lower().split("?",1)[0].endswith(".pdf")
            if "economic" in (title+" "+url).lower() or is_pdf:
                results.append({"title": title or "Economic Update", "canonical_url": url, "pdf_url": url if is_pdf else None,
                                "author": self.config.get("author"), "publication_date": self.config.get("publication_date")})
        return results
    def fetch(self, *, since=None):
        return SourceFetchResult(self.source_id, datetime.utcnow().isoformat()+"Z", document_references=[] , metadata={"status":"fixture_or_operator_fetch_required"})
