import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp: number;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

interface ChatContextType {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  currentId: string | null;
  createConversation: (greeting?: string) => string;
  selectConversation: (id: string) => void;
  deleteConversation: (id: string) => void;
  addMessage: (message: ChatMessage) => void;
  currentMessages: ChatMessage[];
}

const STORAGE_KEY = 'fitcoach_conversations';
const CURRENT_KEY = 'fitcoach_current_conv';

const ChatContext = createContext<ChatContextType | undefined>(undefined);

export function ChatProvider({ children }: { children: ReactNode }) {
  const [conversations, setConversations] = useState<Conversation[]>(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const [currentId, setCurrentId] = useState<string | null>(() => {
    return localStorage.getItem(CURRENT_KEY) || null;
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations));
  }, [conversations]);

  useEffect(() => {
    if (currentId) {
      localStorage.setItem(CURRENT_KEY, currentId);
    } else {
      localStorage.removeItem(CURRENT_KEY);
    }
  }, [currentId]);

  const currentConversation = conversations.find(c => c.id === currentId) || null;

  const createConversation = useCallback((greeting?: string) => {
    const id = Date.now().toString();
    const messages: ChatMessage[] = greeting
      ? [{ role: 'assistant', content: greeting, timestamp: Date.now() }]
      : [];
    const newConv: Conversation = {
      id,
      title: '',
      messages,
      createdAt: Date.now(),
      updatedAt: Date.now(),
    };
    setConversations(prev => [newConv, ...prev]);
    setCurrentId(id);
    return id;
  }, []);

  const selectConversation = useCallback((id: string) => {
    setCurrentId(id);
  }, []);

  const deleteConversation = useCallback((id: string) => {
    setConversations(prev => prev.filter(c => c.id !== id));
    setCurrentId(prev => prev === id ? null : prev);
  }, []);

  const addMessage = useCallback((message: ChatMessage) => {
    setConversations(prev => prev.map(c => {
      if (c.id !== currentId) return c;
      const updatedMessages = [...c.messages, message];
      // Set title from first user message
      const title = !c.title && message.role === 'user'
        ? message.content.slice(0, 50) + (message.content.length > 50 ? '...' : '')
        : c.title;
      return { ...c, messages: updatedMessages, title, updatedAt: Date.now() };
    }));
  }, [currentId]);

  return (
    <ChatContext.Provider value={{
      conversations,
      currentConversation,
      currentId,
      createConversation,
      selectConversation,
      deleteConversation,
      addMessage,
      currentMessages: currentConversation?.messages || [],
    }}>
      {children}
    </ChatContext.Provider>
  );
}

export function useChat() {
  const context = useContext(ChatContext);
  if (!context) throw new Error('useChat must be used within ChatProvider');
  return context;
}