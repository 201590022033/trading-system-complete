# Operational Decision UI Prototype

## Purpose and startup

Run `.venv/bin/python app.py`, then open `http://127.0.0.1:5000/`.
The existing route remains a Flask/Socket.IO prototype. Every price is produced
by an in-memory random walk and labelled `SIMULATED · RESEARCH · NOT LIVE`.

## Main card

The fabricated Sasol card tests this scan order: instrument and direction;
current price/source/time; horizon; entry, stop and target; maximum risk and
size; evidence; rationale; and execution method. Safety-critical values remain
visible. Research details are collapsed. The layout drops from four to two
columns and stacks content below 760px for tablet/phone review.

The example is deliberately `REJECTED RESEARCH`, refers to HR10's 0/40 result,
and is not sourced from HR9. `/api/demo-suggestion` exposes the same canonical
safety state. Copying produces demo text only; the Shyft action opens its public
information page; manual execution is disabled. There is no server order route.

Feedback is stored only in browser `localStorage` under `oi1-ui-feedback`; it is
not sent, written to the repository or committed. Use it for comments such as
confusing, unnecessary, missing, should be larger, or needs explanation.
