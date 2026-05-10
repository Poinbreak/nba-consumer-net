import { useEffect, useRef, useCallback } from 'react';

const WS_BASE = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000/ws';

/**
 * Connects to the Django Channels WebSocket for a specific game.
 * Calls onMessage(data) whenever a game_update payload arrives.
 * Auto-reconnects with exponential back-off.
 */
export function useGameWebSocket(gameId, onMessage) {
  const wsRef        = useRef(null);
  const retryDelay   = useRef(1000);
  const mountedRef   = useRef(true);

  const connect = useCallback(() => {
    if (!gameId || !mountedRef.current) return;

    const url = `${WS_BASE}/game/${gameId}/`;
    const ws  = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log(`[WS] Connected to game ${gameId}`);
      retryDelay.current = 1000; // reset back-off on success
    };

    ws.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.type === 'game_update' && onMessage) {
          onMessage(payload.data);
        }
      } catch (err) {
        console.error('[WS] parse error', err);
      }
    };

    ws.onerror = (err) => console.error('[WS] error', err);

    ws.onclose = () => {
      if (!mountedRef.current) return;
      console.warn(`[WS] Closed. Retrying in ${retryDelay.current}ms`);
      setTimeout(connect, retryDelay.current);
      retryDelay.current = Math.min(retryDelay.current * 2, 30000);
    };
  }, [gameId, onMessage]);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      wsRef.current?.close();
    };
  }, [connect]);
}
