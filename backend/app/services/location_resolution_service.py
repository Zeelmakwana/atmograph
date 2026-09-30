from __future__ import annotations

import re
from typing import Any


class LocationResolutionService:
    """
    Structured location resolution for AtmoGraph.

    Converts free-text / NLP locations into a structured form:

        raw
        normalized
        location_type
        city
        country
        confidence
        match_reasons

    Important rules:

    1. Never invent a city.
    2. Never invent a country.
    3. Prefer city + country over country only.
    4. Recognize common port expressions.
    5. Match against known supplier locations when possible.
    6. Keep unknown locations as unknown.
    """

    COUNTRY_ALIASES: dict[str, str] = {
        "germany": "Germany",
        "deutschland": "Germany",

        "france": "France",

        "taiwan": "Taiwan",
        "republic of china": "Taiwan",

        "india": "India",
        "bharat": "India",

        "united states": "United States",
        "usa": "United States",
        "us": "United States",

        "united kingdom": "United Kingdom",
        "uk": "United Kingdom",

        "netherlands": "Netherlands",
        "holland": "Netherlands",

        "china": "China",
        "prc": "China",

        "japan": "Japan",

        "south korea": "South Korea",
        "korea": "South Korea",

        "singapore": "Singapore",
    }

    CITY_COUNTRY_MAP: dict[str, str] = {
        "hamburg": "Germany",
        "berlin": "Germany",
        "munich": "Germany",
        "frankfurt": "Germany",

        "rotterdam": "Netherlands",
        "amsterdam": "Netherlands",

        "lyon": "France",
        "paris": "France",
        "marseille": "France",

        "hsinchu": "Taiwan",
        "taipei": "Taiwan",
        "kaohsiung": "Taiwan",

        "pune": "India",
        "mumbai": "India",
        "delhi": "India",
        "new delhi": "India",
        "chennai": "India",
        "bengaluru": "India",
        "bangalore": "India",
        "ahmedabad": "India",

        "singapore": "Singapore",

        "tokyo": "Japan",
        "osaka": "Japan",

        "shanghai": "China",
        "shenzhen": "China",
        "beijing": "China",
    }

    PORT_NAMES: set[str] = {
        "hamburg",
        "rotterdam",
        "marseille",
        "kaohsiung",
        "singapore",
        "shanghai",
        "shenzhen",
        "long beach",
        "los angeles",
        "busan",
    }

    @staticmethod
    def normalize(value: str | None) -> str:
        if not value:
            return ""

        value = str(value).lower().strip()

        value = re.sub(
            r"[^a-z0-9\s]",
            " ",
            value,
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @classmethod
    def _clean_location_text(
        cls,
        value: str | None,
    ) -> str:
        """
        Remove common geographic prefixes/suffixes while
        preserving the actual location.
        """

        normalized = cls.normalize(value)

        if not normalized:
            return ""

        prefixes = (
            "port of ",
            "port ",
            "city of ",
        )

        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[
                    len(prefix):
                ].strip()

        suffixes = (
            " port",
            " city",
            " facility",
            " terminal",
        )

        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[
                    : -len(suffix)
                ].strip()

        return normalized

    @classmethod
    def resolve(
        cls,
        raw_location: str | None,
        known_city: str | None = None,
        known_country: str | None = None,
    ) -> dict[str, Any]:
        """
        Resolve one location.

        known_city / known_country are optional contextual
        values from the business entity being matched.
        """

        raw = str(
            raw_location or ""
        ).strip()

        normalized = cls._clean_location_text(
            raw
        )

        result: dict[str, Any] = {
            "raw": raw or None,
            "normalized": normalized or None,
            "location_type": "unknown",
            "city": None,
            "country": None,
            "confidence": 0.0,
            "match_reasons": [],
        }

        if not normalized:
            return result

        # --------------------------------------------------
        # Exact known city
        # --------------------------------------------------

        if normalized in cls.CITY_COUNTRY_MAP:
            country = cls.CITY_COUNTRY_MAP[
                normalized
            ]

            result["city"] = cls._display_city(
                normalized
            )

            result["country"] = country

            if normalized in cls.PORT_NAMES:
                result["location_type"] = "port"
                result["match_reasons"].append(
                    "known_port_city"
                )
            else:
                result["location_type"] = "city"
                result["match_reasons"].append(
                    "known_city"
                )

            result["confidence"] = 1.0

            return result

        # --------------------------------------------------
        # Exact country
        # --------------------------------------------------

        if normalized in cls.COUNTRY_ALIASES:
            result["country"] = (
                cls.COUNTRY_ALIASES[
                    normalized
                ]
            )

            result["location_type"] = "country"

            result["match_reasons"].append(
                "known_country"
            )

            result["confidence"] = 0.95

            return result

        # --------------------------------------------------
        # "city, country"
        # --------------------------------------------------

        parts = [
            part.strip()
            for part in normalized.split(",")
            if part.strip()
        ]

        if len(parts) >= 2:
            city_candidate = parts[0]
            country_candidate = parts[-1]

            country = cls.COUNTRY_ALIASES.get(
                country_candidate
            )

            if country:
                result["city"] = cls._display_city(
                    city_candidate
                )

                result["country"] = country

                if city_candidate in cls.PORT_NAMES:
                    result["location_type"] = "port"
                else:
                    result["location_type"] = "city"

                result["match_reasons"].append(
                    "city_country_explicit"
                )

                result["confidence"] = 1.0

                return result

        # --------------------------------------------------
        # Unknown free-text location.
        #
        # IMPORTANT:
        # Do not guess city/country.
        # --------------------------------------------------

        result["location_type"] = "unknown"

        result["match_reasons"].append(
            "location_unresolved"
        )

        result["confidence"] = 0.0

        return result

    @classmethod
    def resolve_against_entity(
        cls,
        raw_location: str | None,
        entity_city: str | None,
        entity_country: str | None,
    ) -> dict[str, Any]:
        """
        Resolve event location against a known business entity.

        Returns location match information without inventing
        geographic data.
        """

        event_location = cls.resolve(
            raw_location
        )

        event_city = cls.normalize(
            event_location.get("city")
        )

        event_country = cls.normalize(
            event_location.get("country")
        )

        supplier_city = cls.normalize(
            entity_city
        )

        supplier_country = cls.normalize(
            entity_country
        )

        city_match = bool(
            event_city
            and supplier_city
            and event_city == supplier_city
        )

        country_match = bool(
            event_country
            and supplier_country
            and event_country == supplier_country
        )

        # If NLP only gave "Hamburg", resolver knows
        # Hamburg = Germany.
        if (
            not event_country
            and event_city
            and supplier_city
            and event_city == supplier_city
        ):
            country_match = bool(
                supplier_country
            )

        if city_match and country_match:
            score = 100
            confidence = 1.0
            level = "exact_city_country"

        elif city_match:
            score = 90
            confidence = 0.95
            level = "exact_city"

        elif country_match:
            score = 60
            confidence = 0.80
            level = "exact_country"

        else:
            score = 0
            confidence = 0.0
            level = "no_match"

        reasons: list[str] = []

        if city_match:
            reasons.append(
                "city_exact"
            )

        if country_match:
            reasons.append(
                "country_exact"
            )

        if not reasons:
            reasons.append(
                "location_no_match"
            )

        return {
            "event_location": event_location,
            "entity_city": entity_city,
            "entity_country": entity_country,
            "city_match": city_match,
            "country_match": country_match,
            "match_score": score,
            "confidence": confidence,
            "match_level": level,
            "match_reasons": reasons,
        }

    @staticmethod
    def _display_city(
        normalized_city: str,
    ) -> str:
        """
        Convert normalized city text to readable form.
        """

        special = {
            "new delhi": "New Delhi",
            "los angeles": "Los Angeles",
            "long beach": "Long Beach",
        }

        if normalized_city in special:
            return special[
                normalized_city
            ]

        return normalized_city.title()


__all__ = [
    "LocationResolutionService",
]