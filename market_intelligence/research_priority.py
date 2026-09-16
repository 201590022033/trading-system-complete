"""Non-trading bridge from intelligence candidates to research attention."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any

@dataclass(frozen=True)
class InvestigationPriority:
    instrument_id: str
    display_symbol: str
    priority: float
    reason: str
    source_evidence_ids: tuple[str, ...]
    research_only: bool = True

def build_priorities(candidates, resolver) -> tuple[InvestigationPriority, ...]:
    result=[]
    for candidate in candidates:
        try: resolved=resolver.resolve(candidate.instrument_id)
        except (KeyError, ValueError): continue
        result.append(InvestigationPriority(resolved.instrument_id, candidate.display_symbol,
            candidate.confidence, candidate.reason, tuple(candidate.source_evidence_ids)))
    return tuple(sorted(result, key=lambda x:(-x.priority,x.instrument_id)))
