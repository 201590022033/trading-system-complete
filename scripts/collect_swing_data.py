"""Collect once daily locally, retain raw history, then upload a bounded copy."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import os

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def collect(now, fetcher, keys):
    from application.opportunities.public_research import public_share_catalog, _available_at
    from application.opportunities.market_brief import CONTEXT_ETFS
    from market_chart_registry import MARKET_CHART_INSTRUMENTS
    catalog = public_share_catalog()
    symbols = {key: catalog[key]["yahoo_symbol"] for key in keys if key in catalog}
    symbols.update({key: MARKET_CHART_INSTRUMENTS[key].data_symbol for key in CONTEXT_ETFS})
    charts = {}
    for key, symbol in symbols.items():
        try:
            chart = fetcher.get_chart(symbol, "1y")
            bars = [{**{field: row.get(field) for field in ("open", "high", "low", "close", "volume")},
                     "timestamp": row["timestamp"][:10]}
                    for row in chart["bars"] if _available_at(row["timestamp"]) <= now]
            if bars:
                charts[key] = {"symbol": chart["symbol"], "interval": chart["interval"], "currency": chart["currency"], "bars": bars[-600:]}
        except Exception:
            continue
    return {"schema": "local-swing-dataset-v1", "observed_at": now.isoformat(), "charts": charts}


def attach_supplements(dataset, supplement, now):
    from copy import deepcopy
    from application.opportunities.supplemental_data import current_research_charts
    from application.opportunities.swing_research import validate_dataset
    result = deepcopy(dataset)
    # Upload observation is not the provider acquisition time.
    result['observed_at'] = now.isoformat()
    charts = current_research_charts(supplement, now)
    if charts:
        result.update(schema='local-swing-dataset-v2', research_charts=charts)
    else:
        result['schema'] = 'local-swing-dataset-v1'
        result.pop('research_charts', None)
    validate_dataset(result, now)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action="store_true")
    parser.add_argument("--retry-upload", action="store_true", help="Retry the saved snapshot without fetching prices")
    args = parser.parse_args()
    from ai_config import project_environment
    from application.opportunities.paper_config import PaperLoopConfig
    from application.opportunities.swing_research import validate_dataset
    from jse_adapter import YahooFinanceFetcher
    env = project_environment()
    folder = ROOT / "runtime" / "local-swing-data"
    folder.mkdir(parents=True, exist_ok=True)
    latest = folder / "latest.json"
    now = datetime.now(timezone.utc)
    from application.opportunities.ost_data import read_primary, fresh_charts, SCHEMA, POLICY
    primary = read_primary(folder)
    if primary is not None:
        dataset = {'schema': SCHEMA, 'source_policy': POLICY, 'observed_at': now.isoformat(),
                   'charts': fresh_charts(primary, now)}
        if not dataset['charts']:
            print(json.dumps({'state': 'OST_EXPORTS_EXPIRED', 'charts': 0, 'yahoo_fallback': False}))
            return 2
        dataset = validate_dataset(dataset, now)
        from application.opportunities.ost_data import atomic_json
        atomic_json(latest, dataset)
    elif args.retry_upload:
        dataset = json.loads(latest.read_text(encoding="utf-8"))
    else:
        receipt = folder / "collection-day.txt"
        if receipt.exists() and receipt.read_text() == now.date().isoformat() and latest.exists():
            dataset = json.loads(latest.read_text(encoding="utf-8"))
        else:
            config = PaperLoopConfig.load(env.get("PAPER_LOOP_CONFIG") or ROOT / "config" / "paper.railway.json")
            dataset = collect(now, YahooFinanceFetcher(), config.universe)
            validate_dataset(dataset, now)
            raw = json.dumps(dataset, allow_nan=False)
            staged = latest.with_suffix(".tmp")
            staged.write_text(raw, encoding="utf-8")
            os.replace(staged, latest)
            (folder / (now.date().isoformat()+".json")).write_text(raw, encoding="utf-8")
            receipt.write_text(now.date().isoformat())
    supplemental = folder / 'supplemental.json'
    if supplemental.exists() and primary is None:
        dataset = attach_supplements(dataset, json.loads(supplemental.read_text(encoding='utf-8')), now)
        staged = latest.with_suffix('.tmp')
        staged.write_text(json.dumps(dataset, allow_nan=False), encoding='utf-8')
        os.replace(staged, latest)
    if args.upload or args.retry_upload:
        from urllib.parse import urlparse
        import requests
        url, token = env.get("SWING_RESEARCH_URL", ""), env.get("SWING_DATA_UPLOAD_TOKEN", "")
        if urlparse(url).scheme != "https" or not token:
            raise ValueError("Private HTTPS upload configuration required")
        response = requests.post(url.rstrip("/")+"/api/v1/swing-research/datasets", json=dataset,
                                 headers={"Authorization": "Bearer "+token}, timeout=60, allow_redirects=False)
        if response.status_code != 202:
            print(json.dumps({"state": "UPLOAD_FAILED_LOCAL_COPY_RETAINED", "http_status": response.status_code}))
            return 2
        print(json.dumps({"state": "LOCAL_DATA_STORED_AND_UPLOADED", "charts": len(dataset["charts"])}))
        if env.get("WEEKLY_NEWS_RESEARCH_ENABLED") == "1":
            from scripts.weekly_news_research import run
            try:
                print(json.dumps(run(env)))
            except Exception:
                print(json.dumps({"state": "WEEKLY_RESEARCH_UNAVAILABLE_LOCAL_DATA_RETAINED"}))
    else:
        print(json.dumps({"state": "LOCAL_DATA_STORED", "charts": len(dataset["charts"])}))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception:
        print(json.dumps({"state": "COLLECTION_OR_UPLOAD_UNAVAILABLE", "credentials_disclosed": False}))
        raise SystemExit(2)
