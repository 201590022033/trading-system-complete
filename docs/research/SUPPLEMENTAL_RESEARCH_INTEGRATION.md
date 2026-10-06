# Supplemental research integration - 6 October 2026

Owner requested integrating recovered sources. Dataset v2 preserves the 21 original canonical Yahoo charts and adds two separate research charts: Sasol IRESS OHLCV (250 completed bars, last session 5 October), and STX40 OST HLCV benchmark closes (600 retained completed bars, last session 5 October). Acquisition receipts retain original times, raw-file SHA256, provider/origin identity, purpose and explicitly unverified price/action, volume and historical availability semantics. Missing OST opens remain null; inconsistent HLC is not repaired. Original latest.json is backed up in ignored runtime before installation.

The existing collector attaches runtime/local-swing-data/supplemental.json to its bounded upload. Copies are whole-source series, not blended rows/fields. Receipts expire after four days from acquisition and current price freshness is checked independently. Repeated collection/upload cannot rejuvenate the export. Installing a later export requires explicit new acquisition receipts and matching source identities/closes. This is a manual-export supplement, not an automatic OST login/download service.

The dataset API remains compatible with v1 and accepts v2 through the existing authentication/body/date limits. Source provenance survives normalization and durable JSON persistence. UploadedFetcher's canonical get_chart remains unchanged; get_research_chart supplies current supplements only to technical shadow inputs. The paper worker freezes full-series technical values/source provenance and retains bounded research charts for future labels. Alpha repair does not alter an imported feed. Canonical source-session deduplication, ranking prices and cash/accounting remain unchanged. No manual worker or model cycle is run: the next scheduled new canonical session consumes this lane.

Technical decisions from a supplemental provider can mature only against a later export with the same provider/origin/price/volume basis. Updated raw-file hashes are allowed and recorded in outcomes. A source switch cannot silently label old Yahoo decisions or substitute Yahoo data when a broker export expires. Old frozen decisions/outcomes remain unchanged.

Historical AI research still evaluates canonical dataset.charts; supplements do not change its dataset hash, model budget, baseline/holdout evidence or proposal. B5 admission, automatic promotion and Live remain false. The dashboard shows current integrated input preview separately from last frozen worker features and pending/matured counts. Input preview may be AVAILABLE while the old worker snapshot remains PARTIAL until its scheduled update. Source semantics are still unverified; complete numerical inputs do not certify source semantics or strategy edge.

Runtime install retains Sasol acquisition 5 October 16:04:49 UTC and OST capture 6 October 07:36:52 UTC. Actual capture may follow the official 17:00 SAST close before the existing conservative next-UTC-day usability cutoff; both times remain distinct. The API rejects acquisition before the session close, future/stale capture, invalid Sasol OHLC/estimates, wrong identity/hash/basis and invented benchmark opens.

Operating command (from main checkout):

```powershell
.\.venv\Scripts\python.exe scripts/install_swing_supplements.py --iress-sasol <SOL-daily-table.csv> --ost-stx40 <STX40-history.csv> --sasol-acquired-at <actual-UTC-receipt> --stx40-acquired-at <actual-UTC-receipt>
```

The existing daily collection/upload subsequently retains current supplements. Fresh genuine later single-source exports remain required for prospective maturation. No private browser credentials or account/position information is included in uploads. Deployment uses a tracked-file Git archive, retaining existing hosted environment and schedule.

Ten new integration tests cover v1 compatibility, v2 roundtrip and provenance, malformed/future/stale receipts, invalid/estimated data, benchmark missing-open preservation, source expiry, unchanged canonical inputs and historical AI evaluation, worker freeze/deduplication and source-aware maturity. Final full safe suite: 950 tests passed in 88.271 seconds. All 54 protected checks passed before rollout; live deployment receipts follow below.
