"""Bounded historical SENS adapters extending the existing recent SENS collector.

No scheduler, credentials, sentiment inference or broker side effects. Public
HTML and owner-permitted browser/import snapshots share exactly the same parsers.
"""
from dataclasses import dataclass, replace
from datetime import date, datetime, timedelta, timezone
from hashlib import sha256
import json
import re
from urllib.parse import parse_qs, urlencode, urljoin, urlsplit

from bs4 import BeautifulSoup
from data_pipeline import NewsItem, SentimentLabel
from evidence import normalize_news_item
from jse_adapter import SENSFeedFetcher
from source_catalog import DEFAULT_SPECIALIST_SOURCES
from domain.evaluation.experiment import utc

VERSION = 'historical-sens-v1'
SAST = timezone(timedelta(hours=2))
SOURCES = {'sharedata_sens': 'www.sharedata.co.za', 'moneyweb_sens': 'www.moneyweb.co.za',
           'sharenet_sens': 'www.sharenet.co.za'}


@dataclass(frozen=True)
class Issuer:
    instrument: str
    name: str
    code: str
    isin: str

    def __post_init__(self):
        if not all((self.instrument, self.name, self.code, self.isin)):
            raise ValueError('explicit issuer/cash-security identity required')
        if not re.fullmatch(r'[A-Z0-9]+', self.code):
            raise ValueError('exact exchange code required')


def _clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _heading_matches(title, issuer):
    company = re.split(r'\s+[–—-]\s+', _clean(title), maxsplit=1)[0]
    return company.casefold() == issuer.name.casefold()


def source_url(source, url):
    parsed = urlsplit(url)
    if source not in SOURCES or parsed.scheme != 'https' or parsed.hostname != SOURCES[source]:
        raise ValueError('known HTTPS source host required')
    if parsed.username or parsed.password or parsed.port not in (None, 443) or parsed.fragment:
        raise ValueError('plain public source URL required')
    allowed = {'sharedata_sens': {'date', 'enddate', 'keyword', 'sharecode', 'sectorcode', 'id'},
               'moneyweb_sens': {'search', 'shareCode', 'startDate', 'endDate'},
               'sharenet_sens': {'seq', 'tdate', 'scode'}}
    if set(parse_qs(parsed.query, keep_blank_values=True)) - allowed[source]:
        raise ValueError('only known public search/document parameters allowed')
    return url


def _clock(value, formats):
    for pattern in formats:
        try:
            return datetime.strptime(_clean(value), pattern).replace(tzinfo=SAST).astimezone(timezone.utc)
        except ValueError:
            pass
    return None


def parse_search(source, raw, url, issuer):
    """Return exact-issuer leads, never treating keyword matches as securities."""
    source_url(source, url)
    if source == 'sharedata_sens':
        payload = json.loads(raw)
        if not isinstance(payload, list) or len(payload) < 3 or not isinstance(payload[0], str):
            raise ValueError('unexpected ShareData search response')
        tree = BeautifulSoup(payload[0], 'html.parser')
        leads = []
        for td in tree.select('td[onclick]')[:100]:
            match = re.fullmatch(r'ViewSENSWithHighlight\((\d+)\);return false;', td.get('onclick', ''))
            title = _clean(td.get_text(' ', strip=True))
            if not match or not _heading_matches(title, issuer):
                continue
            following = td.parent.find_next_sibling('tr')
            clock = following.get_text(' ', strip=True) if following else ''
            leads.append(dict(title=title, url='https://www.sharedata.co.za/v2/Scripts/SENS.aspx?id='+match[1],
                              source_item_id=match[1], release_display=clock,
                              published_at=_clock(clock, ('%d %b %Y, %H:%M',))))
        return leads
    tree = BeautifulSoup(raw, 'html.parser')
    leads = []
    if source == 'moneyweb_sens':
        for row in tree.select('.sens-row')[:100]:
            link = row.select_one('a[href*="/mny_sens/"]')
            if link is None or not _heading_matches(link.get_text(' ', strip=True), issuer):
                continue
            clock = row.select_one('time')
            display = clock.get_text(' ', strip=True) if clock else ''
            target = source_url(source, urljoin(url, link['href']))
            leads.append(dict(title=_clean(link.get_text(' ', strip=True)), url=target,
                              source_item_id=urlsplit(target).path, release_display=display,
                              raw_machine_timestamp=clock.get('datetime') if clock else None,
                              published_at=_clock(display, ('%d.%m.%y, %H:%M',))))
    elif source == 'sharenet_sens':
        # Public linked pages only. No date enumeration or subscriber PDF URL guessing.
        for link in tree.select('a[href*="sens_display.php"]')[:100]:
            if not _heading_matches(link.get_text(' ', strip=True), issuer):
                continue
            target = urljoin(url, link['href'])
            # Old archive links use HTTP; request the same known host over HTTPS.
            parsed = urlsplit(target)
            if parsed.scheme == 'http' and parsed.hostname == SOURCES[source]:
                target = parsed._replace(scheme='https').geturl()
            target = source_url(source, target)
            tdate = parse_qs(urlsplit(target).query).get('tdate', [''])[0]
            leads.append(dict(title=_clean(link.get_text(' ', strip=True)), url=target,
                              source_item_id=urlsplit(target).query, release_display=tdate,
                              published_at=_clock(tdate, ('%Y%m%d%H%M%S',))))
    return leads


def parse_announcement(source, raw, url, issuer, retrieved_at, *, lead=None, snapshot_url=None):
    """Full-body identity qualification, with separate source/receipt clocks.

    Release displays are interpreted under an explicit SAST research assumption.
    Ambiguous footer dates and WordPress machine clocks are retained as diagnostics,
    never used to make historical evidence available before actual receipt.
    """
    source_url(source, url)
    snapshot_url = source_url(source, snapshot_url or url)
    observed = utc(retrieved_at, 'retrieved_at')
    tree = BeautifulSoup(raw, 'html.parser')
    lead = lead or {}
    body = tree.find('pre')
    if snapshot_url != url:
        body = None  # A search-page snapshot cannot establish a detail-page body.
    if body and any(x.has_attr('hidden') or 'display:none' in x.get('style', '').replace(' ', '').lower()
                    for x in [body, *body.parents] if getattr(x, 'attrs', None) is not None):
        body = None
    if source == 'moneyweb_sens' and 'This Sens announcement is available to subscribers' in tree.get_text(' ', strip=True):
        body = None
    text = body.get_text() if body else ''
    heading = tree.select_one('#sens-title') if source == 'moneyweb_sens' else None
    title = _clean(heading.get_text(' ', strip=True)) if heading else lead.get('title', '')
    display = lead.get('release_display', '')
    published = lead.get('published_at')
    if source == 'sharedata_sens':
        # The first display date belongs to the announcement header, not its footer.
        outside = tree.get_text(' ', strip=True)
        match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun) (\d{1,2} [A-Z][a-z]{2} \d{4}, \d{1,2}:\d{2})', outside)
        if match:
            display = match[1]; published = _clock(display, ('%d %b %Y, %H:%M',))
        if body:
            actual_heading = body.find_previous('td')
            if actual_heading:
                title = _clean(actual_heading.get_text(' ', strip=True))
    elif source == 'sharenet_sens':
        match = re.search(r'Release Date:\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2})', tree.get_text(' ', strip=True))
        if match:
            display = match[1]; published = _clock(display, ('%d/%m/%Y %H:%M',))
        if body and (not title or _heading_matches(title, issuer)):
            page_title = tree.find('title')
            found = re.search(r'^.*? - (.+?) - \d{2}/\d{2}/\d{4}$', page_title.get_text() if page_title else '')
            if found:
                title = _clean(found[1])
            elif title:
                # A public archive lead establishes company identity, while its
                # abbreviated title is expanded from the observed document heading.
                title = re.split(r'\s+[–—-]\s+', title, maxsplit=1)[0]+' - '+next(
                    (line.strip() for line in text.splitlines() if line.strip()), '')
    elif source == 'moneyweb_sens' and heading:
        clock = heading.find_next('h4')
        if clock:
            display = clock.get_text(' ', strip=True)
            published = _clock(display, ('%d %B %Y, %H:%M',))
    title = _clean(title)
    if not title or not _heading_matches(title, issuer):
        raise ValueError('issuer headline identity not established')
    # Presence of a word such as "Sasol" in a warrant/debt notice is not enough.
    identity = bool(text and issuer.isin in text and re.search(r'JSE\s*:\s*'+re.escape(issuer.code)+r'\b', text))
    content = re.split(r'\n\s*Date:\s*\d{2}/\d{2}/\d{4}', text, maxsplit=1)[0]
    content_hash = sha256(_clean(content).encode()).hexdigest() if text else None
    raw_hash = sha256(raw.encode() if isinstance(raw, str) else raw).hexdigest()
    footer = re.search(r'Date:\s*(\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2})', text)
    policy = DEFAULT_SPECIALIST_SOURCES.get(source)
    item = NewsItem(issuer.code, title, policy.source_name, published or observed,
                    SentimentLabel.NEUTRAL, 0.0, text=title)
    record = normalize_news_item(item, source_id=source, source_class=policy.source_class,
             authority_tier=policy.authority_tier, url=url, tickers=[issuer.code], assets=[issuer.instrument],
             observed_at=observed, ingested_at=observed, parser_version=VERSION,
             metadata={'issuer_isin': issuer.isin, 'raw_sha256': raw_hash, 'content_sha256': content_hash,
                       'snapshot_url': snapshot_url,
                       'source_item_id': lead.get('source_item_id', urlsplit(url).query or urlsplit(url).path),
                       'release_display': _clean(display), 'release_timezone_basis': 'ASSUMED_SAST_DISPLAY_NOT_PIT_PROOF',
                       'raw_machine_timestamp': lead.get('raw_machine_timestamp'),
                       'raw_footer_timestamp': footer[1] if footer else None,
                       'identity_state': 'CASH_CODE_AND_ISIN_IN_BODY' if identity else 'HEADLINE_ONLY_UNVERIFIED',
                       'body_state': 'FULL_TEXT_PARSED' if text else 'BODY_UNAVAILABLE_OR_SUBSCRIBER_GATED',
                       'available_at': observed.isoformat(), 'data_grade': 'RECONSTRUCTED_ARCHIVE',
                       'origin_family': 'JSE_SENS_ISSUER_DISCLOSURE', 'independent_publisher_count': 1,
                       'automatic_corporate_action': False, 'automatic_sentiment': False})
    if published is None:
        record = replace(record, published_at=None)
    # Revised content at one provider URL must never overwrite its older version.
    return replace(record, evidence_id=sha256((record.evidence_id+(content_hash or raw_hash)).encode()).hexdigest()[:24])


class HistoricalSENSFetcher(SENSFeedFetcher):
    """Existing session/response bounds, explicit total request cap, no auto polling."""
    def __init__(self, *, max_requests=12, session=None):
        if isinstance(max_requests, bool) or not isinstance(max_requests, int) or not 1 <= max_requests <= 16:
            raise ValueError('bounded request cap required')
        super().__init__()
        if session is not None:
            self.session = session
        self.max_requests = max_requests
        self.requests = 0
        self.receipts = []
        self.blocked_sources = set()

    def read(self, source, url):
        source_url(source, url)
        if source in self.blocked_sources:
            self.last_status = 'SOURCE_ACCESS_BLOCKED'; return None
        if self.requests >= self.max_requests:
            self.last_status = 'REQUEST_BUDGET_EXHAUSTED'; return None
        self.requests += 1
        receipt = {'source_id': source, 'url': url, 'retrieved_at': datetime.now(timezone.utc).isoformat()}
        try:
            # Do not follow redirects to logins/third parties or retry blocked requests.
            with self.session.get(url, timeout=15, stream=True, allow_redirects=False) as response:
                receipt['http_status'] = response.status_code
                if response.status_code != 200:
                    self.last_status = 'ACCESS_BLOCKED' if response.status_code in (401, 403, 429) else 'HTTP_UNAVAILABLE'
                    if response.status_code in (401, 403, 429): self.blocked_sources.add(source)
                    receipt['state'] = self.last_status; self.receipts.append(receipt); return None
                body = bytearray()
                for chunk in response.iter_content(chunk_size=16384):
                    if len(body)+len(chunk) > self.MAX_RESPONSE_BYTES:
                        self.last_status = 'RESPONSE_TOO_LARGE'; receipt['state'] = self.last_status
                        self.receipts.append(receipt); return None
                    body.extend(chunk)
                raw = bytes(body)
            receipt.update(state='OBSERVED', sha256=sha256(raw).hexdigest(), bytes=len(raw),
                           retrieved_at=datetime.now(timezone.utc).isoformat())
            self.receipts.append(receipt); self.last_status = 'OBSERVED'; return raw
        except Exception:
            self.last_status = 'UNAVAILABLE'; receipt['state'] = self.last_status
            self.receipts.append(receipt); return None

    def search_sharedata(self, issuer, start, end):
        if not isinstance(start, date) or not isinstance(end, date) or not 0 <= (end-start).days <= 31:
            raise ValueError('inclusive window of at most 32 calendar dates required')
        url = 'https://www.sharedata.co.za/V2/Controls/Toolbox/SensSearch/SSJSONdata.aspx?'+urlencode(
            dict(date=start.strftime('%d %b %Y'), enddate=end.strftime('%d %b %Y'),
                 keyword='', sharecode=issuer.code, sectorcode=''))
        raw = self.read('sharedata_sens', url)
        if raw is None: return []
        leads = parse_search('sharedata_sens', raw, url, issuer)
        # Refuse widened or malformed responses rather than silently truncating dates.
        if any(x['published_at'] is None or not start <= x['published_at'].astimezone(SAST).date() <= end for x in leads):
            raise ValueError('search response outside requested dated window')
        return leads
