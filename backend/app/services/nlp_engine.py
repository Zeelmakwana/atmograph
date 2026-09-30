"""
AtmoGraph NLP Engine

Converts news text into structured supply-chain information.

Flow:

News
  ↓
NLP
  ↓
Event Type
Severity
Location
Entities
"""

from __future__ import annotations

import re
from typing import Any

import spacy


class AtmoGraphNLPEngine:
    """Extract supply-chain intelligence from news text."""

    # =========================================================
    # EVENT PATTERNS
    # =========================================================

    EVENT_PATTERNS = {
        "port_strike": [
            r"port\s+strike",
            r"strike\s+at\s+(?:the\s+)?port",
            r"workers?\s+strike.*(?:port|harbor|harbour)",
            r"\bstrike\b.*\b(?:port|harbor|harbour)\b",
            r"\b(?:port|harbor|harbour)\b.*\bstrike\b",
            r"\b(?:hamburg|rotterdam|singapore|shanghai|antwerp)\s+strike\b",
        ],

        "port_closure": [
            r"port\s+(?:closure|closed|shutdown)",
            r"port\s+has\s+closed",
            r"port\s+operations\s+(?:halted|suspended)",
        ],

        "weather_disruption": [
            r"\bstorm\b",
            r"\bhurricane\b",
            r"\btyphoon\b",
            r"\bflood\b",
            r"extreme\s+weather",
        ],

        "transport_disruption": [
            r"transport(?:ation)?\s+disruption",
            r"shipping\s+disruption",
            r"rail\s+disruption",
            r"truck(?:ing)?\s+disruption",
        ],

        "factory_shutdown": [
            r"factory\s+(?:shutdown|shut\s+down|closed)",
            r"plant\s+(?:shutdown|shut\s+down|closed)",
            r"production\s+(?:halted|stopped|suspended)",
        ],

        "container_shortage": [
            r"container\s+shortage",
            r"shortage\s+of\s+containers",
            r"lack\s+of\s+containers",
        ],

        "fuel_price_surge": [
            r"fuel\s+prices?\s+(?:surge|spike|rise|increase)",
            r"oil\s+prices?\s+(?:surge|spike|rise|increase)",
            r"fuel\s+price\s+(?:surge|spike)",
        ],

        "supply_chain_disruption": [
            r"supply\s+chain\s+(?:disruption|disruptions)",
            r"supply\s+shortage",
            r"supplies?\s+(?:delayed|disrupted)",
        ],
    }

    # =========================================================
    # SEVERITY
    # =========================================================

    SEVERITY_TERMS = {
        "critical": [
            "critical",
            "severe",
            "massive",
            "major crisis",
        ],

        "high": [
            "major",
            "significant",
            "serious",
            "large-scale",
        ],

        "medium": [
            "moderate",
            "notable",
        ],

        "low": [
            "minor",
            "limited",
            "small",
        ],
    }

    # =========================================================
    # KNOWN SUPPLY-CHAIN LOCATIONS
    # =========================================================

    KNOWN_LOCATIONS = {
        "hamburg",
        "rotterdam",
        "singapore",
        "shanghai",
        "shenzhen",
        "taipei",
        "kaohsiung",
        "busan",
        "dubai",
        "antwerp",
        "felixstowe",
        "los angeles",
        "long beach",
        "new york",
        "savannah",
        "houston",
        "suez",
        "suez canal",
        "panama",
        "panama canal",
        "north sea",
        "south china sea",
        "english channel",
        "gulf of mexico",
        "red sea",
        "arabian sea",
    }

    # =========================================================
    # LOCATION NORMALIZATION
    # =========================================================

    LOCATION_ALIASES = {
        "port of rotterdam": "Rotterdam",
        "rotterdam port": "Rotterdam",

        "port of hamburg": "Hamburg",
        "hamburg port": "Hamburg",

        "port of singapore": "Singapore",
        "singapore port": "Singapore",

        "port of shanghai": "Shanghai",
        "shanghai port": "Shanghai",

        "port of antwerp": "Antwerp",
        "antwerp port": "Antwerp",

        "suez": "Suez",
        "suez canal": "Suez Canal",

        "panama": "Panama",
        "panama canal": "Panama Canal",

        "north sea": "North Sea",
        "south china sea": "South China Sea",

        "red sea": "Red Sea",
        "arabian sea": "Arabian Sea",

        "english channel": "English Channel",

        "gulf of mexico": "Gulf of Mexico",
    }

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        model_name: str = "en_core_web_sm",
    ) -> None:

        self.model_name = model_name

        try:
            self.nlp = spacy.load(model_name)
            self.model_loaded = True

        except OSError:
            # Fallback to blank English pipeline.
            self.nlp = spacy.blank("en")
            self.model_loaded = False

    # =========================================================
    # BASIC HELPERS
    # =========================================================

    @staticmethod
    def _clean(value: str) -> str:
        """Normalize whitespace."""

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @classmethod
    def _canonical_location(
        cls,
        value: str,
    ) -> str:
        """Normalize a location to its canonical name."""

        value = re.sub(
            r"\s+",
            " ",
            value,
        ).strip(" .,;:-")

        return cls.LOCATION_ALIASES.get(
            value.lower(),
            value,
        )

    @staticmethod
    def _overlaps(
        start_a: int,
        end_a: int,
        start_b: int,
        end_b: int,
    ) -> bool:
        """Return True when two character spans overlap."""

        return (
            start_a < end_b
            and end_a > start_b
        )

    # =========================================================
    # DOMAIN LOCATION DETECTION
    # =========================================================

    def _domain_location_candidates(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Detect supply-chain locations using domain knowledge.

        Important:
        We intentionally do NOT use a generic
        "words before port" regex because it can incorrectly
        capture phrases such as:

            "strike at Rotterdam port"

        as:

            "strike at Rotterdam"

        Instead we search for known location names directly.
        """

        candidates: list[dict[str, Any]] = []

        # -----------------------------------------------------
        # Port of Rotterdam
        # Port of Hamburg
        # Port of Singapore
        # -----------------------------------------------------

        port_of_pattern = re.compile(
            r"\bport\s+of\s+"
            r"([A-Za-z][A-Za-z-]*(?:\s+[A-Za-z][A-Za-z-]*){0,2})"
            r"\b",
            re.IGNORECASE,
        )

        for match in port_of_pattern.finditer(text):

            raw = self._clean(
                match.group(1)
            )

            canonical = self._canonical_location(
                raw
            )

            # Only accept if the extracted location is
            # actually a known location.
            if canonical.lower() not in {
                value.lower()
                for value in self.LOCATION_ALIASES.values()
            } and raw.lower() not in self.KNOWN_LOCATIONS:

                continue

            candidates.append(
                {
                    "text": canonical,
                    "start": match.start(1),
                    "end": match.end(1),
                    "reason": "supply_chain_port_context",
                }
            )

        # -----------------------------------------------------
        # Rotterdam port
        # Hamburg port
        #
        # IMPORTANT:
        # Only match known location immediately before "port".
        # -----------------------------------------------------

        lower_text = text.lower()

        for known_location in sorted(
            self.KNOWN_LOCATIONS,
            key=len,
            reverse=True,
        ):

            pattern = re.compile(
                rf"(?<![A-Za-z])"
                rf"{re.escape(known_location)}"
                rf"(?=\s+port\b)",
                re.IGNORECASE,
            )

            for match in pattern.finditer(
                lower_text
            ):

                raw = text[
                    match.start():
                    match.end()
                ]

                candidates.append(
                    {
                        "text": self._canonical_location(
                            raw
                        ),
                        "start": match.start(),
                        "end": match.end(),
                        "reason": "supply_chain_port_context",
                    }
                )

        # -----------------------------------------------------
        # Known supply-chain locations anywhere in text.
        # -----------------------------------------------------

        for known_location in sorted(
            self.KNOWN_LOCATIONS,
            key=len,
            reverse=True,
        ):

            pattern = re.compile(
                rf"(?<![A-Za-z])"
                rf"{re.escape(known_location)}"
                rf"(?![A-Za-z])",
                re.IGNORECASE,
            )

            for match in pattern.finditer(
                lower_text
            ):

                raw = text[
                    match.start():
                    match.end()
                ]

                candidates.append(
                    {
                        "text": self._canonical_location(
                            raw
                        ),
                        "start": match.start(),
                        "end": match.end(),
                        "reason": "known_supply_chain_location",
                    }
                )

        # -----------------------------------------------------
        # Remove duplicate candidates.
        # -----------------------------------------------------

        unique: dict[
            tuple[int, int, str],
            dict[str, Any],
        ] = {}

        priority = {
            "supply_chain_port_context": 0,
            "known_supply_chain_location": 1,
        }

        for candidate in candidates:

            key = (
                candidate["start"],
                candidate["end"],
                candidate["text"].lower(),
            )

            existing = unique.get(key)

            if existing is None:

                unique[key] = candidate

            elif (
                priority.get(
                    candidate["reason"],
                    99,
                )
                < priority.get(
                    existing["reason"],
                    99,
                )
            ):

                unique[key] = candidate

        return list(
            unique.values()
        )

    # =========================================================
    # EVENT TYPE
    # =========================================================

    def extract_event_type(
        self,
        text: str,
    ) -> str:
        """Detect the most relevant supply-chain event type."""

        text_lower = text.lower()

        for event_type, patterns in (
            self.EVENT_PATTERNS.items()
        ):

            for pattern in patterns:

                if re.search(
                    pattern,
                    text_lower,
                ):
                    return event_type

        return "supply_chain_disruption"

    # =========================================================
    # SEVERITY
    # =========================================================

    def extract_severity(
        self,
        text: str,
    ) -> str:
        """Detect severity from the news text."""

        text_lower = text.lower()

        for severity, terms in (
            self.SEVERITY_TERMS.items()
        ):

            for term in terms:

                pattern = (
                    r"\b"
                    + re.escape(term)
                    + r"\b"
                )

                if re.search(
                    pattern,
                    text_lower,
                ):
                    return severity

        return "medium"

    # =========================================================
    # ENTITY EXTRACTION
    # =========================================================

    def extract_entities(
        self,
        text: str,
    ) -> list[dict[str, Any]]:
        """
        Extract named entities using spaCy.

        Then apply AtmoGraph-specific corrections.

        Example:

            spaCy:
                Rotterdam -> PERSON

            AtmoGraph:
                Rotterdam -> GPE
                domain_label -> Location
        """

        if not text.strip():
            return []

        doc = self.nlp(text)

        entities: list[
            dict[str, Any]
        ] = []

        # -----------------------------------------------------
        # Base spaCy entities
        # -----------------------------------------------------

        for entity in doc.ents:

            clean_text = self._clean(
                entity.text
            )

            if not clean_text:
                continue

            entities.append(
                {
                    "text": clean_text,
                    "label": entity.label_,
                    "start": entity.start_char,
                    "end": entity.end_char,
                }
            )

        # -----------------------------------------------------
        # Domain location correction
        # -----------------------------------------------------

        domain_locations = (
            self._domain_location_candidates(
                text
            )
        )

        for candidate in domain_locations:

            location = candidate["text"]
            start = candidate["start"]
            end = candidate["end"]
            reason = candidate["reason"]

            # -------------------------------------------------
            # Exact spaCy entity span exists.
            # Correct its label.
            # -------------------------------------------------

            exact_entity = next(
                (
                    entity
                    for entity in entities
                    if (
                        entity["start"] == start
                        and entity["end"] == end
                    )
                ),
                None,
            )

            if exact_entity is not None:

                original_label = (
                    exact_entity["label"]
                )

                exact_entity["label"] = "GPE"

                exact_entity[
                    "domain_label"
                ] = "Location"

                exact_entity[
                    "domain_reason"
                ] = reason

                exact_entity[
                    "original_ner_label"
                ] = original_label

                exact_entity[
                    "text"
                ] = location

                continue

            # -------------------------------------------------
            # If spaCy has an overlapping entity,
            # don't destroy an organization/product entity.
            # -------------------------------------------------

            overlapping_entity = next(
                (
                    entity
                    for entity in entities
                    if self._overlaps(
                        entity["start"],
                        entity["end"],
                        start,
                        end,
                    )
                ),
                None,
            )

            if overlapping_entity is not None:

                continue

            # -------------------------------------------------
            # Add domain location explicitly.
            # -------------------------------------------------

            entities.append(
                {
                    "text": location,
                    "label": "GPE",
                    "start": start,
                    "end": end,
                    "domain_label": "Location",
                    "domain_reason": reason,
                }
            )

        # -----------------------------------------------------
        # Mark normal spaCy geographic entities.
        # -----------------------------------------------------

        for entity in entities:

            if entity["label"] in {
                "GPE",
                "LOC",
                "FAC",
            }:

                entity.setdefault(
                    "domain_label",
                    "Location",
                )

        # -----------------------------------------------------
        # Sort by text position.
        # -----------------------------------------------------

        entities.sort(
            key=lambda entity: (
                entity["start"],
                entity["end"],
            )
        )

        # -----------------------------------------------------
        # Deduplicate.
        # -----------------------------------------------------

        deduplicated: list[
            dict[str, Any]
        ] = []

        seen: set[
            tuple[int, int, str]
        ] = set()

        for entity in entities:

            key = (
                entity["start"],
                entity["end"],
                entity["text"].lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            deduplicated.append(
                entity
            )

        return deduplicated

    # =========================================================
    # LOCATION EXTRACTION
    # =========================================================

    def extract_locations(
        self,
        text: str,
        entities: list[dict[str, Any]],
    ) -> list[str]:
        """
        Extract normalized supply-chain locations.

        Domain locations are prioritized over generic NER.
        """

        locations: list[str] = []

        # -----------------------------------------------------
        # Domain-corrected locations
        # -----------------------------------------------------

        for entity in entities:

            if entity.get(
                "domain_label"
            ) == "Location":

                locations.append(
                    entity["text"]
                )

        # -----------------------------------------------------
        # Standard spaCy locations
        # -----------------------------------------------------

        for entity in entities:

            if entity["label"] in {
                "GPE",
                "LOC",
                "FAC",
            }:

                locations.append(
                    entity["text"]
                )

        # -----------------------------------------------------
        # Direct domain detection
        # -----------------------------------------------------

        for candidate in (
            self._domain_location_candidates(
                text
            )
        ):

            locations.append(
                candidate["text"]
            )

        # -----------------------------------------------------
        # Deduplicate while preserving order.
        # -----------------------------------------------------

        unique_locations: list[str] = []

        seen: set[str] = set()

        for location in locations:

            normalized = (
                self._canonical_location(
                    location
                )
            )

            key = normalized.lower()

            if (
                normalized
                and key not in seen
            ):

                seen.add(key)

                unique_locations.append(
                    normalized
                )

        return unique_locations

    # =========================================================
    # FULL NEWS ANALYSIS
    # =========================================================

    def analyze(
        self,
        title: str,
        description: str = "",
    ) -> dict[str, Any]:
        """Analyze a news article."""

        title = self._clean(
            title
        )

        description = self._clean(
            description
        )

        full_text = self._clean(
            f"{title}. {description}"
        )

        entities = self.extract_entities(
            full_text
        )

        locations = self.extract_locations(
            full_text,
            entities,
        )

        event_type = self.extract_event_type(
            full_text
        )

        severity = self.extract_severity(
            full_text
        )

        return {
            "title": title,
            "description": description,
            "event_type": event_type,
            "severity": severity,
            "locations": locations,
            "entities": entities,
            "nlp_model": self.model_name,
            "model_loaded": self.model_loaded,
        }


# =============================================================
# GLOBAL ENGINE INSTANCE
# =============================================================

nlp_engine = AtmoGraphNLPEngine()