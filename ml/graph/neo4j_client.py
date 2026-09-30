from neo4j import Driver, GraphDatabase

from app.core.config import settings


class Neo4jClient:
    """
    Reusable Neo4j database client for AtmoGraph.
    """

    def __init__(self) -> None:
        self._driver: Driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(
                settings.NEO4J_USERNAME,
                settings.NEO4J_PASSWORD,
            ),
        )

    def verify_connection(self) -> bool:
        """
        Verify that Neo4j is reachable.
        """

        self._driver.verify_connectivity()
        return True

    def close(self) -> None:
        """
        Close the Neo4j driver.
        """

        self._driver.close()


neo4j_client = Neo4jClient()