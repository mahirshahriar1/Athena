"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAppDispatch } from "@/lib/store";
import { addEvent, setCurrentNode, setStatus, setError, TimelineEvent } from "@/lib/slices/researchSlice";

interface UseResearchStreamOptions {
  jobId: string | null;
  enabled: boolean;
}

interface UseResearchStreamReturn {
  isConnected: boolean;
  disconnect: () => void;
}

export function useResearchStream({
  jobId,
  enabled,
}: UseResearchStreamOptions): UseResearchStreamReturn {
  const dispatch = useAppDispatch();
  const wsRef = useRef<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const handleMessage = useCallback(
    (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        const timelineEvent: TimelineEvent = {
          id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
          type: data.type,
          node: data.node || "",
          content: data.content,
          timestamp: new Date().toISOString(),
        };

        dispatch(addEvent(timelineEvent));

        switch (data.type) {
          case "node_start":
            dispatch(setCurrentNode(data.node));
            break;
          case "node_done":
            if (data.node === "writer") {
              dispatch(setStatus("completed"));
            }
            break;
          case "complete":
            dispatch(setStatus("completed"));
            break;
          case "error":
            dispatch(setError(data.message));
            break;
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    },
    [dispatch]
  );

  useEffect(() => {
    if (!jobId || !enabled) return;

    const wsBase = process.env.NEXT_PUBLIC_WS_URL || "ws://127.0.0.1:8000";
    const wsUrl = `${wsBase}/api/ws/research/${jobId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
    };

    ws.onmessage = handleMessage;

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
      dispatch(setError("WebSocket connection failed"));
    };

    ws.onclose = () => {
      setIsConnected(false);
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [jobId, enabled, handleMessage, dispatch]);

  return { isConnected, disconnect };
}
