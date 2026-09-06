# ADR 0023 — ViewPoint proprietary transport discovery

Status: accepted, 2026-09-06

Before any protocol parsing, ViewPoint discovery records human-annotated
actions and sanitized WebSocket metadata. Raw frames remain local and ignored;
exports contain only host/path, direction, frame type, length and a one-way
SHA-256 hash. The observed `data.iress.co.za` binary channel is described as
instrument/action-correlated only. Hash, timing and length cannot establish
whether it carries quotes, tickets, account state, or orders.

Known logger, user-settings and Heap endpoints are classified as non-broker
transport. No decoder, offsets, selectors, endpoint guesses or submission path
are introduced. Final order submission remains human-controlled.
