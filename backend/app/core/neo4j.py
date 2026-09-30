from neo4j import Driver

from app.services.neo4j_service import neo4j_service


def get_neo4j_driver() -> Driver:
    """
    Return the active Neo4j driver.

    Raises:
        RuntimeError: If the Neo4j database connection has not been initialized.
    """
    if neo4j_service.driver is None:
        raise RuntimeError("Neo4j database connection is not initialized.")

    return neo4j_service.driver


def verify_neo4j() -> bool:
    """
    Verify that the Neo4j database is reachable.
    """
    if neo4j_service.driver is None:
        return False

    return neo4j_service.verify_connection()