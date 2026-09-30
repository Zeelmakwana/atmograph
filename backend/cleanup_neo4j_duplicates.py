"""
AtmoGraph - Neo4j Duplicate Cleanup
===================================

APOC-FREE cleanup utility.

What this script does:
1. Finds duplicate canonical Supplier nodes by supplier_id.
2. Finds duplicate canonical Product nodes by product_id.
3. Moves relationships from duplicate nodes to the keeper.
4. Removes duplicate nodes.
5. Removes duplicate canonical relationships.
6. Creates uniqueness constraints for canonical IDs.
7. Verifies the final graph.

IMPORTANT:
- Only canonical nodes with non-null supplier_id/product_id are cleaned.
- NLP-only nodes with null canonical IDs are NOT deleted.
- No APOC dependency.
"""

from collections import defaultdict

from app.services.neo4j_service import neo4j_service


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

RELATIONSHIP_TYPES = [
    "OCCURS_AT",
    "INVOLVES",
    "AFFECTS",
    "RELATED_TO",
    "DISRUPTS",
    "IMPACTS",
    "SUPPLIES",
    "MANUFACTURES",
    "SHIPS_TO",
    "LOCATED_IN",
    "DEPENDS_ON",
    "DISTRIBUTES_TO",
]


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------

def run_query(query, parameters=None):
    """Execute a Cypher query through the existing Neo4j service."""
    return neo4j_service.execute_query(query, parameters or {})


def print_header(title):
    print()
    print("=" * 70)
    print(f" {title}")
    print("=" * 70)


# ---------------------------------------------------------------------
# Relationship migration
# ---------------------------------------------------------------------

def migrate_relationships(
    label,
    duplicate_element_id,
    keeper_element_id,
):
    """
    Move relationships between duplicate node and keeper.

    We cannot dynamically create relationship types in plain Cypher,
    so we process the known AtmoGraph relationship types individually.
    """

    total_created = 0

    for rel_type in RELATIONSHIP_TYPES:

        # -------------------------------------------------------------
        # Duplicate -> target
        # -------------------------------------------------------------

        outgoing = run_query(
            f"""
            MATCH (dup:{label})-[r:{rel_type}]->(target)
            WHERE elementId(dup) = $duplicate_element_id

            MATCH (keeper:{label})
            WHERE elementId(keeper) = $keeper_element_id

            RETURN
                elementId(target) AS target_id,
                properties(r) AS rel_properties
            """,
            {
                "duplicate_element_id": duplicate_element_id,
                "keeper_element_id": keeper_element_id,
            },
        )

        for item in outgoing:
            target_id = item["target_id"]
            properties = item["rel_properties"] or {}

            # MERGE avoids creating duplicate relationships.
            run_query(
                f"""
                MATCH (keeper:{label})
                WHERE elementId(keeper) = $keeper_element_id

                MATCH (target)
                WHERE elementId(target) = $target_id

                MERGE (keeper)-[r:{rel_type}]->(target)
                SET r += $rel_properties

                RETURN count(r) AS count
                """,
                {
                    "keeper_element_id": keeper_element_id,
                    "target_id": target_id,
                    "rel_properties": properties,
                },
            )

            total_created += 1

        # -------------------------------------------------------------
        # source -> Duplicate
        # -------------------------------------------------------------

        incoming = run_query(
            f"""
            MATCH (source)-[r:{rel_type}]->(dup:{label})
            WHERE elementId(dup) = $duplicate_element_id

            MATCH (keeper:{label})
            WHERE elementId(keeper) = $keeper_element_id

            RETURN
                elementId(source) AS source_id,
                properties(r) AS rel_properties
            """,
            {
                "duplicate_element_id": duplicate_element_id,
                "keeper_element_id": keeper_element_id,
            },
        )

        for item in incoming:
            source_id = item["source_id"]
            properties = item["rel_properties"] or {}

            run_query(
                f"""
                MATCH (source)
                WHERE elementId(source) = $source_id

                MATCH (keeper:{label})
                WHERE elementId(keeper) = $keeper_element_id

                MERGE (source)-[r:{rel_type}]->(keeper)
                SET r += $rel_properties

                RETURN count(r) AS count
                """,
                {
                    "source_id": source_id,
                    "keeper_element_id": keeper_element_id,
                    "rel_properties": properties,
                },
            )

            total_created += 1

    return total_created


# ---------------------------------------------------------------------
# Supplier cleanup
# ---------------------------------------------------------------------

def cleanup_supplier_duplicates():
    print_header("SUPPLIER CLEANUP")

    rows = run_query(
        """
        MATCH (s:Supplier)
        WHERE s.supplier_id IS NOT NULL
        RETURN
            s.supplier_id AS supplier_id,
            collect(elementId(s)) AS node_ids
        ORDER BY supplier_id
        """
    )

    duplicate_groups = 0
    removed_nodes = 0

    for row in rows:

        supplier_id = row["supplier_id"]
        node_ids = row["node_ids"]

        if len(node_ids) <= 1:
            continue

        duplicate_groups += 1

        # Keep first canonical node.
        keeper_id = node_ids[0]
        duplicate_ids = node_ids[1:]

        print()
        print(f"Supplier {supplier_id}: {len(node_ids)} nodes found")
        print(f"  KEEP    : {keeper_id}")

        for duplicate_id in duplicate_ids:

            print(f"  MERGE   : {duplicate_id}")

            migrate_relationships(
                label="Supplier",
                duplicate_element_id=duplicate_id,
                keeper_element_id=keeper_id,
            )

            # Delete duplicate after relationships have been migrated.
            run_query(
                """
                MATCH (dup:Supplier)
                WHERE elementId(dup) = $duplicate_element_id
                DETACH DELETE dup
                """,
                {
                    "duplicate_element_id": duplicate_id,
                },
            )

            removed_nodes += 1
            print("  DELETED : duplicate supplier")

    print()
    print(f"Duplicate supplier groups : {duplicate_groups}")
    print(f"Supplier nodes removed    : {removed_nodes}")


# ---------------------------------------------------------------------
# Product cleanup
# ---------------------------------------------------------------------

def cleanup_product_duplicates():
    print_header("PRODUCT CLEANUP")

    rows = run_query(
        """
        MATCH (p:Product)
        WHERE p.product_id IS NOT NULL
        RETURN
            p.product_id AS product_id,
            collect(elementId(p)) AS node_ids
        ORDER BY product_id
        """
    )

    duplicate_groups = 0
    removed_nodes = 0

    for row in rows:

        product_id = row["product_id"]
        node_ids = row["node_ids"]

        if len(node_ids) <= 1:
            continue

        duplicate_groups += 1

        keeper_id = node_ids[0]
        duplicate_ids = node_ids[1:]

        print()
        print(f"Product {product_id}: {len(node_ids)} nodes found")
        print(f"  KEEP    : {keeper_id}")

        for duplicate_id in duplicate_ids:

            print(f"  MERGE   : {duplicate_id}")

            migrate_relationships(
                label="Product",
                duplicate_element_id=duplicate_id,
                keeper_element_id=keeper_id,
            )

            run_query(
                """
                MATCH (dup:Product)
                WHERE elementId(dup) = $duplicate_element_id
                DETACH DELETE dup
                """,
                {
                    "duplicate_element_id": duplicate_id,
                },
            )

            removed_nodes += 1
            print("  DELETED : duplicate product")

    print()
    print(f"Duplicate product groups : {duplicate_groups}")
    print(f"Product nodes removed    : {removed_nodes}")


# ---------------------------------------------------------------------
# Relationship deduplication
# ---------------------------------------------------------------------

def deduplicate_canonical_relationships():
    """
    Remove duplicate relationships between canonical nodes.

    This is especially important for cases such as:

        Event 25 -> Supplier 1
        Event 25 -> Supplier 1

    where two identical AFFECTS relationships may exist.
    """

    print_header("RELATIONSHIP DEDUPLICATION")

    total_removed = 0

    for rel_type in RELATIONSHIP_TYPES:

        # Find duplicate relationships with the same start/end nodes.
        rows = run_query(
            f"""
            MATCH (a)-[r:{rel_type}]->(b)
            WITH
                elementId(a) AS source_id,
                elementId(b) AS target_id,
                collect(elementId(r)) AS relationship_ids
            WHERE size(relationship_ids) > 1
            RETURN
                source_id,
                target_id,
                relationship_ids
            """
        )

        for row in rows:

            relationship_ids = row["relationship_ids"]

            # Keep first relationship.
            delete_ids = relationship_ids[1:]

            for relationship_id in delete_ids:

                run_query(
                    f"""
                    MATCH (a)-[r:{rel_type}]->(b)
                    WHERE elementId(r) = $relationship_id
                    DELETE r
                    """,
                    {
                        "relationship_id": relationship_id,
                    },
                )

                total_removed += 1

            print(
                f"  {rel_type}: removed {len(delete_ids)} "
                f"duplicate relationship(s)"
            )

    print()
    print(f"Duplicate relationships removed : {total_removed}")


# ---------------------------------------------------------------------
# Constraints
# ---------------------------------------------------------------------

def create_constraints():
    print_header("UNIQUENESS CONSTRAINTS")

    constraints = [
        (
            "supplier_id_unique",
            """
            CREATE CONSTRAINT supplier_id_unique IF NOT EXISTS
            FOR (s:Supplier)
            REQUIRE s.supplier_id IS UNIQUE
            """,
        ),
        (
            "product_id_unique",
            """
            CREATE CONSTRAINT product_id_unique IF NOT EXISTS
            FOR (p:Product)
            REQUIRE p.product_id IS UNIQUE
            """,
        ),
        (
            "event_id_unique",
            """
            CREATE CONSTRAINT event_id_unique IF NOT EXISTS
            FOR (e:Event)
            REQUIRE e.event_id IS UNIQUE
            """,
        ),
    ]

    for name, query in constraints:

        try:
            run_query(query)
            print(f"[PASS] {name}")
        except Exception as exc:
            print(f"[WARN] {name}")
            print(f"       {exc}")


# ---------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------

def verify_cleanup():
    print_header("FINAL VERIFICATION")

    # -------------------------------------------------------------
    # Suppliers
    # -------------------------------------------------------------

    suppliers = run_query(
        """
        MATCH (s:Supplier)
        WHERE s.supplier_id IS NOT NULL
        RETURN
            s.supplier_id AS id,
            count(s) AS count
        ORDER BY id
        """
    )

    print()
    print("SUPPLIERS:")

    supplier_ok = True

    for row in suppliers:
        print(f"  Supplier {row['id']} -> {row['count']} node(s)")

        if row["count"] != 1:
            supplier_ok = False

    # -------------------------------------------------------------
    # Products
    # -------------------------------------------------------------

    products = run_query(
        """
        MATCH (p:Product)
        WHERE p.product_id IS NOT NULL
        RETURN
            p.product_id AS id,
            count(p) AS count
        ORDER BY id
        """
    )

    print()
    print("PRODUCTS:")

    product_ok = True

    for row in products:
        print(f"  Product {row['id']} -> {row['count']} node(s)")

        if row["count"] != 1:
            product_ok = False

    # -------------------------------------------------------------
    # Event 25
    # -------------------------------------------------------------

    event_25 = run_query(
        """
        MATCH (e:Event {event_id: 25})-[r:AFFECTS]->(s:Supplier)
        RETURN
            count(r) AS relationships,
            count(DISTINCT s) AS unique_suppliers,
            collect(DISTINCT s.name) AS suppliers
        """
    )

    print()
    print("EVENT 25 AFFECTS:")

    if event_25:
        data = event_25[0]

        print(f"  Relationships    : {data['relationships']}")
        print(f"  Unique suppliers : {data['unique_suppliers']}")
        print(f"  Suppliers        : {data['suppliers']}")

        event_25_ok = (
            data["relationships"] == data["unique_suppliers"]
        )
    else:
        event_25_ok = True
        print("  Event 25 not found")

    # -------------------------------------------------------------
    # Graph statistics
    # -------------------------------------------------------------

    stats = run_query(
        """
        MATCH (n)
        OPTIONAL MATCH ()-[r]->()
        RETURN
            count(DISTINCT n) AS nodes,
            count(r) AS relationships
        """
    )

    print()
    print("GRAPH:")

    if stats:
        print(f"  Nodes         : {stats[0]['nodes']}")
        print(f"  Relationships : {stats[0]['relationships']}")

    # -------------------------------------------------------------
    # Final result
    # -------------------------------------------------------------

    print()
    print("=" * 70)

    if supplier_ok and product_ok and event_25_ok:
        print(" CLEANUP STATUS: SUCCESS")
    else:
        print(" CLEANUP STATUS: NEEDS ATTENTION")

    print("=" * 70)

    return supplier_ok and product_ok and event_25_ok


# ---------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------

def main():

    print("=" * 70)
    print(" AT M O G R A P H   N E O 4 J   D A T A   C L E A N U P")
    print("=" * 70)

    # Connection check
    try:
        result = run_query(
            "RETURN 1 AS connected"
        )

        if not result or result[0]["connected"] != 1:
            raise RuntimeError("Neo4j connection check failed")

        print()
        print("[PASS] Neo4j connection")
    except Exception as exc:
        print()
        print("[FAIL] Neo4j connection")
        print(exc)
        return

    # Cleanup
    cleanup_supplier_duplicates()
    cleanup_product_duplicates()

    # Remove duplicate relationships after node merging.
    deduplicate_canonical_relationships()

    # Add database-level protection.
    create_constraints()

    # Verify everything.
    success = verify_cleanup()

    print()

    if success:
        print("ATMO GRAPH NEO4J STATUS: CLEAN")
    else:
        print("ATMO GRAPH NEO4J STATUS: CHECK REQUIRED")


if __name__ == "__main__":
    main()