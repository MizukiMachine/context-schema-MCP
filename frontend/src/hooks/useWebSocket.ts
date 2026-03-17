/**
 * Custom hook for WebSocket real-time optimization progress updates.
 */
import { useEffect, useRef, useState, useCallback } from 'react';

const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

export interface WebSocketMessage {
  type: 'connected' | 'subscribed' | 'progress' | 'step_complete' | 'completed' | 'error' | 'pong';
  task_id?: string;
  message?: string;
  progress?: number;
  current_step?: string;
  step?: string;
  result?: unknown;
  error?: string;
}

export interface OptimizationProgress {
  isConnected: boolean;
  progress: number;
  currentStep: string | null;
  completedSteps: string[];
  result: unknown | null;
  error: string | null;
}

export function useOptimizationWebSocket(taskId: string | null) {
  const [state, setState] = useState<OptimizationProgress>({
    isConnected: false,
    progress: 0,
    currentStep: null,
    completedSteps: [],
    result: null,
    error: null,
  });

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    if (!taskId || wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(`${WS_BASE_URL}/api/v1/ws/tasks/${taskId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setState((prev) => ({ ...prev, isConnected: true, error: null }));
      reconnectAttemptsRef.current = 0;

      // Send subscribe message
      ws.send(JSON.stringify({ type: 'subscribe' }));
    };

    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data);
        handleMessage(data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setState((prev) => ({
        ...prev,
        error: 'WebSocket connection error',
      }));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setState((prev) => ({ ...prev, isConnected: false }));
      wsRef.current = null;

      // Attempt reconnection
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          console.log(`Reconnecting... (attempt ${reconnectAttemptsRef.current})`);
          connect();
        }, delay);
      }
    };

    wsRef.current = ws;
  }, [taskId]);

  const handleMessage = (data: WebSocketMessage) => {
    switch (data.type) {
      case 'connected':
      case 'subscribed':
        break;

      case 'progress':
        setState((prev) => ({
          ...prev,
          progress: data.progress ?? 0,
          currentStep: data.current_step ?? null,
        }));
        break;

      case 'step_complete':
        setState((prev) => ({
          ...prev,
          completedSteps: [...prev.completedSteps, data.step ?? ''],
        }));
        break;

      case 'completed':
        setState((prev) => ({
          ...prev,
          progress: 100,
          result: data.result,
        }));
        break;

      case 'error':
        setState((prev) => ({
          ...prev,
          error: data.error ?? 'Unknown error',
        }));
        break;

      case 'pong':
        // Keep-alive response
        break;

      default:
        console.log('Unknown message type:', data.type);
    }
  };

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  const sendPing = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'ping' }));
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  // Keep-alive ping every 30 seconds
  useEffect(() => {
    if (!state.isConnected) return;

    const interval = setInterval(sendPing, 30000);
    return () => clearInterval(interval);
  }, [state.isConnected, sendPing]);

  return {
    ...state,
    reconnect: connect,
    disconnect,
    sendPing,
  };
}

export default useOptimizationWebSocket;
