const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "http://127.0.0.1:8000";

const WS_BASE_URL =
  API_BASE_URL
    .replace(/^http:/, "ws:")
    .replace(/^https:/, "wss:")
    .replace(/\/$/, "");


export function connectAtmoGraphWebSocket(
  onMessage: (data: any) => void,
  onError?: () => void,
  onClose?: () => void,
) {
  /*
   * Backend:
   *
   * router = APIRouter(prefix="/ws")
   * @router.websocket("/updates")
   *
   * Final endpoint:
   *
   * ws://127.0.0.1:8000/ws/updates
   *
   * IMPORTANT:
   * There is NO /api prefix.
   */

  const url =
    `${WS_BASE_URL}/ws/updates`;

  const socket =
    new WebSocket(url);


  socket.onopen = () => {
    try {
      socket.send(
        JSON.stringify({
          type: "ping",
          source: "atmograph_frontend",
        }),
      );
    } catch {
      // Ignore send failure.
    }
  };


  socket.onmessage = (
    event,
  ) => {
    try {
      const data =
        JSON.parse(event.data);

      onMessage(data);
    } catch {
      // Ignore malformed messages.
    }
  };


  socket.onerror = () => {
    onError?.();
  };


  socket.onclose = () => {
    onClose?.();
  };


  return socket;
}