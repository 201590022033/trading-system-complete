# Alpha Vantage setup and current disabled state

Reviewed 5 October 2026. Keys were saved privately locally and on Railway. **Current `ALPHA_VANTAGE_ENABLED=0` on both local and cloud services.** The bounded probes did not verify JSE identity/history coverage. Do not interpret a saved key or a download advertisement as proof of access.

## Helper behavior versus deployed settings

`scripts/configure_alpha_vantage.ps1` prompts privately, preserves other local settings and uses stdin/native Railway CLI calls with `--skip-deploys`. It leaves local scheduled requests disabled, but **its Railway branch writes `ALPHA_VANTAGE_ENABLED=1`** for a future deployment. That is helper behavior, not today's verified cloud setting. Do not rerun the cloud branch simply to repeat setup: doing so changes the intended disabled configuration. Prefer `-LocalOnly` for an additional local key save; a reviewed future cloud key rotation must preserve the disabled flags privately afterward.

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File ./scripts/configure_alpha_vantage.ps1 -LocalOnly
```

The execution-policy override is confined to this process. `-UseSavedLocalKey` reuses a previously saved local key without printing it. Never paste a key/password into chat or print Railway variable listings. Setup receipts under ignored `.cache` contain no secret and do not prove coverage or deployment.

## Explicit coverage checks

`python -m scripts.alpha_vantage_probe SASOL` is a manual external request, excluded from safe tests. It uses the same persistent ignored probe cache and a five-call rolling-day budget; a symbol/history probe may use up to two calls. Reusing the cache preserves that budget. Exit 0 means verified history returned; exit 2 means coverage/configuration unresolved. `JSE_SYMBOL_UNVERIFIED` must not be treated as a data success.

Five actual bounded discovery calls did not establish unique South African ZAR coverage; foreign listings and provider-limit responses were not used to repair JSE bars. Free `TIME_SERIES_DAILY` compact is limited to up to 100 observations in this client's contract; it cannot supply the advertised 20-year JSE history or repair every older defect.

## Existing conditional repair logic

When explicitly enabled on a provider-fetch path, repair is only for invalid Yahoo research bars, using verified symbol/session/currency and matching real close. Good charts, duplicate sessions, status reads and worker retries do not trigger another call. The code's shared production limit is 20 requests per rolling day and five per minute, reserving five calls for local checks under the user's 25-call allowance. Other tools using the same key can still consume that allowance.

Current local daily collection does not call Alpha Vantage. The cloud's `LOCAL_UPLOAD` paper-input mode does not perform provider fallback. No automatic request is enabled to fill these defects, and there is no LLM-generated OHLCV fallback. See [provider matrix](MARKET_DATA_EXECUTION_MATRIX.md).
