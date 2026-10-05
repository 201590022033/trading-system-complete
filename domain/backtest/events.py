"""Optional evidence sidecar for local replay; it cannot change trades or scores."""
from datetime import datetime
from hashlib import sha256
import re
import unicodedata

from domain.evaluation.experiment import utc


def event_family(record):
    """Syndicated release grouping, not independent-publisher corroboration.

    Corrections and releases at different times keep separate groups. Full source
    records/revisions remain in each group; disagreeing bodies are never overwritten.
    """
    headline = re.split(r'\s+[–—-]\s+', record.headline, maxsplit=1)[-1]
    title = re.sub(r'[^a-z0-9]+', ' ', unicodedata.normalize('NFKD', headline).lower()).strip()
    parts = (record.metadata['issuer_isin'], record.published_at or 'UNKNOWN:'+record.evidence_id, title)
    return sha256('|'.join(parts).encode()).hexdigest()[:24]


def group_announcements(records):
    groups = {}
    for record in records:
        key = event_family(record)
        group = groups.setdefault(key, {'event_family_id': key, 'published_at': record.published_at,
            'headline': record.headline, 'evidence_ids': [], 'sources': [], 'content_versions': [],
            'independent_origin_count': 1, 'automatic_corporate_action': False})
        for field, value in (('evidence_ids', record.evidence_id), ('sources', record.source_id),
                             ('content_versions', record.metadata.get('content_sha256'))):
            if value and value not in group[field]: group[field].append(value)
    return sorted(groups.values(), key=lambda g: (g['published_at'] or '', g['event_family_id']))


def events_available_as_of(records, as_of):
    """Actual receipt/ingestion governs availability, not the historical release date."""
    cutoff = utc(as_of, 'as_of')
    visible = []
    for record in records:
        if record.published_at is None or record.metadata.get('identity_state') != 'CASH_CODE_AND_ISIN_IN_BODY':
            continue
        if record.metadata.get('body_state') != 'FULL_TEXT_PARSED':
            continue
        clocks = [utc(datetime.fromisoformat(value), 'evidence clock') for value in
                  (record.published_at, record.observed_at, record.ingested_at, record.metadata['available_at'])]
        published, observed, ingested, available = clocks
        if published <= observed <= ingested <= available <= cutoff:
            visible.append(record)
    return tuple(sorted(visible, key=lambda r: (r.published_at, r.evidence_id)))


def align_observed_price_context(records, daily, intraday):
    """Post-hoc release/day/slot alignment; no certified calendar or fill inference."""
    dates = {b['timestamp'][:10] for b in daily['bars']}
    slots = [(datetime.fromisoformat(b['timestamp']), b['timestamp']) for b in intraday['bars']]
    groups = group_announcements(records)
    result = []
    for group in groups:
        published = datetime.fromisoformat(group['published_at']) if group['published_at'] else None
        local_date = published.astimezone(datetime.fromisoformat(daily['bars'][0]['timestamp']).tzinfo).date().isoformat() if published else None
        following = next((text for at, text in slots if published and at >= published), None)
        result.append({**group, 'observed_daily_date': local_date if local_date in dates else None,
                       'first_observed_slot_start_at_or_after_release': following,
                       'basis': 'POSTHOC_RELEASE_ALIGNMENT_NOT_TRADABLE_AVAILABILITY',
                       'historical_eligible_evidence_count': len(events_available_as_of(
                           [r for r in records if r.evidence_id in group['evidence_ids']], published)) if published else 0})
    return result
