import {
  useEffect,
  useRef,
  useState,
} from "react";

import {
  connectAtmoGraphWebSocket,
} from "../services/websocket";

export function useLiveUpdates(
  onUpdate?: (data: any) => void
) {
  const [connected, setConnected] =
    useState(false);

  const [lastUpdate, setLastUpdate] =
    useState<any>(null);

  const callbackRef =
    useRef(onUpdate);

  const socketRef =
    useRef<WebSocket | null>(null);

  useEffect(() => {
    callbackRef.current =
      onUpdate;
  }, [onUpdate]);

  useEffect(() => {
    let disposed = false;

    const socket =
      connectAtmoGraphWebSocket(
        (data) => {
          if (disposed) {
            return;
          }

          setConnected(true);
          setLastUpdate(data);

          callbackRef.current?.(
            data
          );
        },
        () => {
          if (!disposed) {
            setConnected(false);
          }
        },
        () => {
          if (!disposed) {
            setConnected(false);
          }
        }
      );

    socketRef.current =
      socket;

    return () => {
      disposed = true;

      if (
        socketRef.current
      ) {
        socketRef.current.close();
        socketRef.current = null;
      }

      setConnected(false);
    };
  }, []);

  return {
    connected,
    lastUpdate,
  };
}