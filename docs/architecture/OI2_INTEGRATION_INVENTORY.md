# OI2 Integration Inventory

| Capability | Existing asset used | OI2 status |
|---|---|---|
| Legacy signal | `signal_pipeline.legacy_technical_score` | Operational benchmark |
| Technical calculation | `UnifiedDataPipeline` | Operational on HR7 history |
| Point-in-time evidence | HR7 asset technical features | Default, historical |
| Yahoo quotes | `YahooFinanceFetcher` | On demand, graceful failure |
| SENS/Moneyweb | existing public fetchers | On demand, graceful failure |
| HR10 research | frozen reports/artifacts | Diagnostics only |
| Broker boundary | `provider_interfaces` | No live provider; handoff disabled |
| Simulation | legacy prototype/random fetchers | Not used by OI2 |

The previous inline prototype was a simulated presentation surface. Its
compatibility endpoints remain non-live but no longer generate simulated prices
or a fabricated trade idea.
