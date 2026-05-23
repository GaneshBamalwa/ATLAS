import { motion } from 'framer-motion';
import { Send, Paperclip, Plus } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';
import { FadeIn, StaggerContainer } from '@/ui/animations/LayoutTransition';
import { getActiveUserId } from '@/lib/authUser';
import { useChatContext, Message } from '@/contexts/ChatContext';

export default function ChatPanel() {
  const { messages, addMessage, updateMessage, setMessages } = useChatContext();
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Orchestrating');
  const [isFocused, setIsFocused] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with welcome message if empty
  useEffect(() => {
    if (messages.length === 0) {
      addMessage({
        id: '1',
        type: 'ai',
        content: 'Hello! I\'m ATLAS, your AI orchestration assistant. I can help you manage complex workflows across Gmail, Google Drive, Calendar, and other integrated services. What would you like to accomplish today?',
        timestamp: new Date(),
      });
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = async () => {
    if (!inputValue.trim()) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date(),
      status: 'sending',
    };

    addMessage(userMessage);
    const currentInput = inputValue;
    setInputValue('');
    setIsLoading(true);
    setLoadingStep('Planning intent');

    // Simulate step changes for better UX since it's not a streaming API yet
    const steps = ['Analyzing context', 'Executing tools', 'Synthesizing result'];
    let stepIndex = 0;
    const stepInterval = setInterval(() => {
      if (stepIndex < steps.length) {
        setLoadingStep(steps[stepIndex]);
        stepIndex++;
      }
    }, 2000);

    try {
      const activeUserId = getActiveUserId();
      const response = await fetch('http://localhost:9000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: currentInput,
          session_id: sessionId,
          gmail_user_id: activeUserId,
          drive_user_id: activeUserId,
          calendar_user_id: activeUserId,
          history: messages.map(m => ({ role: m.type === 'user' ? 'user' : 'assistant', content: m.content }))
        }),
      });

      clearInterval(stepInterval);
      if (!response.ok) throw new Error('Failed to reach ATLAS');

      const data = await response.json();
      
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      // DEBUG: Check what the API actually returned
      if (data.response && data.response.includes('Email Sent')) {
        console.log("=== API RESPONSE CHECK ===");
        console.log("Response length:", data.response.length);
        console.log("Response has newlines:", data.response.includes('\n'));
        console.log("Newline count:", (data.response.match(/\n/g) || []).length);
        console.log("First 200 chars (JSON):", JSON.stringify(data.response.substring(0, 200)));
        console.log("===========================");
      }

      // Update user message status to sent
      updateMessage(userMessage.id, { status: 'sent' });

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        tools: data.trace?.steps?.map((s: any) => s.title.replace('Activity: ', '')) || [],
        pipeline: data.pipeline ?? undefined,
      };

      addMessage(aiResponse);
    } catch (error) {
      clearInterval(stepInterval);
      console.error('Chat Error:', error);
      
      // Update user message status to error
      updateMessage(userMessage.id, { status: 'error' });
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'I apologize, but I encountered an error connecting to the ATLAS Orchestrator. Please ensure the backend services are running.',
        timestamp: new Date(),
        status: 'error'
      };
      addMessage(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative flex h-full min-h-0 flex-col overflow-hidden">
      <div className="border-b border-white/5 px-6 py-5">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-medium tracking-tight text-foreground">Command Log</h2>
            <p className="mt-1 text-xs text-muted-foreground">ATLAS is ready for the next instruction.</p>
          </div>
          <div className="flex items-center gap-2 text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" />
            Online
          </div>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto overscroll-contain px-6 py-5 custom-scrollbar">
        <StaggerContainer className="space-y-4">
          {messages.map((message, index) => (
            <FadeIn key={message.id}>
              <MessageBubble message={message} index={index} />
            </FadeIn>
          ))}

          {isLoading && (
            <FadeIn className="mb-4 flex items-center gap-3 rounded-2xl border border-white/5 bg-white/[0.02] px-4 py-3">
              <div className="flex gap-1.5">
                {[0, 0.2, 0.4].map((delay) => (
                  <motion.div
                    key={delay}
                    animate={{ scale: [1, 1.2, 1], opacity: [0.45, 1, 0.45] }}
                    transition={{ duration: 1.4, repeat: Infinity, delay, ease: 'easeInOut' }}
                    className="h-1.5 w-1.5 rounded-full bg-white/50"
                  />
                ))}
              </div>
              <motion.div
                key={loadingStep}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center gap-2"
              >
                <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                  {loadingStep}
                </span>
                <span className="text-[10px] text-primary">…</span>
              </motion.div>
            </FadeIn>
          )}

          <div ref={messagesEndRef} className="h-16" />
        </StaggerContainer>
      </div>

      <div className="shrink-0 border-t border-white/5 px-6 py-5">
        <motion.div
          animate={{ y: isFocused ? -2 : 0 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="flex items-center gap-2 rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2"
        >
          <motion.button
            whileHover={{ opacity: 0.78 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 hover:text-foreground"
          >
            <Plus size={18} />
          </motion.button>

          <input
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type a command..."
            className="flex-1 bg-transparent py-3 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />

          <div className="flex items-center gap-1">
            <motion.button
              whileHover={{ opacity: 0.78 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 hover:text-foreground"
            >
              <Paperclip size={17} />
            </motion.button>

            <motion.button
              whileHover={{ opacity: 0.9 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white transition-opacity duration-150 disabled:opacity-40"
            >
              <Send size={16} />
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
            <div className="flex gap-1.5">
              {[0, 0.2, 0.4].map((delay) => (
                <motion.div
                  key={delay}
                  animate={{ scale: [1, 1.2, 1], opacity: [0.45, 1, 0.45] }}
                  transition={{ duration: 1.4, repeat: Infinity, delay, ease: 'easeInOut' }}
                  className="h-1.5 w-1.5 rounded-full bg-white/50"
                />
              ))}
            </div>
            <motion.div
              key={loadingStep}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex items-center gap-2"
            >
              <span className="text-[10px] uppercase tracking-[0.22em] text-muted-foreground">
                {loadingStep}
              </span>
              <span className="text-[10px] text-primary">…</span>
            </motion.div>
          </FadeIn>
        )}

        <div ref={messagesEndRef} className="h-16" />
      </StaggerContainer>

      <div className="border-t border-white/5 px-6 py-5">
        <motion.div
          animate={{ y: isFocused ? -2 : 0 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="flex items-center gap-2 rounded-2xl border border-white/8 bg-white/[0.03] px-3 py-2"
        >
          <motion.button
            whileHover={{ opacity: 0.78 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 hover:text-foreground"
          >
            <Plus size={18} />
          </motion.button>

          <input
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type a command..."
            className="flex-1 bg-transparent py-3 text-sm text-foreground outline-none placeholder:text-muted-foreground"
          />

          <div className="flex items-center gap-1">
            <motion.button
              whileHover={{ opacity: 0.78 }}
              whileTap={{ scale: 0.98 }}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 hover:text-foreground"
            >
              <Paperclip size={17} />
            </motion.button>

            <motion.button
              whileHover={{ opacity: 0.9 }}
              whileTap={{ scale: 0.98 }}
              onClick={handleSendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary text-white transition-opacity duration-150 disabled:opacity-40"
            >
              <Send size={16} />
            </motion.button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
