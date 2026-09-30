"""
AtmoGraph Live News Monitor.

Continuously checks configured RSS feeds and sends new
articles through the existing AtmoGraph intelligence pipeline.

Architecture:

    RSS
     ↓
    NewsIngestionService
     ↓
    NLP
     ↓
    Event
     ↓
    Business Intelligence
     ↓
    GNN / Hybrid
     ↓
    Unified Intelligence

The monitor creates a fresh database session for every
monitoring cycle and always closes that session after use.

This service intentionally does NOT duplicate
the existing intelligence/business logic.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.core.database import SessionLocal

from app.services.news_ingestion_service import (
    NewsIngestionService,
)


logger = logging.getLogger(__name__)


# ============================================================
# LIVE NEWS MONITOR
# ============================================================


class LiveNewsMonitor:
    """
    Background RSS news monitor.

    The monitor periodically calls the existing
    NewsIngestionService.

    It does not implement:
        - NLP
        - supplier matching
        - business simulation
        - route analysis
        - resilience
        - risk
        - GNN

    Those responsibilities remain inside the
    existing intelligence pipeline.
    """

    def __init__(
        self,
        interval_seconds: int = 300,
        feed_url: Optional[str] = None,
        limit: int = 10,
        auto_simulate: bool = True,
    ) -> None:

        self.interval_seconds = max(
            30,
            int(interval_seconds),
        )

        self.feed_url = feed_url

        self.limit = max(
            1,
            min(int(limit), 50),
        )

        self.auto_simulate = bool(
            auto_simulate
        )

        self._task: Optional[
            asyncio.Task
        ] = None

        self._running = False

    # ========================================================
    # STATUS
    # ========================================================

    @property
    def running(self) -> bool:
        """
        Return whether the monitor is active.
        """

        return self._running

    # ========================================================
    # START
    # ========================================================

    def start(self) -> None:
        """
        Start the background news monitor.
        """

        if self._running:

            logger.info(
                "Live news monitor is already running."
            )

            return

        self._running = True

        self._task = asyncio.create_task(
            self._run(),
            name="atmograph-live-news-monitor",
        )

        logger.info(
            (
                "AtmoGraph live news monitor started "
                "(interval=%ss, limit=%s)."
            ),
            self.interval_seconds,
            self.limit,
        )

    # ========================================================
    # STOP
    # ========================================================

    async def stop(self) -> None:
        """
        Stop the background monitor cleanly.
        """

        self._running = False

        if self._task is None:
            return

        self._task.cancel()

        try:

            await self._task

        except asyncio.CancelledError:

            pass

        finally:

            self._task = None

        logger.info(
            "AtmoGraph live news monitor stopped."
        )

    # ========================================================
    # MAIN LOOP
    # ========================================================

    async def _run(self) -> None:
        """
        Main monitoring loop.

        The first RSS check happens immediately
        after application startup.

        Following checks happen according to
        interval_seconds.
        """

        # ----------------------------------------------------
        # Startup grace period before initial check
        # ----------------------------------------------------

        try:
            await asyncio.sleep(2)
            if self._running:
                await self._run_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Initial RSS check failed, continuing monitoring loop.")

        # ----------------------------------------------------
        # Continuous monitoring
        # ----------------------------------------------------

        while self._running:

            try:

                await asyncio.sleep(
                    self.interval_seconds
                )

                if not self._running:
                    break

                await self._run_once()

            except asyncio.CancelledError:

                raise

            except Exception:

                logger.exception(
                    "Unexpected error in "
                    "live news monitor loop."
                )

    # ========================================================
    # ONE MONITORING CYCLE
    # ========================================================

    async def _run_once(self) -> None:
        """
        Execute one RSS ingestion cycle.

        A fresh SQLAlchemy session is created for this
        monitoring cycle and closed after ingestion.

        The synchronous ingestion service runs inside
        a worker thread so the FastAPI event loop remains
        responsive.
        """

        db = None

        try:

            logger.info(
                "Live news monitor: checking RSS feed."
            )

            # ------------------------------------------------
            # Create a fresh DB session for this cycle.
            # ------------------------------------------------

            db = SessionLocal()

            service = NewsIngestionService(db)

            # ------------------------------------------------
            # Existing ingestion pipeline.
            # ------------------------------------------------

            result = await asyncio.to_thread(
                service.ingest_rss,
                feed_url=self.feed_url,
                limit=self.limit,
                auto_simulate=self.auto_simulate,
            )

            data = (
                result.get(
                    "data",
                    result,
                )
                if isinstance(result, dict)
                else {}
            )

            logger.info(
                (
                    "Live news monitor cycle completed: "
                    "found=%s processed=%s "
                    "skipped=%s failed=%s"
                ),
                data.get(
                    "articles_found",
                    0,
                ),
                data.get(
                    "processed_count",
                    0,
                ),
                data.get(
                    "skipped_count",
                    0,
                ),
                data.get(
                    "failed_count",
                    0,
                ),
            )

        except Exception:

            logger.exception(
                "Live news monitor cycle failed."
            )

        finally:

            # ------------------------------------------------
            # Always close the DB session.
            # ------------------------------------------------

            if db is not None:

                try:

                    db.close()

                except Exception:

                    logger.exception(
                        "Failed to close live news "
                        "monitor database session."
                    )


# ============================================================
# APPLICATION-LEVEL MONITOR
# ============================================================


live_news_monitor = LiveNewsMonitor(
    interval_seconds=300,
    limit=10,
    auto_simulate=True,
)