# ADR 0054 - Supplemental research inputs

Date: 6 October 2026. Status: accepted.

Owner requested integrating recovered sources. Extend the existing dataset API to local-swing-dataset-v2, retaining canonical Yahoo charts and adding research_charts with bounded provider, file hash and acquisition provenance. Explicit SOL.JSE IRESS and STX40 OST mappings only. Never combine bars or fields across feeds. Acquisition time is separate from upload observation; exclude unfinished sessions and expire supplemental acquisition after four days. Originals and immutable past decisions remain intact.

UploadedFetcher supplies supplemental charts to technical shadow calculations only. Canonical ranking/accounting, existing duplicate-session/frozen retry behavior and model budgets remain intact. The dashboard distinguishes current input preview from last frozen worker decision. Existing normal worker schedule consumes supplements on its next new canonical session, not a manually forced broker/model cycle.

Adjustment/action, volume and historical availability semantics remain unverified. Prospective shadow observation is permitted; historical baseline/AI evaluation stays on canonical inputs and does not certify imported retrospective data. B5 replay admission and promotion remain false. Current source preview becomes unavailable after four days; a fresh upload cannot rejuvenate an old export. Reuse the existing collector with an ignored supplemental receipt file, independently hash and compare bar content, and retain the original latest snapshot before installing v2.
