import React, { createContext, useContext, useState, useEffect } from 'react';

export interface PipelineNode {
  id: string;
  label: string;
  status: 'success' | 'error' | 'pending';
  duration: number;
  error?: string;
}

export interface PipelineEdge {
  source: string;
  target: string;
  type: string;
}

export interface PipelineData {
  nodes: PipelineNode[];
  edges: PipelineEdge[];
  execution_time_ms: number;
}

export interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
  tools?: string[];
  pipeline?: PipelineData;
}

interface ChatContextType {
  messages: Message[];
  addMessage: (message: Message) => void;
  updateMessage: (id: string, updates: Partial<Message>) => void;
  setMessages: (messages: Message[]) => void;
  clearMessages: () => void;
}

const ChatContext = createContext<ChatContextType | undefined>(undefined);

const CHAT_STORAGE_KEY = 'atlas_chat_messages';

export function ChatProvider({ children }: { children: React.ReactNode }) {
  const [messages, setMessagesState] = useState<Message[]>(() => {
    const stored = localStorage.getItem(CHAT_STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        return parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
      } catch {
        return [];
      }
    }
    return [];
  });

  // Persist messages to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(CHAT_STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  const addMessage = (message: Message) => {
    setMessagesState((prev) => [...prev, message]);
  };

  const updateMessage = (id: string, updates: Partial<Message>) => {
    setMessagesState((prev) =>
      prev.map((msg) => (msg.id === id ? { ...msg, ...updates } : msg))
    );
  };

  const setMessages = (newMessages: Message[]) => {
    setMessagesState(newMessages);
  };

  const clearMessages = () => {
    setMessagesState([]);
    localStorage.removeItem(CHAT_STORAGE_KEY);
  };

  return (
    <ChatContext.Provider
      value={{
        messages,
        addMessage,
        updateMessage,
        setMessages,
        clearMessages,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

export function useChatContext() {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error('useChatContext must be used within ChatProvider');
  }
  return context;
}
