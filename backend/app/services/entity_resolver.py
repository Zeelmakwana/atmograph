from __future__ import annotations

from typing import Any


class EntityResolver:
    """
    Converts generic spaCy entities into AtmoGraph domain hints.

    IMPORTANT:
    NLP labels are only hints.
    Final Supplier/Product identity is resolved against
    the canonical supply-chain database.
    """

    COMPANY_HINTS = {
        "maersk",
        "dhl",
        "fedex",
        "ups",
        "amazon",
        "tesla",
        "toyota",
        "volkswagen",
        "apple",
        "samsung",
        "bosch",
    }

    PORT_HINTS = {
        "port",
        "harbor",
        "harbour",
        "terminal",
    }

    def resolve(
        self,
        entities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:

        resolved = []

        for entity in entities:

            text = str(
                entity.get("text", "")
            ).strip()

            if not text:
                continue

            original_label = str(
                entity.get("label", "")
            ).upper().strip()

            domain_label = self._resolve_label(
                text,
                original_label,
            )

            resolved.append(
                {
                    **entity,
                    "original_label": original_label,
                    "domain_label": domain_label,
                }
            )

        return resolved

    def _resolve_label(
        self,
        text: str,
        original_label: str,
    ) -> str:

        normalized = text.lower().strip()

        # Known supply-chain companies
        if normalized in self.COMPANY_HINTS:
            return "Supplier"

        # Ports / terminals / facilities
        if any(
            hint in normalized
            for hint in self.PORT_HINTS
        ):
            return "Facility"

        # DO NOT blindly convert ORG → Supplier.
        # Database-backed resolution happens later.
        if original_label == "ORG":
            return "Entity"

        if original_label == "PRODUCT":
            return "Product"

        if original_label in {
            "GPE",
            "LOC",
        }:
            return "Location"

        if original_label == "FAC":
            return "Facility"

        if original_label == "PERSON":
            return "Person"

        if original_label == "NORP":
            return "Group"

        return "Entity"