"""Provider-neutral, validated Market AI analysis boundary."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Protocol
import math
from .schemas import DocumentFact, MarketDocumentAnalysis, SCHEMA_VERSION

PROMPT_VERSION = "market-intelligence-prompt-v1"

class StructuredAnalysisProvider(Protocol):
    name: str
    model: str
    def analyse(self, *, title: str, text: str) -> dict[str, Any]: ...

def validate_analysis(raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict): raise ValueError("analysis must be an object")
    for key in ("facts", "themes", "candidates", "uncertainties", "contradictions"):
        if not isinstance(raw.get(key), list): raise ValueError(f"{key} must be a list")
        if len(raw[key])>100: raise ValueError("analysis collection exceeds bound")
    def text(value):
        if not isinstance(value,str) or not value.strip() or len(value)>10000: raise ValueError('invalid analysis text')
    def confidence(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value) or not 0<=value<=1:
            raise ValueError('invalid confidence')
    def strings(value):
        if not isinstance(value,list): raise ValueError('string list required')
        for item in value: text(item)
    for fact in raw['facts']:
        if not isinstance(fact,dict): raise ValueError('fact object required')
        text(fact.get('fact'))
        if not isinstance(fact.get('source_span',''),str): raise ValueError('invalid source span')
        confidence(fact.get('confidence',1.0))
    for theme in raw['themes']:
        if not isinstance(theme,dict): raise ValueError('theme object required')
        text(theme.get('theme')); text(theme.get('expected_horizon')); confidence(theme.get('confidence'))
        if isinstance(theme.get('direction'),bool) or theme.get('direction') not in (-1,0,1): raise ValueError('invalid theme direction')
        for key in ('affected_sectors','affected_asset_classes','potentially_affected_instruments'):
            strings(theme.get(key,[]))
        for key in ('supporting_evidence','contradictory_evidence'):
            if not isinstance(theme.get(key,[]),list): raise ValueError('evidence list required')
            for evidence in theme.get(key,[]):
                if not isinstance(evidence,dict): raise ValueError('evidence object required')
                for name in ('evidence_id','source_id','source_name','headline'): text(evidence.get(name))
                if evidence.get('direction') not in (-1,0,1): raise ValueError('invalid evidence direction')
                confidence(evidence.get('strength'))
    for candidate in raw['candidates']:
        if not isinstance(candidate,dict): raise ValueError('candidate object required')
        for key in ('instrument_id','display_symbol','reason','theme'): text(candidate.get(key))
        confidence(candidate.get('confidence')); strings(candidate.get('source_evidence_ids',[]))
    for key in ('uncertainties','contradictions'): strings(raw[key])
    usage=raw.get('usage',{})
    if not isinstance(usage,dict) or any(key not in {'input_tokens','output_tokens','total_tokens'}
        or isinstance(value,bool) or not isinstance(value,int) or value<0 for key,value in usage.items()):
        raise ValueError('invalid usage metadata')
    from .schemas import MarketTheme,InstrumentCandidate,SourceEvidence
    for theme in raw['themes']:
        value=dict(theme)
        for key in ('supporting_evidence','contradictory_evidence'):
            value[key]=[SourceEvidence(**item) for item in value.get(key,[])]
        MarketTheme(**value)
    for candidate in raw['candidates']: InstrumentCandidate(**candidate)
    return raw

def analyse_document(document, provider: StructuredAnalysisProvider, *, content_hash: str, analysis_id: str, now: str | None = None) -> MarketDocumentAnalysis:
    raw=validate_analysis(provider.analyse(title=document.title, text=document.metadata.get("text", "")))
    facts=[DocumentFact(str(x.get("fact", "")), str(x.get("source_span", "")), float(x.get("confidence", 1.0))) for x in raw["facts"] if isinstance(x,dict) and x.get("fact")]
    return MarketDocumentAnalysis(analysis_id, document.document_id, provider.name, provider.model, SCHEMA_VERSION,
        PROMPT_VERSION, content_hash, now or datetime.now(timezone.utc).isoformat(), facts,
        raw["themes"], raw["candidates"], [str(x) for x in raw["uncertainties"]], [str(x) for x in raw["contradictions"]],
        dict(raw.get("usage", {})))
