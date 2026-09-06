# ViewPoint authenticated discovery workflow

This is a user-controlled, read-only discovery procedure. The project does
not log in, capture credentials, read browser profiles, submit orders, or
accept raw authenticated captures.

## User steps (Chrome or Edge)

1. Create the local ignored folder `.viewpoint-discovery`.
2. Open a fresh Chrome/Edge window and log into Standard Bank ViewPoint
   normally, completing MFA/CAPTCHA yourself.
3. Open DevTools (`F12`), choose **Network**, enable **Preserve log**, and
   clear the log. Filter one action at a time: account/profile, cash/balance,
   portfolio/positions, open orders, optional history, an instrument, and a
   trade ticket. Close the ticket without submitting.
4. For each relevant Fetch/XHR/WebSocket/HTML observation, record only a
   redacted path or message type, method, response content type, transport,
   and field names. Do not save response values.
5. If exporting HAR is unavoidable, save it only under `.viewpoint-discovery`
   and remove request/response headers, cookies, authorization, tokens,
   session/CSRF values, account numbers and personal data before sharing.
6. Create a small JSON structural summary marked `"sanitized": true` using
   the shape documented by `viewpoint_discovery.py`; run the local validator
   before providing it. Delete the raw HAR afterward.

The validator rejects sensitive field names/markers and retains only
structural evidence. It does not claim sanitization is perfect; the user must
visually inspect the export first. No endpoint, selector, status, or broker
schema is considered verified until supplied in this form.

Current result: no authenticated ViewPoint evidence has been supplied.

## Binary WebSocket action correlation

Manual evidence identifies `data.iress.co.za` as an instrument/action-correlated
binary channel. This is VERIFIED only as an observation; it is not identified
as an order, quote, account, or portfolio channel. `trpc` produced a generic
subscription acknowledgement. The logger, settings, and Heap endpoints are
classified as telemetry/settings/third-party analytics and excluded from
candidate broker-transport reports.

Use `viewpoint_ws_discovery.py` with metadata recorded from DevTools: action
type/alias, socket host/path, direction, TEXT/BINARY type, byte length, and a
local SHA-256 hash. Never export frames. Compare repeated actions and aliases;
do not infer semantics from length, timing, or hash differences alone.

Minimal matrix: idle baseline; repeat one equity three times; compare two
equities; compare equity/ETF/future/index/commodity aliases where available;
change market/limit and stop controls; edit quantity/price; clear ticket;
open portfolio/trades/order pad/account selector. Close every ticket without
submitting. Retain raw frame material only in `.viewpoint-discovery/` and
delete it after metadata extraction.
