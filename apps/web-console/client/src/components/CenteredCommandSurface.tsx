import { motion } from 'framer-motion';
import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'wouter';
import { ArrowRight, ChevronRight, LoaderCircle, Mic, Plus } from 'lucide-react';
import { ChatMessage } from '@/components/ChatMessage';
import { useChatContext, type Message as ChatMessageRecord } from '@/contexts/ChatContext';
import { getActiveUserId } from '@/lib/authUser';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
};

const PROMPTS = [
  'Check my unread emails',
  'Summarize today\'s calendar',
  'Send an email to Sarah about the meeting',
  'Create a workflow for file backups',
  'What needs my attention today?',
  'Draft a follow-up email',
  'Show recent activity',
  'Connect Google Drive',
  'Schedule a meeting tomorrow at 2pm',
  'Find files shared with me this week',
  'Review my latest tasks',
  'Create a new automation',
];

export default function CenteredCommandSurface() {
  const { messages, addMessage, clearMessages } = useChatContext();
  const [inputValue, setInputValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [promptIndex, setPromptIndex] = useState(0);
  const [typedPrompt, setTypedPrompt] = useState('');
  const [promptPhase, setPromptPhase] = useState<'typing' | 'pause' | 'fade'>('typing');

  const inputRef = useRef<HTMLTextAreaElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [, setLocation] = useLocation();

  const hasConversation = messages.length > 0 || isLoading;
  const isExpanded = isFocused || hasConversation || inputValue.trim().length > 0;
  const currentPrompt = PROMPTS[promptIndex % PROMPTS.length];

  useEffect(() => {
    if (!isExpanded && !inputValue) {
      const prompt = currentPrompt;

      if (promptPhase === 'typing' && typedPrompt.length < prompt.length) {
        const nextCharTimer = window.setTimeout(() => {
          setTypedPrompt(prompt.slice(0, typedPrompt.length + 1));
        }, 34);

        return () => window.clearTimeout(nextCharTimer);
      }

      if (promptPhase === 'typing' && typedPrompt.length >= prompt.length) {
        const pauseTimer = window.setTimeout(() => setPromptPhase('pause'), 1600);
        return () => window.clearTimeout(pauseTimer);
      }

      if (promptPhase === 'pause') {
        const fadeTimer = window.setTimeout(() => setPromptPhase('fade'), 180);
        return () => window.clearTimeout(fadeTimer);
      }

      if (promptPhase === 'fade') {
        const resetTimer = window.setTimeout(() => {
          setTypedPrompt('');
          setPromptIndex((index) => (index + 1) % PROMPTS.length);
          setPromptPhase('typing');
        }, 90);

        return () => window.clearTimeout(resetTimer);
      }
    }

    return undefined;
  }, [currentPrompt, inputValue, isExpanded, promptPhase, promptIndex, typedPrompt]);

  useEffect(() => {
    if (isExpanded) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isExpanded]);

  useEffect(() => {
    const textarea = inputRef.current;
    if (!textarea) return;

    textarea.style.height = '0px';
    const nextHeight = Math.min(textarea.scrollHeight, 160);
    textarea.style.height = `${nextHeight}px`;
  }, [inputValue]);

  const shouldRenderPrompt = !isExpanded && !inputValue;
  const promptVisible = shouldRenderPrompt && promptPhase !== 'fade';

  const sendMessage = async () => {
    const trimmed = inputValue.trim();
    if (!trimmed || isLoading) return;

    const userMessage: ChatMessageRecord = {
      id: Date.now().toString(),
      type: 'user',
      content: trimmed,
      timestamp: new Date(),
    };

    addMessage(userMessage);
    setInputValue('');
    setIsLoading(true);

    try {
      const activeUserId = getActiveUserId();
      const response = await fetch('http://localhost:9000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Use-Graph': 'true',
        },
        body: JSON.stringify({
          message: trimmed,
          session_id: sessionId,
          gmail_user_id: activeUserId,
          drive_user_id: activeUserId,
          calendar_user_id: activeUserId,
          history: messages.map((message) => ({
            role: message.type === 'user' ? 'user' : 'assistant',
            content: message.content,
          })),
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to reach ATLAS');
      }

      const data = await response.json();

      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      addMessage({
        id: `${Date.now() + 1}`,
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
      });
    } catch (error) {
      console.error('Chat Error:', error);
      addMessage({
        id: `${Date.now() + 1}`,
        type: 'ai',
        content: 'I could not reach the orchestrator. Please make sure the backend services are running.',
        timestamp: new Date(),
      });
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const clearConversation = () => {
    clearMessages();
    setSessionId(null);
    setIsFocused(false);
    setIsLoading(false);
    setInputValue('');
    setPromptPhase('typing');
  };

  const renderedMessages = useMemo(
    () =>
      messages.map((message) => (
        <div key={message.id} className="border-l border-white/8 pl-4">
          <div className="mb-1 flex items-center justify-between text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
            <span>{message.type === 'user' ? 'You' : 'Atlas'}</span>
            <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
          </div>
          <div className={message.type === 'user' ? 'text-sm leading-6 text-foreground' : 'text-sm leading-6 text-foreground/88'}>
            <ChatMessage message={message.content} isUser={message.type === 'user'} />
          </div>
        </div>
      )),
    [messages],
  );

  const handleKeyDown = (event: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      void sendMessage();
    }
  };

  return (
    <div className={`flex h-full min-h-0 overflow-hidden px-6 py-6 ${isExpanded ? 'items-stretch justify-stretch' : 'items-center justify-center'}`}>
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className={`w-full ${isExpanded ? 'h-full min-h-0 max-w-none' : 'max-w-[640px]'}`}
      >
        <motion.div
          animate={{ height: isExpanded ? '100%' : 48 }}
          transition={{ duration: 0.22, ease: 'easeInOut' }}
          className={`overflow-hidden border border-white/[0.08] bg-white/[0.03] ${isExpanded ? 'h-full min-h-0 rounded-[16px]' : 'rounded-[12px]'}`}
        >
          <div className="flex h-full min-h-0 flex-col">
            {isExpanded && (
              <div className="flex items-center justify-between border-b border-white/5 px-4 py-3">
                <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
                  <span className="h-1.5 w-1.5 rounded-full bg-primary" />
                  Ready
                </div>
                <button
                  onClick={clearConversation}
                  className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground transition-colors duration-150 hover:text-foreground"
                >
                  Clear
                </button>
              </div>
            )}

            {isExpanded && (
              <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-4 py-4 scrollbar-hide">
                <div className="space-y-4">
                  {renderedMessages}

                  {!messages.length && !isLoading && (
                    <div className="border-l border-white/8 pl-4 text-sm leading-6 text-muted-foreground">
                      No active conversation. Start by typing a command.
                    </div>
                  )}

                  {isLoading && (
                    <div className="border-l border-white/8 pl-4 text-sm leading-6 text-muted-foreground">
                      <span className="inline-flex items-center gap-2">
                        <LoaderCircle size={14} className="animate-spin" />
                        Working
                      </span>
                    </div>
                  )}

                  <div ref={messagesEndRef} />
                </div>
              </div>
            )}

            <div className={`relative flex items-center px-4 ${isExpanded ? 'border-t border-white/5 py-3' : 'h-12'}`}>
              <div className="pointer-events-none absolute inset-y-0 left-4 flex items-center text-sm text-muted-foreground">
                <span className={`${promptVisible ? 'opacity-100' : 'opacity-0'} transition-opacity duration-200 ease-in-out`}>
                  {typedPrompt}
                </span>
                {promptVisible && (
                  <motion.span
                    animate={{ opacity: [0, 1, 0] }}
                    transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
                    className="ml-0.5 inline-block h-4 w-px bg-muted-foreground"
                  />
                )}
              </div>

              <textarea
                ref={inputRef}
                value={inputValue}
                onChange={(event) => setInputValue(event.target.value)}
                onFocus={() => setIsFocused(true)}
                onBlur={() => setIsFocused(false)}
                onKeyDown={handleKeyDown}
                rows={1}
                spellCheck={false}
                aria-label="Command input"
                placeholder={isFocused ? 'Type a command' : ''}
                className={`relative z-10 w-full resize-none bg-transparent text-sm leading-6 outline-none placeholder:text-muted-foreground/70 ${
                  inputValue ? 'text-foreground' : 'text-transparent caret-white'
                }`}
                style={{ minHeight: 20 }}
              />

              <div className="ml-3 flex items-center gap-1">
                <button
                  onClick={() => setLocation('/tools')}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors duration-150 hover:text-foreground"
                  aria-label="Open tools"
                >
                  <Plus size={15} />
                </button>
                <button
                  onClick={() => setLocation('/integrations')}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors duration-150 hover:text-foreground"
                  aria-label="Connect services"
                >
                  <ChevronRight size={15} />
                </button>
                <button
                  onClick={sendMessage}
                  disabled={!inputValue.trim() || isLoading}
                  className="inline-flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground transition-colors duration-150 hover:text-foreground disabled:opacity-40"
                  aria-label="Send command"
                >
                  <ArrowRight size={15} />
                </button>
              </div>
            </div>
          </div>
        </motion.div>

        {!isExpanded && (
          <div className="mt-3 flex items-center justify-center gap-2 text-[10px] uppercase tracking-[0.3em] text-muted-foreground">
            <Mic size={12} />
            <span>Type to begin</span>
          </div>
        )}
      </motion.div>
    </div>
  );
}