"""
AtmoGraph News Ingestion Service.

Responsibilities:

1. Manual news -> NLP -> Event
2. External RSS feed -> Article extraction
3. RSS article -> IntelligencePipeline
4. Duplicate article protection
5. Canonical intelligence response
6. Real-time WebSocket intelligence updates

Architecture:

External RSS
    ↓
RSS Parser
    ↓
Article
    ↓
IntelligencePipeline
    ↓
NLP
    ↓
Event
    ↓
Supplier / Entity Resolution
    ↓
Business Simulation
    ↓
Route Impact
    ↓
Resilience
    ↓
Risk
    ↓
GNN / Hybrid Prediction
    ↓
Unified Intelligence
    ↓
WebSocket
    ↓
Frontend
"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET

from sqlalchemy.orm import Session

from app.models.event import Event
from app.services.nlp_engine import nlp_engine
from app.api.routes.websocket import manager


class NewsIngestionService:
    """News ingestion and external RSS processing service."""

    DEFAULT_RSS_URL = (
        "https://news.google.com/rss/search"
        "?q=supply+chain+disruption"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    USER_AGENT = (
        "AtmoGraph/1.0 "
        "(Supply Chain Intelligence)"
    )

    def __init__(
        self,
        db: Session,
    ) -> None:

        self.db = db

    # =========================================================
    # TEXT HELPERS
    # =========================================================

    @staticmethod
    def _clean_text(
        value: str | None,
    ) -> str:

        if not value:

            return ""

        value = html.unescape(
            str(value)
        )

        value = re.sub(
            r"<[^>]+>",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    # =========================================================
    # URL VALIDATION
    # =========================================================

    @staticmethod
    def _validate_url(
        url: str,
    ) -> str:

        url = str(url).strip()

        parsed = urlparse(
            url
        )

        if parsed.scheme not in {
            "http",
            "https",
        }:

            raise ValueError(
                "RSS feed URL must use "
                "http or https."
            )

        if not parsed.netloc:

            raise ValueError(
                "Invalid RSS feed URL."
            )

        return url

    # =========================================================
    # FETCH RSS
    # =========================================================

    def fetch_feed(
        self,
        feed_url: str,
        timeout: int = 15,
    ) -> str:

        feed_url = self._validate_url(
            feed_url
        )

        request = Request(
            feed_url,
            headers={
                "User-Agent": self.USER_AGENT,
                "Accept": (
                    "application/rss+xml, "
                    "application/atom+xml, "
                    "application/xml, "
                    "text/xml, "
                    "*/*"
                ),
            },
        )

        try:

            with urlopen(
                request,
                timeout=timeout,
            ) as response:

                raw = response.read()

        except Exception as exc:

            raise RuntimeError(
                f"Unable to fetch RSS feed: {exc}"
            ) from exc

        try:

            return raw.decode(
                "utf-8",
                errors="replace",
            )

        except Exception as exc:

            raise RuntimeError(
                f"Unable to decode RSS feed: {exc}"
            ) from exc

    # =========================================================
    # XML HELPERS
    # =========================================================

    @staticmethod
    def _find_text(
        element: ET.Element,
        names: list[str],
    ) -> str:

        for name in names:

            child = element.find(
                name
            )

            if child is not None:

                value = (
                    child.text
                    or ""
                ).strip()

                if value:

                    return value

        return ""

    @staticmethod
    def _find_atom_text(
        element: ET.Element,
        local_name: str,
    ) -> str:

        for child in list(
            element
        ):

            tag = child.tag

            if "}" in tag:

                tag = tag.split(
                    "}",
                    1,
                )[1]

            if tag == local_name:

                value = (
                    child.text
                    or ""
                ).strip()

                if value:

                    return value

        return ""

    @staticmethod
    def _find_atom_link(
        element: ET.Element,
    ) -> str:

        for child in list(
            element
        ):

            tag = child.tag

            if "}" in tag:

                tag = tag.split(
                    "}",
                    1,
                )[1]

            if tag != "link":

                continue

            href = child.attrib.get(
                "href",
                "",
            ).strip()

            if href:

                return href

            value = (
                child.text
                or ""
            ).strip()

            if value:

                return value

        return ""

    # =========================================================
    # RSS PARSER
    # =========================================================

    def parse_feed(
        self,
        xml_text: str,
        feed_url: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:

        try:

            root = ET.fromstring(
                xml_text
            )

        except ET.ParseError as exc:

            raise RuntimeError(
                f"Invalid RSS/Atom XML: {exc}"
            ) from exc

        articles: list[
            dict[str, Any]
        ] = []

        # -----------------------------------------------------
        # RSS 2.0
        # -----------------------------------------------------

        rss_items = root.findall(
            ".//item"
        )

        for item in rss_items:

            title = self._find_text(
                item,
                [
                    "title",
                ],
            )

            description = self._find_text(
                item,
                [
                    "description",
                    "content",
                ],
            )

            link = self._find_text(
                item,
                [
                    "link",
                ],
            )

            published = self._find_text(
                item,
                [
                    "pubDate",
                    "published",
                    "updated",
                ],
            )

            source = self._find_text(
                item,
                [
                    "source",
                ],
            )

            title = self._clean_text(
                title
            )

            description = self._clean_text(
                description
            )

            if not title:

                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "url": link,
                    "published_at": published,
                    "source": (
                        source
                        or urlparse(
                            feed_url
                        ).netloc
                    ),
                }
            )

            if len(articles) >= limit:

                return articles

        # -----------------------------------------------------
        # Atom
        # -----------------------------------------------------

        atom_entries = []

        for element in root.iter():

            tag = element.tag

            if "}" in tag:

                tag = tag.split(
                    "}",
                    1,
                )[1]

            if tag == "entry":

                atom_entries.append(
                    element
                )

        for entry in atom_entries:

            title = self._find_atom_text(
                entry,
                "title",
            )

            description = (
                self._find_atom_text(
                    entry,
                    "summary",
                )
                or self._find_atom_text(
                    entry,
                    "content",
                )
            )

            link = self._find_atom_link(
                entry
            )

            published = (
                self._find_atom_text(
                    entry,
                    "published",
                )
                or self._find_atom_text(
                    entry,
                    "updated",
                )
            )

            title = self._clean_text(
                title
            )

            description = self._clean_text(
                description
            )

            if not title:

                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "url": link,
                    "published_at": published,
                    "source": urlparse(
                        feed_url
                    ).netloc,
                }
            )

            if len(articles) >= limit:

                break

        return articles

    # =========================================================
    # DUPLICATE CHECK
    # =========================================================

    def article_exists(
        self,
        title: str,
    ) -> bool:

        normalized = self._clean_text(
            title
        ).lower()

        if not normalized:

            return False

        existing_events = (
            self.db.query(Event)
            .all()
        )

        for event in existing_events:

            existing_title = (
                self._clean_text(
                    event.title
                ).lower()
            )

            if (
                existing_title
                == normalized
            ):

                return True

        return False

    # =========================================================
    # MANUAL NEWS
    # =========================================================

        # =========================================================
    # MANUAL NEWS -> COMPLETE INTELLIGENCE PIPELINE
    # =========================================================

    def process_news(
        self,
        title: str,
        description: str = "",
        source: str | None = None,
        auto_simulate: bool = True,
    ) -> dict[str, Any]:
        """
        Analyze manual news through the complete AtmoGraph
        intelligence pipeline.

        Flow:

            Manual News
                ↓
            IntelligencePipeline
                ↓
            NLP
                ↓
            Event
                ↓
            Entity Resolution
                ↓
            Location Resolution
                ↓
            Business Supply Chain
                ↓
            Simulation
                ↓
            Graph
                ↓
            Prediction
        """

        title = str(title or "").strip()
        description = str(
            description or ""
        ).strip()

        if not title:
            raise ValueError(
                "News title is required."
            )

        if not description:
            raise ValueError(
                "News description is required."
            )

        # -----------------------------------------------------
        # Use the SAME canonical pipeline as RSS ingestion.
        # -----------------------------------------------------

        from app.services.intelligence_pipeline import (
            IntelligencePipeline,
        )

        pipeline = IntelligencePipeline(
            self.db
        )

        result = pipeline.process(
            title=title,
            description=description,
            source=source or "manual",
            auto_simulate=auto_simulate,
        )

        return result
    # =========================================================
    # WEBSOCKET HELPERS
    # =========================================================

    @staticmethod
    def _broadcast_intelligence(
        *,
        event_id: int | None,
        graph_id: str | None,
        intelligence: dict[str, Any],
    ) -> None:
        """
        Broadcast the canonical intelligence result.

        This method is intentionally non-blocking.

        The ingestion pipeline is synchronous and may run in
        asyncio.to_thread(), so the WebSocket manager handles
        thread-safe scheduling onto FastAPI's main event loop.
        """

        if event_id is None:

            return

        # -----------------------------------------------------
        # EVENT CREATED
        # -----------------------------------------------------

        event_data = intelligence.get(
            "event",
            {},
        )

        manager.broadcast_from_thread(
            "EVENT_CREATED",
            data=event_data,
            event_id=event_id,
            graph_id=graph_id,
        )

        # -----------------------------------------------------
        # IMPACT UPDATED
        # -----------------------------------------------------

        impact_data = {
            "business_impact": intelligence.get(
                "business_impact",
                {},
            ),
            "supplier_exposure": intelligence.get(
                "supplier_exposure",
                {},
            ),
            "route_impact": intelligence.get(
                "route_impact",
                {},
            ),
            "resilience": intelligence.get(
                "resilience",
                {},
            ),
        }

        manager.broadcast_from_thread(
            "IMPACT_UPDATED",
            data=impact_data,
            event_id=event_id,
            graph_id=graph_id,
        )

        # -----------------------------------------------------
        # RISK UPDATED
        # -----------------------------------------------------

        manager.broadcast_from_thread(
            "RISK_UPDATED",
            data=intelligence.get(
                "risk",
                {},
            ),
            event_id=event_id,
            graph_id=graph_id,
        )

        # -----------------------------------------------------
        # PREDICTION UPDATED
        # -----------------------------------------------------

        manager.broadcast_from_thread(
            "PREDICTION_UPDATED",
            data=intelligence.get(
                "prediction",
                {},
            ),
            event_id=event_id,
            graph_id=graph_id,
        )

        # -----------------------------------------------------
        # GRAPH UPDATED
        # -----------------------------------------------------

        manager.broadcast_from_thread(
            "GRAPH_UPDATED",
            data={
                "event_id": event_id,
                "graph_id": graph_id,
            },
            event_id=event_id,
            graph_id=graph_id,
        )

        # -----------------------------------------------------
        # COMPLETE INTELLIGENCE
        # -----------------------------------------------------

        manager.broadcast_from_thread(
            "INTELLIGENCE_UPDATED",
            data=intelligence,
            event_id=event_id,
            graph_id=graph_id,
        )

    # =========================================================
    # COMPLETE RSS INTELLIGENCE
    # =========================================================

    def ingest_rss(
        self,
        feed_url: str | None = None,
        limit: int = 10,
        auto_simulate: bool = True,
    ) -> dict[str, Any]:

        feed_url = (
            feed_url
            or self.DEFAULT_RSS_URL
        )

        if limit < 1:

            limit = 1

        if limit > 50:

            limit = 50

        xml_text = self.fetch_feed(
            feed_url
        )

        articles = self.parse_feed(
            xml_text=xml_text,
            feed_url=feed_url,
            limit=limit,
        )

        # -----------------------------------------------------
        # Lazy imports.
        # -----------------------------------------------------

        from app.services.intelligence_pipeline import (
            IntelligencePipeline,
        )

        from app.services.unified_intelligence_service import (
            UnifiedIntelligenceService,
        )

        pipeline = IntelligencePipeline(
            self.db
        )

        processed: list[
            dict[str, Any]
        ] = []

        skipped: list[
            dict[str, Any]
        ] = []

        failed: list[
            dict[str, Any]
        ] = []

        for article in articles:

            title = article.get(
                "title",
                "",
            )

            description = article.get(
                "description",
                "",
            )

            source = (
                article.get(
                    "source"
                )
                or urlparse(
                    feed_url
                ).netloc
            )

            if not title:

                continue

            # -------------------------------------------------
            # DUPLICATE
            # -------------------------------------------------

            if self.article_exists(
                title
            ):

                skipped.append(
                    {
                        "title": title,
                        "reason": "duplicate",
                    }
                )

                continue

            # -------------------------------------------------
            # COMPLETE INTELLIGENCE PIPELINE
            # -------------------------------------------------

            try:

                try:

                    result = pipeline.process(
                        title=title,
                        description=description,
                        source=source,
                        auto_simulate=(
                            auto_simulate
                        ),
                    )

                except TypeError as exc:

                    if (
                        "auto_simulate"
                        not in str(exc)
                    ):

                        raise

                    result = pipeline.process(
                        title=title,
                        description=description,
                        source=source,
                    )

                intelligence = (
                    UnifiedIntelligenceService.build(
                        result
                    )
                )

                event_id = (
                    result.get(
                        "event_id"
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else None
                )

                graph_id = (
                    result.get(
                        "graph_id"
                    )
                    if isinstance(
                        result,
                        dict,
                    )
                    else None
                )

                # -------------------------------------------------
                # REAL-TIME BROADCAST
                # -------------------------------------------------

                self._broadcast_intelligence(
                    event_id=event_id,
                    graph_id=graph_id,
                    intelligence=intelligence,
                )

                processed.append(
                    {
                        "title": title,
                        "url": article.get(
                            "url"
                        ),
                        "published_at": article.get(
                            "published_at"
                        ),
                        "source": source,
                        "event_id": event_id,
                        "graph_id": graph_id,
                        "intelligence": intelligence,
                    }
                )

            except Exception as exc:

                self.db.rollback()

                failed.append(
                    {
                        "title": title,
                        "url": article.get(
                            "url"
                        ),
                        "error": str(exc),
                    }
                )

        return {
            "feed_url": feed_url,
            "articles_found": len(
                articles
            ),
            "processed_count": len(
                processed
            ),
            "skipped_count": len(
                skipped
            ),
            "failed_count": len(
                failed
            ),
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
        }


__all__ = [
    "NewsIngestionService",
]