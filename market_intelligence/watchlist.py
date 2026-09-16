"""Deterministic hybrid pinned/dynamic investigation watchlist selector."""
from __future__ import annotations
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from .schemas import InstrumentCandidate, TickerSelection

def select_watchlist(candidates, *, pinned=(), existing=(), slots=3, now=None, confidence_floor=.55,
                     replacement_threshold=.15, minimum_display=timedelta(hours=6), cooldown=timedelta(hours=1),
                     max_replacements=1, corroboration_required=1):
    now = now or datetime.now(timezone.utc)
    pinned_ids={x.instrument_id for x in pinned}; result=list(pinned); replacements=0
    eligible=[c for c in candidates if c.instrument_id not in pinned_ids and c.confidence >= confidence_floor and len(c.source_evidence_ids) >= corroboration_required]
    eligible=sorted(eligible, key=lambda c:(-c.confidence, c.instrument_id))
    old={x.instrument_id:x for x in existing if not x.pinned}
    for candidate in eligible:
        if len(result) >= len(pinned)+slots: break
        prior=old.get(candidate.instrument_id)
        if prior:
            result.append(TickerSelection(candidate.instrument_id,candidate.display_symbol,False,candidate.reason,candidate.theme,candidate.confidence,candidate.source_evidence_ids,prior.selected_at,candidate.review_at))
        else:
            result.append(TickerSelection(candidate.instrument_id,candidate.display_symbol,False,candidate.reason,candidate.theme,candidate.confidence,candidate.source_evidence_ids,now.isoformat(),candidate.review_at))
    return tuple(result)
