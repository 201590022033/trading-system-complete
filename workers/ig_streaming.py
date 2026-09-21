"""Durable IG Demo streaming ingestion worker. Read-only: no orders."""
from dataclasses import dataclass
from datetime import datetime, timezone
import os
import threading
from typing import Callable

from shadow_learning import JobCheckpoint, ObservationRecord, stable_id, timestamp


IG_STREAM_JOB_INTERVAL_SECONDS = 60


@dataclass(frozen=True)
class IGStreamIngestionConfig:
    """Operator-controlled streaming ingestion bounds."""
    enabled: bool
    instruments: tuple[str, ...]  # "CANONICAL_ID:EPIC"
    run_seconds: int
    stale_after_seconds: int

    @classmethod
    def from_env(cls, environ=None):
        environ = os.environ if environ is None else environ
        enabled = environ.get("IG_STREAM_ENABLED", "0").strip() == "1"
        raw = environ.get("IG_STREAM_INSTRUMENTS", "").strip()
        instruments = tuple(x.strip() for x in raw.split(",") if x.strip() and ":" in x)
        run_seconds = int(environ.get("IG_STREAM_RUN_SECONDS", "25") or "25")
        stale_after_seconds = int(environ.get("IG_STREAM_STALE_AFTER_SECONDS", "30") or "30")
        if run_seconds < 1 or run_seconds > 60:
            raise ValueError("IG_STREAM_RUN_SECONDS must be between 1 and 60")
        if stale_after_seconds < 1:
            raise ValueError("IG_STREAM_STALE_AFTER_SECONDS must be positive")
        return cls(enabled, instruments, run_seconds, stale_after_seconds)


class IGStreamIngestion:
    """Bounded, read-only ingestion of IG Demo PRICE updates into the observation ledger."""

    def __init__(self, repository, config, *, clock=None, transport_factory=None, adapter_factory=None):
        self.repository = repository
        self.config = config
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.transport_factory = transport_factory or self._default_transport
        self.adapter_factory = adapter_factory or self._default_adapter
        # Lightstreamer may deliver PRICE callbacks concurrently. PostgreSQL
        # repositories use one connection per worker, so serialize immutable
        # observation writes and keep transaction/savepoint ownership intact.
        self._save_lock = threading.Lock()
        self._last_health = {"status": "NOT_STARTED", "observations": 0, "error": None,
                             "live_execution": False}

    @staticmethod
    def _default_transport(on_observation=None):
        from domain.broker.ig_lightstreamer import LightstreamerTransport
        return LightstreamerTransport(on_observation=on_observation)

    @staticmethod
    def _default_adapter(config):
        from domain.broker.ig import IGReadOnlyAdapter
        return IGReadOnlyAdapter(config)

    def _build_mappings(self, adapter):
        from domain.broker.ig import IGMapping
        mappings = []
        for item in self.config.instruments:
            canonical_id, epic = item.split(":", 1)
            market = adapter.get_market(epic)
            mappings.append(IGMapping(
                canonical_instrument_id=canonical_id,
                broker="IG",
                epic=market.epic,
                environment="DEMO",
                product_variant=market.instrument_type,
                market_name=market.name,
                mapping_status="CANDIDATE / RESEARCH",
            ))
        return mappings

    def _to_observation_record(self, obs):
        observed_at = obs.source_timestamp or obs.received_at
        return ObservationRecord(
            observation_id=stable_id("ig-obs", obs.instrument_id, obs.epic, observed_at.isoformat()),
            instrument=obs.instrument_id,
            observed_at=observed_at.isoformat(),
            horizon="streaming",
            market_data={
                "bid": obs.bid,
                "ask": obs.ask,
                "mid": obs.mid,
                "spread": obs.spread,
                "last": obs.last,
                "market_status": obs.market_status,
                "stale": obs.stale,
                "delayed": obs.delayed,
                "ordering_state": obs.ordering_state.value if obs.ordering_state is not None else None,
            },
            research_context={
                "broker": obs.broker,
                "epic": obs.epic,
                "subscription_id": obs.subscription_id,
                "source_version": obs.source_version,
                "provenance": obs.provenance,
            },
            source_version=obs.source_version or "unknown",
            pipeline_version="ig-streaming-ingestion-v1",
            created_at=self.clock().isoformat(),
        )

    def run_once(self, *, stop_event=None):
        """Connect, collect observations for a bounded window, disconnect, return health."""
        if not self.config.enabled or not self.config.instruments:
            self._last_health = {"status": "DISABLED", "observations": 0, "error": None,
                                 "live_execution": False}
            return self._last_health

        from domain.broker.ig import IGConfig, IGReadOnlyAdapter, IGRequestError
        from domain.broker.ig_streaming import IGMarketStream

        observations = []
        stream = None
        event = stop_event or threading.Event()

        def on_observation(value):
            record = self._to_observation_record(value)
            with self._save_lock:
                self.repository.save_observation(record)
                observations.append(record.observation_id)

        timer = None
        try:
            config = IGConfig.from_env()
            adapter = self.adapter_factory(config)
            adapter.authenticate()
            mappings = self._build_mappings(adapter)
            transport = self.transport_factory(on_observation=on_observation)
            stream = IGMarketStream(
                adapter, mappings, transport=transport,
                stale_after_seconds=self.config.stale_after_seconds)
            stream.connect()
            if stop_event is None:
                timer = threading.Timer(self.config.run_seconds, event.set)
                timer.start()
            event.wait(self.config.run_seconds + 5)
            health = stream.health(self.clock())
            self._last_health = {
                "status": health.status.value,
                "observations": len(observations),
                "error": health.error,
                "connected": health.connected,
                "subscriptions": health.subscription_count,
                "reconnect_attempts": health.reconnect_attempts,
                "live_execution": False,
            }
        except IGRequestError as exc:
            self._last_health = {
                "status": "AUTH_FAILED" if exc.error_category == "AUTHENTICATION_FAILED" else "REQUEST_FAILED",
                "observations": len(observations),
                "error": exc.safe_message,
                "live_execution": False,
            }
        except Exception as exc:
            self._last_health = {
                "status": "FAILED",
                "observations": len(observations),
                "error": str(exc),
                "live_execution": False,
            }
        finally:
            if timer is not None:
                timer.cancel()
            if stream is not None:
                try:
                    stream.disconnect()
                except Exception:
                    pass
        return self._last_health

    def health(self):
        return dict(self._last_health)


class IGStreamScheduler:
    """Enqueue one bounded IG stream ingestion job per minute bucket."""

    def __init__(self, repository, interval_seconds=IG_STREAM_JOB_INTERVAL_SECONDS):
        if not isinstance(interval_seconds, int) or interval_seconds < 10:
            raise ValueError("bounded stream scheduling interval required")
        self.repository = repository
        self.interval = interval_seconds

    def enqueue(self, now):
        at = timestamp(now)
        bucket = int(at.timestamp()) // self.interval * self.interval
        target = datetime.fromtimestamp(bucket, timezone.utc).isoformat()
        job = JobCheckpoint(
            stable_id("ig-stream-ingestion", target),
            "ig-stream-ingestion", target, checkpoint={})
        self.repository.ensure_job(job)
        return job


def compose_ig_stream_worker(repository):
    """Return scheduler and handler for continuous IG streaming ingestion."""
    from workers.runtime import runtime_handlers
    config = IGStreamIngestionConfig.from_env()
    if not config.enabled:
        return None, None
    scheduler = IGStreamScheduler(repository)
    handlers = runtime_handlers(repository)
    return scheduler, handlers["ig-stream-ingestion"]
