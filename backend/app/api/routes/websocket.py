"""
AtmoGraph WebSocket Routes.

Central real-time connection manager for AtmoGraph.

Supported backend event types:

    EVENT_CREATED
    IMPACT_UPDATED
    RISK_UPDATED
    GRAPH_UPDATED
    PREDICTION_UPDATED
    INTELLIGENCE_UPDATED

The WebSocket layer is transport-only.
Business intelligence remains inside the existing services.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)


router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)


logger = logging.getLogger(__name__)


# ============================================================
# CONNECTION MANAGER
# ============================================================


class ConnectionManager:
    """
    Manage all active AtmoGraph WebSocket connections.

    The manager also keeps a reference to the main asyncio
    event loop so synchronous backend services running inside
    worker threads can safely schedule WebSocket broadcasts.
    """

    def __init__(self) -> None:

        self.active_connections: list[
            WebSocket
        ] = []

        self._loop: asyncio.AbstractEventLoop | None = None

    # ========================================================
    # REGISTER EVENT LOOP
    # ========================================================

    def register_loop(self) -> None:
        """
        Register the currently running FastAPI event loop.
        """

        try:

            self._loop = asyncio.get_running_loop()

        except RuntimeError:

            logger.warning(
                "Unable to register WebSocket event loop."
            )

    # ========================================================
    # CONNECT
    # ========================================================

    async def connect(
        self,
        websocket: WebSocket,
    ) -> None:
        """
        Accept and register a WebSocket connection.
        """

        await websocket.accept()

        self.register_loop()

        if websocket not in self.active_connections:

            self.active_connections.append(
                websocket
            )

        logger.info(
            (
                "WebSocket client connected. "
                "active_connections=%s"
            ),
            len(self.active_connections),
        )

    # ========================================================
    # DISCONNECT
    # ========================================================

    def disconnect(
        self,
        websocket: WebSocket,
    ) -> None:
        """
        Remove a WebSocket connection.
        """

        if websocket in self.active_connections:

            self.active_connections.remove(
                websocket
            )

        logger.info(
            (
                "WebSocket client disconnected. "
                "active_connections=%s"
            ),
            len(self.active_connections),
        )

    # ========================================================
    # BROADCAST
    # ========================================================

    async def broadcast(
        self,
        message: dict[str, Any],
    ) -> None:
        """
        Broadcast a JSON message to every connected client.
        """

        if not self.active_connections:

            return

        disconnected: list[
            WebSocket
        ] = []

        for connection in list(
            self.active_connections
        ):

            try:

                await connection.send_json(
                    message
                )

            except Exception:

                disconnected.append(
                    connection
                )

        for connection in disconnected:

            self.disconnect(
                connection
            )

    # ========================================================
    # STANDARD EVENT BROADCAST
    # ========================================================

    async def broadcast_event(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        *,
        event_id: int | None = None,
        graph_id: str | None = None,
    ) -> None:
        """
        Broadcast a standardized AtmoGraph event.
        """

        message: dict[str, Any] = {
            "type": event_type,
            "data": data or {},
        }

        if event_id is not None:

            message["event_id"] = event_id

        if graph_id is not None:

            message["graph_id"] = graph_id

        await self.broadcast(
            message
        )

    # ========================================================
    # THREAD-SAFE BROADCAST
    # ========================================================

    def broadcast_from_thread(
        self,
        event_type: str,
        data: dict[str, Any] | None = None,
        *,
        event_id: int | None = None,
        graph_id: str | None = None,
    ) -> None:
        """
        Safely schedule a WebSocket broadcast from a
        synchronous worker thread.

        News ingestion runs in asyncio.to_thread(), so this
        method bridges that worker thread back to FastAPI's
        main event loop.
        """

        if not self.active_connections:

            return

        loop = self._loop

        if loop is None:

            logger.warning(
                (
                    "WebSocket broadcast skipped because "
                    "the FastAPI event loop is not registered."
                )
            )

            return

        if loop.is_closed():

            logger.warning(
                "WebSocket broadcast skipped because event loop is closed."
            )

            return

        coroutine = self.broadcast_event(
            event_type=event_type,
            data=data,
            event_id=event_id,
            graph_id=graph_id,
        )

        try:

            asyncio.run_coroutine_threadsafe(
                coroutine,
                loop,
            )

        except Exception:

            logger.exception(
                "Failed to schedule WebSocket broadcast."
            )


# ============================================================
# GLOBAL MANAGER
# ============================================================


manager = ConnectionManager()


# ============================================================
# WEBSOCKET ENDPOINT
# ============================================================


@router.websocket("/updates")
async def websocket_updates(
    websocket: WebSocket,
) -> None:
    """
    Main AtmoGraph real-time WebSocket endpoint.

    Frontend:

        ws://127.0.0.1:8000/ws/updates
    """

    await manager.connect(
        websocket
    )

    try:

        await websocket.send_json(
            {
                "type": "connection",
                "status": "connected",
                "message": (
                    "AtmoGraph live updates connected"
                ),
            }
        )

        while True:

            raw_message = (
                await websocket.receive_text()
            )

            try:

                message = json.loads(
                    raw_message
                )

            except json.JSONDecodeError:

                message = {
                    "type": raw_message
                }

            if not isinstance(
                message,
                dict,
            ):

                message = {
                    "type": str(message)
                }

            message_type = (
                message.get("type")
            )

            # ------------------------------------------------
            # HEARTBEAT
            # ------------------------------------------------

            if message_type == "ping":

                await websocket.send_json(
                    {
                        "type": "pong",
                        "status": "ok",
                    }
                )

                continue

            # ------------------------------------------------
            # OPTIONAL SUBSCRIPTION
            # ------------------------------------------------

            if message_type == "subscribe":

                await websocket.send_json(
                    {
                        "type": "subscription",
                        "status": "ok",
                        "event_id": message.get(
                            "event_id"
                        ),
                        "graph_id": message.get(
                            "graph_id"
                        ),
                    }
                )

                continue

            logger.debug(
                "WebSocket client message: %s",
                message,
            )

    except WebSocketDisconnect:

        manager.disconnect(
            websocket
        )

    except Exception as exc:

        logger.exception(
            "WebSocket error: %s",
            exc,
        )

        manager.disconnect(
            websocket
        )