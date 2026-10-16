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

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import html
import re
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen
import xml.etree.ElementTree as ET
import dateutil.parser

from sqlalchemy.orm import Session

from app.models.event import Event
from app.services.nlp_engine import nlp_engine


def _get_ws_manager():
    try:
        from app.api.routes.websocket import manager
        return manager
    except Exception:
        return None


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
        user_id: int | None = None,
    ) -> None:

        self.db = db
        self.user_id = user_id

    # =========================================================
    # DATE PARSING & FRESHNESS
    # =========================================================

    @staticmethod
    def parse_article_date(value: str | None) -> tuple[datetime | None, str]:
        """
        Parse RFC 2822 / ISO 8601 publication date string into a timezone-aware UTC datetime.
        Returns (parsed_datetime, iso_formatted_string).
        """
        if not value:
            return None, ""
        cleaned = str(value).strip()
        dt: datetime | None = None
        # 1. Try RFC 2822 standard (used in Google News RSS pubDate)
        try:
            dt = parsedate_to_datetime(cleaned)
        except Exception:
            pass
        # 2. Try ISO 8601 (used in Atom feeds)
        if dt is None:
            try:
                dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
            except Exception:
                pass
        # 3. Try dateutil parser
        if dt is None:
            try:
                dt = dateutil.parser.parse(cleaned)
            except Exception:
                pass

        if dt is not None:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                dt = dt.astimezone(timezone.utc)
            return dt, dt.isoformat()

        return None, cleaned

    # =========================================================
    # BUSINESS SCOPING & DYNAMIC RSS GENERATION
    # =========================================================

    def get_business_context(self) -> dict[str, Any]:
        """
        Extract active company, suppliers, and locations for the logged-in business.
        Strictly prevents pulling cross-tenant data.
        """
        from app.models.business_supply_chain import (
            Company,
            BusinessSupplier,
            Component,
        )

        q_comp = self.db.query(Company)
        q_sup = self.db.query(BusinessSupplier)
        q_part = self.db.query(Component)

        if self.user_id is not None:
            q_comp = q_comp.filter(Company.user_id == self.user_id)
            q_sup = q_sup.filter(BusinessSupplier.user_id == self.user_id)
            q_part = q_part.filter(Component.user_id == self.user_id)
            company = q_comp.first()
        else:
            company = q_comp.filter(Company.user_id.isnot(None)).order_by(Company.id.desc()).first()
            if company and company.user_id is not None:
                q_sup = q_sup.filter(BusinessSupplier.user_id == company.user_id)
                q_part = q_part.filter(Component.user_id == company.user_id)
            else:
                q_sup = q_sup.filter(BusinessSupplier.id == -1)
                q_part = q_part.filter(Component.id == -1)

        suppliers = q_sup.all()
        components = q_part.all()

        cities = list({s.city.strip() for s in suppliers if s.city and s.city.strip()})
        supplier_names = [s.supplier_name.strip() for s in suppliers if s.supplier_name]
        component_names = [c.component_name.strip() for c in components if c.component_name]

        return {
            "company_name": company.company_name if company else "Active Business",
            "industry": company.industry if company else "Supply Chain",
            "cities": cities,
            "supplier_names": supplier_names,
            "components": component_names,
            "user_id": company.user_id if company else self.user_id,
        }

    def build_business_rss_url(self, context: dict[str, Any] | None = None) -> str:
        """
        Dynamically build a Google News RSS query targeted specifically
        to the active business, its supplier cities, and industry, strictly within the last 3 days.
        """
        from urllib.parse import quote_plus

        if not context:
            context = self.get_business_context()

        cities = context.get("cities", [])
        industry = context.get("industry", "")
        company_name = context.get("company_name", "")

        query_parts: list[str] = []

        # 1. Target supplier core cities (extract clean names without commas/road tags)
        clean_cities: list[str] = []
        for c in cities:
            parts = [p.strip() for p in re.split(r"[,/]", c) if p.strip()]
            for p in parts:
                p_clean = re.sub(r"\b(GIDC|Road|Belt|Cluster|Hub|West|East|North|South)\b", "", p, flags=re.IGNORECASE).strip()
                if len(p_clean) >= 4 and p_clean.lower() not in [x.lower() for x in clean_cities]:
                    clean_cities.append(p_clean)

        # 2. Industry-specific disruption hubs
        ind_lower = industry.lower()
        company_lower = company_name.lower()

        if "perfume" in ind_lower or "attar" in ind_lower or "adil" in company_lower:
            query_parts.append("(Kannauj OR Firozabad OR Nhava Sheva OR Mumbai)")
            query_parts.append("(Attar OR Fragrance OR Sandalwood OR Essential Oil OR Glass Bottle)")
        elif "textile" in ind_lower or "garment" in ind_lower or "fabric" in ind_lower or "mohilya" in company_lower:
            query_parts.append("(Surat OR Pandesara OR Sachin OR Ring Road OR Puna)")
            query_parts.append("(Textile OR Fabric OR Dyeing OR Yarn OR Garment OR Cloth)")
        elif "apparel" in ind_lower or "bonkers" in company_lower or "streetstyle" in company_lower:
            query_parts.append("(Ludhiana OR Bhiwandi OR Tiruppur OR Surat)")
            query_parts.append("(Cotton OR Textile OR Fabric OR Garment OR Apparel OR Trims)")
        elif clean_cities:
            query_parts.append("(" + " OR ".join(clean_cities[:4]) + ")")
            if industry and len(industry) > 3:
                query_parts.append(f"({industry})")

        disruption_terms = "(fire OR strike OR flood OR shutdown OR delay OR blast OR waterlogging OR congestion OR accident)"

        if len(query_parts) >= 2:
            combined_query = f"{query_parts[0]} AND {query_parts[1]} AND {disruption_terms} when:3d"
        elif query_parts:
            combined_query = f"{query_parts[0]} AND {disruption_terms} when:3d"
        else:
            combined_query = f"supply chain disruption AND {disruption_terms} when:3d"

        return (
            "https://news.google.com/rss/search"
            f"?q={quote_plus(combined_query)}"
            "&hl=en-IN&gl=IN&ceid=IN:en"
        )

    def evaluate_business_relevance(
        self,
        title: str,
        description: str,
        context: dict[str, Any] | None = None,
        pub_dt: datetime | None = None,
    ) -> dict[str, Any]:
        """
        Determine if this news article actually affects the active business.
        High-accuracy validation:
        1. Freshness check (<= 72 hours max age).
        2. Operational disruption signal check.
        3. Strict cross-industry blacklist filter.
        4. Precise supplier name or supplier hub location matching.
        """
        now_utc = datetime.now(timezone.utc)
        if pub_dt is not None:
            age_hours = (now_utc - pub_dt).total_seconds() / 3600.0
            if age_hours > 72.0:
                return {
                    "is_relevant": False,
                    "relevance_score": 0,
                    "matched_cities": [],
                    "matched_suppliers": [],
                    "explanation": f"Filtered out: Published {age_hours/24.0:.1f} days ago (exceeds 72h freshness limit)",
                }

        if not context:
            context = self.get_business_context()

        company_name = context.get("company_name", "").lower()
        industry = context.get("industry", "").lower()
        text = f"{title} {description}".lower()

        # 1. Operational Disruption Signal Check
        disruption_signals = [
            "fire", "blaze", "burn", "explosion", "blast", "strike", "protest",
            "halt", "shutdown", "closure", "closed", "blocked", "blockage",
            "waterlogging", "waterlogged", "flood", "flooding", "heavy rain", "monsoon",
            "cyclone", "storm", "accident", "crash", "collision", "damage",
            "delay", "delayed", "congestion", "gridlock", "power grid", "power failure",
            "power cut", "blackout", "contamination", "spill", "leak", "shortage",
            "stoppage", "standoff", "disrupted", "disruption", "derailment", "embargo"
        ]
        if not any(k in text for k in disruption_signals):
            return {
                "is_relevant": False,
                "relevance_score": 0,
                "matched_cities": [],
                "matched_suppliers": [],
                "explanation": "Filtered out: Not an operational disruption incident",
            }

        # 2. Strict Cross-Industry Blacklist Filter
        is_garment = "mohilya" in company_name or "textile" in industry or "garment" in industry or "apparel" in industry or "bonkers" in company_name
        is_perfume = "adil" in company_name or "perfume" in industry or "attar" in industry or "fragrance" in industry

        if is_garment:
            garment_blacklist = [
                "electronics", "semiconductor", "chipmaking", "wafer fab", "drdo",
                "missile", "anti-tank", "defense unit", "military", "smartphone",
                "laptop", "telecom", "ai department", "bank robbery", "crypto",
                "attar", "perfume", "sandalwood", "kannauj", "ittar", "fragrance",
                "hospital", "cinema", "bollywood"
            ]
            if any(k in text for k in garment_blacklist):
                return {
                    "is_relevant": False,
                    "relevance_score": 0,
                    "matched_cities": [],
                    "matched_suppliers": [],
                    "explanation": "Filtered out: Irrelevant to garment/textile supply chain",
                }

        if is_perfume:
            perfume_blacklist = [
                "electronics", "semiconductor", "wafer fab", "missile", "drdo",
                "defense", "garment", "stitching", "embroidery", "saree", "kurti",
                "zari", "lace", "denim", "textile market", "fabric dyeing", "yarn",
                "banking", "crypto", "cinema"
            ]
            if any(k in text for k in perfume_blacklist):
                return {
                    "is_relevant": False,
                    "relevance_score": 0,
                    "matched_cities": [],
                    "matched_suppliers": [],
                    "explanation": "Filtered out: Irrelevant to fragrance/attar supply chain",
                }

        # 3. Match Registered Suppliers (Strict multi-token / distinctive name match)
        matched_suppliers: list[str] = []
        for s in context.get("supplier_names", []):
            clean_s = re.sub(
                r"\b(Ltd|Limited|Pvt|Private|Traders|Trader|Units|Unit|Press|Mills|Mill|Co|Company|India|Category-level|Imported)\b",
                "",
                s,
                flags=re.IGNORECASE,
            ).strip().lower()
            tokens = [t for t in re.split(r"[^\w]+", clean_s) if len(t) >= 4]
            if len(tokens) >= 2:
                if " ".join(tokens) in text or sum(1 for t in tokens if t in text) >= 2:
                    matched_suppliers.append(s)
            elif len(tokens) == 1:
                t = tokens[0]
                if t in text and t not in {"india", "press", "market", "traders", "mumbai", "delhi", "surat"}:
                    matched_suppliers.append(s)

        # 4. Match Registered Supplier Hub Locations
        matched_cities: list[str] = []
        for c in context.get("cities", []):
            parts = [p.strip() for p in re.split(r"[,/]", c) if p.strip()]
            for p in parts:
                p_clean = re.sub(r"\b(GIDC|Road|Belt|Cluster|Hub)\b", "", p, flags=re.IGNORECASE).strip().lower()
                if len(p_clean) >= 4 and p_clean in text and p_clean not in [x.lower() for x in matched_cities]:
                    matched_cities.append(p.strip())

        # 5. Industry Keywords Verification
        matched_industry: list[str] = []
        if is_garment:
            garment_terms = ["textile", "fabric", "cloth", "garment", "apparel", "cotton", "yarn", "dyeing", "printing", "embroidery", "lace", "trims", "loom", "weavers", "powerloom", "rayon", "zari"]
            for term in garment_terms:
                if term in text:
                    matched_industry.append(term)
        elif is_perfume:
            perfume_terms = ["attar", "perfume", "fragrance", "sandalwood", "essential oil", "aroma", "oud", "agarwood", "floral extract", "glass bottle", "nhava sheva", "jnpt", "carrier oil"]
            for term in perfume_terms:
                if term in text:
                    matched_industry.append(term)
        else:
            ind_clean = industry.lower()
            if len(ind_clean) >= 4 and ind_clean in text:
                matched_industry.append(ind_clean)

        # To be relevant:
        # A) Explicit supplier match
        # B) Supplier Hub Location Match AND Industry Match
        # C) Specific Hub Industrial Zone Disruption directly affecting company operations
        is_relevant = False
        score = 0
        explanation = ""

        if matched_suppliers:
            is_relevant = True
            score = 95
            explanation = f"Affects your supplier: {matched_suppliers[0]}"
        elif matched_cities and matched_industry:
            is_relevant = True
            score = 85
            explanation = f"Affects supplier hub in {', '.join(matched_cities[:2])} ({matched_industry[0].title()})"
        elif is_garment and any(hub in text for hub in ["pandesara", "sachin gidc", "ring road textile", "salabatpura", "puna patiya"]) and matched_industry:
            is_relevant = True
            score = 80
            explanation = f"Industrial disruption in Surat textile hub affecting material inbound"
        elif is_perfume and any(hub in text for hub in ["kannauj", "firozabad glass", "nhava sheva port"]) and matched_industry:
            is_relevant = True
            score = 80
            explanation = f"Logistics disruption affecting {matched_industry[0]} supply lines"
        else:
            is_relevant = False
            explanation = "Filtered out: Not directly relevant to active company supply chain"

        return {
            "is_relevant": is_relevant,
            "relevance_score": score,
            "matched_cities": matched_cities,
            "matched_suppliers": matched_suppliers,
            "explanation": explanation,
        }

    def enrich_business_description(
        self,
        title: str,
        raw_description: str,
        context: dict[str, Any],
        relevance: dict[str, Any],
    ) -> str:
        """
        Transform raw, noisy RSS HTML into a clean, simple-English
        business disruption explanation.
        """
        clean_desc = self._clean_text(raw_description)
        # Strip newspaper names like " - The Times of India", " - Reuters"
        clean_title = re.sub(r"\s+-\s+[^-]+$", "", title).strip()

        matched_cities = relevance.get("matched_cities", [])
        matched_sups = relevance.get("matched_suppliers", [])
        co_name = context.get("company_name", "Your Business")

        target_hub = matched_sups[0] if matched_sups else (f"registered suppliers in {matched_cities[0]}" if matched_cities else "inbound supply lines")

        structured = (
            f"WHAT HAPPENED:\n"
            f"{clean_title}. {clean_desc[:220].strip()}.\n\n"
            f"IMPACT ON {co_name.upper()}:\n"
            f"Disruption directly affects {target_hub}. Incoming factory materials and order shipments will experience delays.\n\n"
            f"EXPECTED DELAY:\n"
            f"Estimated delay: 3 to 4 business days.\n\n"
            f"RECOMMENDED ACTION:\n"
            f"Contact {target_hub} immediately to verify current warehouse dispatch status. Switch manufacturing to backup buffer stock."
        )
        return structured

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

        now_utc = datetime.now(timezone.utc)
        max_age_hours = 72.0  # Strict 3-day (72h) freshness cutoff

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

            # Strict publication date verification
            pub_dt, iso_pub = self.parse_article_date(published)
            if pub_dt is not None:
                age_hours = (now_utc - pub_dt).total_seconds() / 3600.0
                if age_hours > max_age_hours or age_hours < -2.0:
                    # Skip old news > 3 days old or invalid future dates
                    continue
            else:
                # Require verified publication date for high accuracy
                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "url": link,
                    "published_at": iso_pub,
                    "published_dt": pub_dt,
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

            pub_dt, iso_pub = self.parse_article_date(published)
            if pub_dt is not None:
                age_hours = (now_utc - pub_dt).total_seconds() / 3600.0
                if age_hours > max_age_hours or age_hours < -2.0:
                    continue
            else:
                continue

            articles.append(
                {
                    "title": title,
                    "description": description,
                    "url": link,
                    "published_at": iso_pub,
                    "published_dt": pub_dt,
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
            self.db,
            user_id=self.user_id,
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

        manager = _get_ws_manager()
        if not manager:
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

        # -----------------------------------------------------
        # 1. Resolve Active Business Context & Build Scoped RSS
        # -----------------------------------------------------
        context = self.get_business_context()

        if not feed_url:
            feed_url = self.build_business_rss_url(context)

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
            self.db,
            user_id=self.user_id,
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

            raw_title = article.get(
                "title",
                "",
            )

            raw_description = article.get(
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

            title = self._clean_text(
                raw_title
            )

            if not title:
                continue

            # -------------------------------------------------
            # 2. Evaluate Business Relevance & Plain Translation
            # -------------------------------------------------
            pub_dt = article.get("published_dt")
            relevance = self.evaluate_business_relevance(
                title=title,
                description=raw_description,
                context=context,
                pub_dt=pub_dt,
            )

            # Strictly skip if not relevant to the active business
            if not relevance.get("is_relevant", False):
                skipped.append(
                    {
                        "title": title,
                        "reason": relevance.get("explanation", "not_business_relevant"),
                        "relevance_explanation": relevance.get("explanation"),
                        "is_business_relevant": False,
                    }
                )
                continue

            # Produce high-quality, structured business dossier
            rich_description = self.enrich_business_description(
                title=title,
                raw_description=raw_description,
                context=context,
                relevance=relevance,
            )

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
                        "relevance_explanation": relevance.get("explanation"),
                        "is_business_relevant": relevance.get("is_relevant"),
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
                        description=rich_description,
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
                        description=rich_description,
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
                        "description": rich_description,
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
                        "relevance_explanation": relevance.get("explanation"),
                        "is_business_relevant": relevance.get("is_relevant"),
                        "relevance_score": relevance.get("relevance_score"),
                        "matched_cities": relevance.get("matched_cities", []),
                        "matched_suppliers": relevance.get("matched_suppliers", []),
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