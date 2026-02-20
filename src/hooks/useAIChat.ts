import { useState, useCallback, useRef } from 'react';
import { useAuth } from './useAuth';
import { useLanguage } from '@/contexts/LanguageContext';

interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

interface ChatResponse {
  reply: string;
  conversation_id: string;
  language: string;
}

const AI_BACKEND_URL = import.meta.env.VITE_AI_BACKEND_URL || 'http://127.0.0.1:8000';

export function useAIChat() {
  const { user } = useAuth();
  const { language } = useLanguage();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const sendMessage = useCallback(
    async (
      message: string,
      conversationId?: string,
      onChunk?: (chunk: string) => void
    ): Promise<ChatResponse | null> => {
      if (!message.trim()) {
        setError('Message cannot be empty');
        return null;
      }

      setIsLoading(true);
      setError(null);
      abortControllerRef.current = new AbortController();

      try {
        // Map language codes for backend
        const backendLanguage = language === 'ar' ? 'ar_fusha' : language;

        const response = await fetch(`${AI_BACKEND_URL}/chat`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            message: message.trim(),
            user_id: user?.id || 'anonymous',
            conversation_id: conversationId || 'default',
            language: backendLanguage,
            stream: false,
          }),
          signal: abortControllerRef.current.signal,
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(
            errorData.detail || `Request failed with status ${response.status}`
          );
        }

        const data: ChatResponse = await response.json();
        setIsLoading(false);
        return data;
      } catch (err) {
        if (err instanceof Error) {
          if (err.name !== 'AbortError') {
            setError(err.message);
            console.error('Chat API error:', err);
          }
        }
        setIsLoading(false);
        return null;
      }
    },
    [user, language]
  );

  const getHistory = useCallback(
    async (conversationId: string): Promise<ChatMessage[] | null> => {
      try {
        const response = await fetch(
          `${AI_BACKEND_URL}/conversation/${conversationId}?user_id=${user?.id || 'anonymous'}`,
          {
            method: 'GET',
            signal: abortControllerRef.current?.signal,
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch history: ${response.status}`);
        }

        const data = await response.json();
        return data.messages || [];
      } catch (err) {
        console.error('History fetch error:', err);
        return null;
      }
    },
    [user]
  );

  const clearConversation = useCallback(
    async (conversationId: string): Promise<boolean> => {
      try {
        const response = await fetch(
          `${AI_BACKEND_URL}/conversation/${conversationId}/clear`,
          {
            method: 'POST',
            body: JSON.stringify({ user_id: user?.id || 'anonymous' }),
            headers: { 'Content-Type': 'application/json' },
            signal: abortControllerRef.current?.signal,
          }
        );

        return response.ok;
      } catch (err) {
        console.error('Clear error:', err);
        return false;
      }
    },
    [user]
  );

  const cancel = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsLoading(false);
  }, []);

  const checkHealth = useCallback(async (): Promise<boolean> => {
    try {
      const response = await fetch(`${AI_BACKEND_URL}/health`);
      return response.ok;
    } catch {
      return false;
    }
  }, []);

  return {
    sendMessage,
    getHistory,
    clearConversation,
    cancel,
    checkHealth,
    isLoading,
    error,
    setError,
  };
}
