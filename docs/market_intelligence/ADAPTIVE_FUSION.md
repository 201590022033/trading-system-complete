# Adaptive Fusion (Shadow Mode)

`adaptive_fusion.py` implements `adaptive-fusion-v1` beside the legacy score.
`JSESignalEngine` still returns its original fixed score, action, confidence and
threshold behavior. The adaptive result is explanatory metadata only.

## Factor contract

Each factor declares a name, category, bounded score, base weight,
availability, reliability and reliability sample count. Effective weights are
the product of:

`base weight * regime multiplier * profile multiplier * reliability multiplier`

Available effective weights are normalized before contributions are summed.
The report logs every multiplier, effective/normalized weight and signed
contribution, plus regime/profile context and the benchmark legacy result.

Reliability remains at the neutral multiplier until the configured minimum
sample gate (20 by default). Mature reliability multipliers are bounded from
0.5 to 1.5. Unknown factor categories are rejected.

## Current integration

The existing engine supplies legacy technical, aggregate sentiment and
profile-macro factors. With no connected historical reliability summary, the
sentiment factor remains at the conservative prior. Invalid/unavailable regime
history is recorded as unavailable and cannot interrupt legacy scoring.

This initial configuration is a hypothesis for M7 evaluation, not a promoted
production policy.
