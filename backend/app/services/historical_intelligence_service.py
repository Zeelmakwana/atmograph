from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Any

from sqlalchemy.orm import Session

from app.models.event import Event
from app.services.event_impact_graph_service import EventImpactGraphService
from app.services.nlp_engine import nlp_engine
from app.services.intelligence_pipeline import IntelligencePipeline
from app.services.prediction_engine import predict_event_impact
from app.services.unified_intelligence_service import UnifiedIntelligenceService
from app.services.hybrid_prediction_service import HybridPredictionService

class HistoricalIntelligenceService:
    """
    Historical Intelligence layer.

    Responsibilities:
    - Browse historical events.
    - Group similar events into deterministic clusters.
    - Build an event-family timeline.
    - Replay an event through the existing business impact graph.
    
    Business simulation / business graph remains the source of truth.
    ML is not allowed to overwrite historical business facts.
    """

    VERSION = "1.0"
    MAX_LIMIT = 500

    _STOPWORDS = {
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "at",
        "to",
        "for",
        "and",
        "or",
        "is",
        "are",
        "was",
        "were",
        "with",
        "from",
        "affects",
        "affecting",
        "faces",
        "causes",
        "causing",
        "major",
        "critical",
        "high",
        "medium",
        "low",
        "disruption",
        "disrupted",
        "supply",
        "chain",
    }

    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # HISTORY
    # ------------------------------------------------------------------

    def list_history(
        self,
        *,
        company_id: str = "",
        search: str = "",
        severity: str = "",
        status: str = "",
        event_type: str = "",
        source: str = "",
        limit: int = 100,
    ) -> dict[str, Any]:

        limit = max(1, min(int(limit), self.MAX_LIMIT))

        query = self.db.query(Event)

        # Multi-business scoping: isolate historical events by company
        if company_id and company_id.strip():
            cid = company_id.strip()
            if cid in ("C001", "adilqadri"):
                query = query.filter(Event.company_id.in_(["C001", "adilqadri"]))
            elif cid in ("mohilya", "C002"):
                query = query.filter(Event.company_id.in_(["mohilya", "C002"]))
            else:
                query = query.filter(Event.company_id == cid)
        else:
            from app.models.business_supply_chain import Company
            active_co = self.db.query(Company).first()
            if active_co:
                cname = (active_co.company_name or "").lower()
                if "adil" in cname or active_co.company_id == "C001":
                    query = query.filter(Event.company_id.in_(["C001", "adilqadri"]))
                elif "mohilya" in cname:
                    query = query.filter(Event.company_id.in_(["mohilya", "C002"]))
                elif active_co.company_id:
                    query = query.filter(Event.company_id == active_co.company_id)

        if search and search.strip():
            pattern = f"%{search.strip()}%"
            query = query.filter(
                Event.title.ilike(pattern)
                | Event.description.ilike(pattern)
                | Event.location.ilike(pattern)
            )

        if severity and severity.strip():
            query = query.filter(Event.severity == severity.strip())

        if status and status.strip():
            query = query.filter(Event.status == status.strip())

        if event_type and event_type.strip():
            query = query.filter(Event.event_type == event_type.strip())

        if source and source.strip():
            query = query.filter(Event.source == source.strip())

        events = [
            self._serialize_event(event)
            for event in query.order_by(Event.id.desc()).limit(limit).all()
        ]

        clusters = self._cluster_serialized_events(events)

        event_to_cluster: dict[int, str] = {}

        for cluster in clusters:
            for event_id in cluster["event_ids"]:
                event_to_cluster[event_id] = cluster["cluster_id"]

        for event in events:
            event["cluster_id"] = event_to_cluster.get(event["id"])

        return {
            "success": True,
            "version": self.VERSION,
            "count": len(events),
            "events": events,
            "clusters": clusters,
        }

    # ------------------------------------------------------------------
    # CLUSTERS
    # ------------------------------------------------------------------

    def clusters(self, limit: int = 100) -> dict[str, Any]:
        result = self.list_history(limit=limit)

        return {
            "success": True,
            "version": self.VERSION,
            "count": len(result["clusters"]),
            "clusters": result["clusters"],
        }

    # ------------------------------------------------------------------
    # TIMELINE
    # ------------------------------------------------------------------

    def timeline(self, event_id: int) -> dict[str, Any]:
        event = (
            self.db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if event is None:
            return {
                "success": False,
                "event_id": event_id,
                "message": "Event not found.",
            }

        current = self._serialize_event(event)

        others = [
            self._serialize_event(item)
            for item in (
                self.db.query(Event)
                .filter(Event.id != event_id)
                .order_by(Event.id.asc())
                .all()
            )
        ]

        related = [
            item
            for item in others
            if self._cluster_similarity(current, item) >= 0.72
        ]

        timeline = [*related, current]
        timeline.sort(key=lambda item: item["id"])

        return {
            "success": True,
            "version": self.VERSION,
            "event": current,
            "timeline": timeline,
        }

    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # FULL INTELLIGENCE REPLAY
    # ------------------------------------------------------------------

    def intelligence(self, event_id: int) -> dict[str, Any]:
        """
        Rebuild the complete canonical intelligence for an existing
        historical event without creating a new Event row.

        IMPORTANT:
        - Existing event ID is preserved.
        - Existing business supply-chain data is reused.
        - Business simulation remains the operational source of truth.
        - ML/GNN remains a secondary predictive signal.
        """

        event = (
            self.db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if event is None:
            return {
                "success": False,
                "event_id": event_id,
                "message": "Event not found.",
            }

        # Re-run NLP only to recover the same entity/location context
        # required by the existing business supplier matcher.
        nlp_result = nlp_engine.analyze(
            title=event.title or "",
            description=event.description or "",
        )

        pipeline = IntelligencePipeline(self.db)

        # Existing supplier-resolution logic.
        business_supplier_matches = (
            pipeline._match_business_suppliers(
                title=event.title or "",
                description=event.description or "",
                nlp_result=nlp_result,
            )
        )

        # Existing deterministic business simulation.
        business_impact = (
            pipeline._simulate_business_impact(
                matched_business_suppliers=(
                    business_supplier_matches
                ),
                event_location=event.location,
                event_severity=event.severity,
                event_type=event.event_type,
            )
        )

        # Existing canonical business aggregation.
        business_summary = (
            pipeline._aggregate_business_impact(
                business_impact
            )
        )

        # Existing prediction engine for this SAME event ID.
        #
        # This remains the business/rule-based prediction source.
        try:
            prediction = predict_event_impact(
                self.db,
                event.id,
            )
        except Exception as exc:
            prediction = {
                "success": False,
                "error": str(exc),
            }

        # ------------------------------------------------------------
        # HYBRID PREDICTION HYDRATION
        # ------------------------------------------------------------
        #
        # Historical Intelligence must expose the same hybrid
        # prediction that the live Graph Intelligence endpoint uses.
        #
        # IMPORTANT:
        # - Business simulation remains the source of truth.
        # - Hybrid/GNN is only a secondary predictive signal.
        # - Nothing from hybrid_prediction is allowed to overwrite
        #   business_supply_chain simulation facts.
        #
        hybrid_prediction_result: dict[str, Any] = {
            "success": False,
            "event_id": event.id,
            "graph_id": f"event_{event.id}",
        }

        try:
            hybrid_service = HybridPredictionService()

            hybrid_prediction_result = (
                hybrid_service.predict(
                    db=self.db,
                    event_id=event.id,
                    graph_id=f"event_{event.id}",
                )
            )

        except Exception as exc:
            hybrid_prediction_result = {
                "success": False,
                "event_id": event.id,
                "graph_id": f"event_{event.id}",
                "error": str(exc),
            }

        # ------------------------------------------------------------
        # Keep both prediction layers available.
        #
        # The unified intelligence service understands:
        #   prediction.base_prediction
        #   prediction.gnn_prediction
        #   prediction.hybrid_prediction
        #
        # Therefore the historical replay gets the same structure
        # as the normal live intelligence pipeline.
        # ------------------------------------------------------------

        if (
            isinstance(
                prediction,
                dict,
            )
            and isinstance(
                hybrid_prediction_result,
                dict,
            )
            and hybrid_prediction_result.get(
                "success"
            )
        ):
            prediction = {
                **prediction,
                "base_prediction": hybrid_prediction_result.get(
                    "base_prediction",
                    {},
                ),
                "gnn_prediction": hybrid_prediction_result.get(
                    "gnn_prediction",
                    {},
                ),
                "hybrid_prediction": hybrid_prediction_result.get(
                    "hybrid_prediction",
                    {},
                ),
                "weights": hybrid_prediction_result.get(
                    "weights",
                    {},
                ),
                "hybrid_prediction_available": True,
            }

        elif isinstance(
            prediction,
            dict,
        ):
            prediction = {
                **prediction,
                "hybrid_prediction_available": False,
                "hybrid_prediction_error": (
                    hybrid_prediction_result.get(
                        "error"
                    )
                    if isinstance(
                        hybrid_prediction_result,
                        dict,
                    )
                    else "Hybrid prediction unavailable."
                ),
            }

        raw = {
            "success": True,

            "event_id": event.id,
            "graph_id": f"event_{event.id}",

            "event": self._serialize_event(event),

            "nlp": nlp_result,

            "business_supply_chain": {
                "matched_suppliers": (
                    business_supplier_matches
                ),

                "supplier_match_count": len(
                    business_supplier_matches
                ),

                "simulation": business_impact,

                "summary": business_summary,
            },

            "prediction": prediction,
        }

        # Build the SAME canonical Unified Intelligence object
        # used by the normal News Intelligence pipeline.
        intelligence = UnifiedIntelligenceService.build(
            raw
        )

        return {
            "success": True,
            "version": self.VERSION,
            "event_id": event.id,
            "graph_id": f"event_{event.id}",

            "event": self._serialize_event(event),

            "nlp": nlp_result,

            "business_supply_chain": (
                raw["business_supply_chain"]
            ),

            "intelligence": intelligence,
        }

    # REPLAY
    # ------------------------------------------------------------------

    def replay(self, event_id: int) -> dict[str, Any]:
        event = (
            self.db.query(Event)
            .filter(Event.id == event_id)
            .first()
        )

        if event is None:
            return {
                "success": False,
                "event_id": event_id,
                "message": "Event not found.",
            }

        event_impact_graph = EventImpactGraphService(self.db).build(event_id)

        return {
            "success": True,
            "version": self.VERSION,
            "replay": {
                "event_id": event_id,
                "graph_id": f"event_{event_id}",
                "replay_type": "operational_event_replay",
                "source_of_truth": "business_supply_chain",
                "ml_override": False,
                "event": self._serialize_event(event),
                "event_impact_graph": event_impact_graph,
            },
        }

    # ------------------------------------------------------------------
    # CLUSTERING
    # ------------------------------------------------------------------

    @classmethod
    def _cluster_serialized_events(
        cls,
        events: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        clusters: list[dict[str, Any]] = []

        for event in sorted(events, key=lambda item: item["id"]):
            best_cluster = None
            best_score = 0.0

            for cluster in clusters:
                representative = cluster["representative"]

                score = cls._cluster_similarity(
                    event,
                    representative,
                )

                if score > best_score:
                    best_score = score
                    best_cluster = cluster

            if best_cluster is not None and best_score >= 0.72:
                best_cluster["event_ids"].append(event["id"])
                best_cluster["event_count"] = len(
                    best_cluster["event_ids"]
                )

            else:
                clusters.append(
                    {
                        "cluster_id": f"cluster_{len(clusters) + 1:04d}",
                        "event_ids": [event["id"]],
                        "event_count": 1,
                        "representative": event,
                    }
                )

        for cluster in clusters:
            cluster.pop("representative", None)

        return clusters

    @classmethod
    def _cluster_similarity(
        cls,
        left: dict[str, Any],
        right: dict[str, Any],
    ) -> float:

        left_type = left.get("event_type")
        right_type = right.get("event_type")

        if (
            left_type
            and right_type
            and left_type != right_type
        ):
            return 0.0

        location_score = cls._location_similarity(
            left.get("location"),
            right.get("location"),
        )

        title_score = cls._text_similarity(
            left.get("title"),
            right.get("title"),
        )

        description_score = cls._text_similarity(
            left.get("description"),
            right.get("description"),
        )

        score = (
            0.60 * title_score
            + 0.20 * description_score
            + 0.20 * location_score
        )

        if (
            location_score >= 1.0
            and title_score >= 0.55
        ):
            score += 0.08

        return min(1.0, score)

    @classmethod
    def _text_similarity(
        cls,
        left: Any,
        right: Any,
    ) -> float:

        a = cls._normalize_text(left)
        b = cls._normalize_text(right)

        if not a or not b:
            return 0.0

        raw_similarity = SequenceMatcher(
            None,
            a,
            b,
        ).ratio()

        a_tokens = set(a.split())
        b_tokens = set(b.split())

        union = a_tokens | b_tokens
        intersection = a_tokens & b_tokens

        jaccard = (
            len(intersection) / len(union)
            if union
            else 0.0
        )

        return max(
            raw_similarity,
            jaccard,
        )

    @staticmethod
    def _location_similarity(
        left: Any,
        right: Any,
    ) -> float:

        a = str(left or "").strip().lower()
        b = str(right or "").strip().lower()

        if not a or not b:
            return 0.0

        if a == b:
            return 1.0

        if len(a) >= 4 and len(b) >= 4:
            return SequenceMatcher(
                None,
                a,
                b,
            ).ratio()

        return 0.0

    @classmethod
    def _normalize_text(cls, value: Any) -> str:
        text = re.sub(
            r"[^a-z0-9\s]",
            " ",
            str(value or "").lower(),
        )

        tokens = [
            token
            for token in text.split()
            if token not in cls._STOPWORDS
        ]

        return " ".join(tokens)

    # ------------------------------------------------------------------
    # SERIALIZATION
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_event(event: Event) -> dict[str, Any]:

        def iso(value: Any) -> Any:
            if hasattr(value, "isoformat"):
                return value.isoformat()

            return value

        return {
            "id": int(event.id),
            "event_id": int(event.id),
            "title": event.title,
            "description": event.description,
            "source": event.source,
            "event_type": event.event_type,
            "location": event.location,
            "severity": event.severity,
            "status": event.status,
            "company_id": getattr(event, "company_id", None),
            "event_time": iso(
                getattr(event, "event_time", None)
            ),
            "created_at": iso(
                getattr(event, "created_at", None)
            ),
            "updated_at": iso(
                getattr(event, "updated_at", None)
            ),
            "graph_id": f"event_{event.id}",
        }

