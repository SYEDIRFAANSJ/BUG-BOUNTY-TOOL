import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';

export const useLiveUpdates = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<any>(null);

  useEffect(() => {
    let ws: WebSocket;
    let reconnectTimer: NodeJS.Timeout;
    let backoff = 1000;

    const connect = () => {
      ws = new WebSocket('ws://localhost:8000/ws/updates');

      ws.onopen = () => {
        setIsConnected(true);
        backoff = 1000;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setLastUpdate(data);
          if (data.type === 'NEW_PROGRAM') {
            toast.success(`New program added: ${data.name}`);
          } else if (data.type === 'SCOPE_UPDATE') {
            toast.info(`Scope updated for ${data.name}`);
          }
        } catch (e) {
          console.error('WebSocket message parsing failed', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        reconnectTimer = setTimeout(connect, backoff);
        backoff = Math.min(backoff * 2, 30000);
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) ws.close();
    };
  }, []);

  return { isConnected, lastUpdate };
};
