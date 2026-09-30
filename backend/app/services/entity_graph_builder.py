from __future__ import annotations

from typing import Any

from app.services.entity_resolver import EntityResolver


class EntityGraphBuilder:
    """
    Converts AtmoGraph NLP output into a Neo4j-friendly graph structure.

    Responsibilities:
    1. Create Event node.
    2. Resolve generic spaCy entities into AtmoGraph domain types.
    3. Avoid duplicate entities.
    4. Create meaningful event-to-entity relationships.
    """

    def __init__(self) -> None:
        self.resolver = EntityResolver()

    def build(
        self,
        nlp_result: dict[str, Any],
    ) -> dict[str, list[dict[str, Any]]]:

        nodes: list[dict[str, Any]] = []
        relationships: list[dict[str, Any]] = []

        # =========================================================
        # 1. EVENT NODE
        # =========================================================

        title = str(
            nlp_result.get("title", "")
        ).strip()

        event_type = nlp_result.get(
            "event_type",
            "supply_chain_disruption",
        )

        severity = nlp_result.get(
            "severity",
            "medium",
        )

        event_id: str | None = None

        if title:

            event_id = (
                "event_"
                + self._slugify(title)
            )

            nodes.append(
                {
                    "id": event_id,
                    "label": "Event",
                    "name": title,
                    "properties": {
                        "event_type": event_type,
                        "severity": severity,
                        "source": "nlp",
                    },
                }
            )

        # =========================================================
        # 2. RESOLVE SPAcy ENTITIES
        # =========================================================

        entities = nlp_result.get(
            "entities",
            [],
        )

        resolved_entities = self.resolver.resolve(
            entities
        )

        # =========================================================
        # 3. ENTITY NODES
        # =========================================================

        # Keeps track of already-created domain entities.
        # Key = (label, normalized name)
        existing_entities: dict[
            tuple[str, str],
            str,
        ] = {}

        for index, entity in enumerate(
            resolved_entities
        ):

            text = str(
                entity.get("text", "")
            ).strip()

            domain_label = str(
                entity.get(
                    "domain_label",
                    "Entity",
                )
            )

            original_label = str(
                entity.get(
                    "original_label",
                    "",
                )
            )

            if not text:
                continue

            normalized_name = text.lower().strip()

            entity_key = (
                domain_label,
                normalized_name,
            )

            # -----------------------------------------------------
            # Avoid duplicate entity nodes
            # -----------------------------------------------------

            if entity_key in existing_entities:

                node_id = existing_entities[
                    entity_key
                ]

            else:

                node_id = (
                    domain_label.lower()
                    + "_"
                    + self._slugify(text)
                )

                # Ensure uniqueness if same name appears
                # with different entity occurrences.
                if any(
                    node["id"] == node_id
                    for node in nodes
                ):
                    node_id = (
                        f"{node_id}_{index}"
                    )

                nodes.append(
                    {
                        "id": node_id,
                        "label": domain_label,
                        "name": text,
                        "properties": {
                            "entity_type": original_label,
                            "source": "nlp",
                        },
                    }
                )

                existing_entities[
                    entity_key
                ] = node_id

            # -----------------------------------------------------
            # Event → Entity relationship
            # -----------------------------------------------------

            if event_id:

                relationship_type = (
                    self._relationship_for(
                        domain_label
                    )
                )

                self._add_relationship(
                    relationships,
                    source=event_id,
                    target=node_id,
                    relationship_type=relationship_type,
                )

        # =========================================================
        # 4. EXPLICIT LOCATIONS
        # =========================================================

        locations = nlp_result.get(
            "locations",
            [],
        )

        for location in locations:

            location = str(
                location
            ).strip()

            if not location:
                continue

            normalized_location = (
                location.lower().strip()
            )

            # -----------------------------------------------------
            # Check if this location already exists
            # -----------------------------------------------------

            existing_location_id = None

            for (
                key,
                node_id,
            ) in existing_entities.items():

                label, name = key

                if (
                    label in {
                        "Location",
                        "Facility",
                    }
                    and name
                    == normalized_location
                ):
                    existing_location_id = (
                        node_id
                    )
                    break

            # -----------------------------------------------------
            # Create location only if necessary
            # -----------------------------------------------------

            if existing_location_id:

                location_node_id = (
                    existing_location_id
                )

            else:

                location_node_id = (
                    "location_"
                    + self._slugify(location)
                )

                # Avoid ID collision
                if any(
                    node["id"]
                    == location_node_id
                    for node in nodes
                ):
                    location_node_id = (
                        location_node_id
                        + "_explicit"
                    )

                nodes.append(
                    {
                        "id": location_node_id,
                        "label": "Location",
                        "name": location,
                        "properties": {
                            "source": (
                                "nlp_location_extractor"
                            ),
                        },
                    }
                )

                existing_entities[
                    (
                        "Location",
                        normalized_location,
                    )
                ] = location_node_id

            # -----------------------------------------------------
            # Event → Location
            # -----------------------------------------------------

            if event_id:

                self._add_relationship(
                    relationships,
                    source=event_id,
                    target=location_node_id,
                    relationship_type="OCCURS_AT",
                )

        return {
            "nodes": nodes,
            "relationships": relationships,
        }

    # =============================================================
    # RELATIONSHIP MAPPING
    # =============================================================

    @staticmethod
    def _relationship_for(
        label: str,
    ) -> str:

        mapping = {
            "Supplier": "INVOLVES",
            "Organization": "INVOLVES",
            "Facility": "OCCURS_AT",
            "Location": "OCCURS_AT",
            "Product": "AFFECTS",
            "Person": "INVOLVES",
            "Group": "INVOLVES",
        }

        return mapping.get(
            label,
            "RELATED_TO",
        )

    # =============================================================
    # DUPLICATE RELATIONSHIP PROTECTION
    # =============================================================

    @staticmethod
    def _add_relationship(
        relationships: list[dict[str, Any]],
        source: str,
        target: str,
        relationship_type: str,
    ) -> None:

        relationship = {
            "source": source,
            "target": target,
            "type": relationship_type,
        }

        if relationship not in relationships:
            relationships.append(
                relationship
            )

    # =============================================================
    # SLUGIFY
    # =============================================================

    @staticmethod
    def _slugify(
        value: str,
    ) -> str:

        value = value.lower().strip()

        result = []

        for char in value:

            if char.isalnum():
                result.append(char)
            else:
                result.append("_")

        slug = "".join(result)

        while "__" in slug:
            slug = slug.replace(
                "__",
                "_",
            )

        return slug.strip("_")