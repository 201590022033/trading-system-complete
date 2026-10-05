# Local engine implementation record

B1 active: data/time contracts and independent oracle harness. Existing checkout verified clean at e6f47b0, master, expected origin. Baseline 869 offline safe tests passed (60.338s); protected verifier 54/54 passed. Authorization now covers B1–B5, superseding B0's planning-only scope.

B1 interfaces: immutable `domain.backtest.data.Manifest`, `Session`, `Bar`; raw prices, explicit actions, timezone-aware availability, complete expected-session windows, immutable content hashes. Toy holiday calendar is explicitly synthetic. Reconstructed archives do not establish historical availability. New research modules do not wire into runtime.

The independent fixture fixes Monday-close entry 102, stop 90, third subsequent session Friday close 106, ten shares, two-unit fee each way, cash 2036 from 2000. It is authored arithmetic, not implementation-generated truth.

B1 completed: three independent fixture/admission tests passed; full safe suite 872/872 (59.644s); protected 54/54; diff check passed. Calendar fixtures include a holiday, missing-session refusal and future changes ignored before availability. No real calendar/provider admission claim is made.
