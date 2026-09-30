from app.api.routes.websocket import manager


async def broadcast_event_created(event: dict):
    await manager.broadcast({
        "type": "event_created",
        "event": event,
    })


async def broadcast_graph_updated(
    event_id: int,
    graph_id: str,
):
    await manager.broadcast({
        "type": "graph_updated",
        "event_id": event_id,
        "graph_id": graph_id,
    })


async def broadcast_prediction_updated(
    event_id: int,
    graph_id: str,
    prediction: dict,
):
    await manager.broadcast({
        "type": "prediction_updated",
        "event_id": event_id,
        "graph_id": graph_id,
        "prediction": prediction,
    })


async def broadcast_intelligence_created(
    event: dict,
    graph_id: str,
    prediction: dict | None = None,
):
    await manager.broadcast({
        "type": "intelligence_created",
        "event": event,
        "graph_id": graph_id,
        "prediction": prediction,
    })