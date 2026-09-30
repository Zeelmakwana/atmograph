from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.nlp_engine import nlp_engine
from app.services.entity_graph_builder import EntityGraphBuilder
from app.services.neo4j_service import Neo4jService


router = APIRouter(
    prefix="/nlp-graph",
    tags=["NLP → Neo4j"],
)


class NLPGraphRequest(BaseModel):
    title: str
    description: str = ""


@router.post("/analyze-and-sync")
def analyze_and_sync(request: NLPGraphRequest):
    """
    Analyze news using AtmoGraph NLP and
    synchronize the resulting graph into Neo4j.
    """

    # 1. NLP
    nlp_result = nlp_engine.analyze(
        request.title,
        request.description,
    )

    # 2. Resolve + build graph
    graph = EntityGraphBuilder().build(nlp_result)

    # 3. Neo4j
    neo4j = Neo4jService()

    try:
        result = neo4j.sync_nlp_graph(
            nodes=graph["nodes"],
            relationships=graph["relationships"],
        )

        if not result.get("success"):
            raise HTTPException(
                status_code=503,
                detail=result.get(
                    "message",
                    "Neo4j synchronization failed.",
                ),
            )

        return {
            "success": True,
            "nlp": nlp_result,
            "graph": graph,
            "neo4j": result,
        }

    finally:
        neo4j.close()


@router.get("/ripple/{graph_id}")
def get_nlp_ripple(
    graph_id: str,
    max_depth: int = 3,
):
    """
    Return downstream ripple paths for an NLP-generated event.
    """

    neo4j = Neo4jService()

    try:
        if not neo4j.verify_connection():
            raise HTTPException(
                status_code=503,
                detail="Unable to connect to Neo4j.",
            )

        paths = neo4j.get_nlp_ripple(
            graph_id=graph_id,
            max_depth=max_depth,
        )

        return {
            "success": True,
            "graph_id": graph_id,
            "max_depth": max_depth,
            "paths": paths,
        }

    finally:
        neo4j.close()