import { useMemo } from 'react';

// Simple token count estimation (roughly 4 characters per token)
export function useTokenCount(text: string): number {
  return useMemo(() => {
    if (!text) return 0;
    // Rough estimation: ~4 characters per token for English
    // For more accurate counting, use tiktoken on the backend
    return Math.ceil(text.length / 4);
  }, [text]);
}
