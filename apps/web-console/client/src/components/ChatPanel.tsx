import { motion } from 'framer-motion';
import { Send, Paperclip, Plus } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
import MessageBubble from './MessageBubble';
import { FadeIn, StaggerContainer } from '@/ui/animations/LayoutTransition';
import { GlassPanel } from '@/ui/primitives/GlassPanel';

interface Message {
  id: string;
  type: 'user' | 'ai';
  content: string;
  timestamp: Date;
  status?: 'sending' | 'sent' | 'error';
  tools?: string[];
}

export default function ChatPanel() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'ai',
      content: 'Hello! I\'m ATLAS, your AI orchestration assistant. I can help you manage complex workflows across Gmail, Google Drive, Calendar, and other integrated services. What would you like to accomplish today?',
      timestamp: new Date(),
    },
  ]);

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState('Orchestrating');
  const [isFocused, setIsFocused] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

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

    setMessages((prev) => [...prev, userMessage]);
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
      const response = await fetch('http://localhost:9000/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Use-Graph': 'true',
        },
        body: JSON.stringify({
          message: currentInput,
          session_id: sessionId,
          gmail_user_id: 'default_user',
          drive_user_id: 'default_user',
          history: messages.map(m => ({ role: m.type === 'user' ? 'user' : 'assistant', content: m.content }))
        }),
      });

      clearInterval(stepInterval);
      if (!response.ok) throw new Error('Failed to reach ATLAS');

      const data = await response.json();
      
      if (!sessionId && data.session_id) {
        setSessionId(data.session_id);
      }

      const aiResponse: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        tools: data.trace?.steps?.map((s: any) => s.title.replace('Activity: ', '')) || [],
      };

      setMessages((prev) => 
        prev.map(m => m.id === userMessage.id ? { ...m, status: 'sent' } : m).concat(aiResponse)
      );
    } catch (error) {
      clearInterval(stepInterval);
      console.error('Chat Error:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'I apologize, but I encountered an error connecting to the ATLAS Orchestrator. Please ensure the backend services are running.',
        timestamp: new Date(),
        status: 'error'
      };
      setMessages((prev) => prev.concat(errorMessage));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col relative">
      {/* Header - Transparent overlay glass */}
      <div className="p-6 border-b border-white/5 bg-white/[0.02] backdrop-blur-md z-10">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="font-display text-lg tracking-tight text-foreground-primary">Conversation</h2>
            <div className="flex items-center gap-2 mt-1">
              <span className="w-1.5 h-1.5 rounded-full bg-accent-green shadow-[0_0_8px_#32D74B]" />
              <p className="text-[10px] uppercase tracking-widest text-foreground-tertiary font-medium">ATLAS Active</p>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <StaggerContainer className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        {messages.map((message, index) => (
          <FadeIn key={message.id}>
            <MessageBubble message={message} index={index} />
          </FadeIn>
        ))}

        {isLoading && (
          <FadeIn className="flex gap-3">
            <GlassPanel intensity="medium" className="px-4 py-2.5 rounded-2xl rounded-tl-none border-white/5 flex items-center gap-3 shadow-lg">
              <div className="flex gap-1">
                {[0, 0.2, 0.4].map((delay) => (
                  <motion.div
                    key={delay}
                    animate={{ 
                      scale: [1, 1.3, 1], 
                      opacity: [0.4, 1, 0.4],
                      backgroundColor: ['#BF5AF2', '#64D2FF', '#BF5AF2']
                    }}
                    transition={{ duration: 1.5, repeat: Infinity, delay, ease: "easeInOut" }}
                    className="w-1 h-1 rounded-full bg-accent-purple shadow-[0_0_8px_rgba(191,90,242,0.4)]"
                  />
                ))}
              </div>
              <motion.div
                key={loadingStep}
                initial={{ opacity: 0, y: 5 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center"
              >
                <motion.span 
                  animate={{ 
                    opacity: [0.5, 1, 0.5],
                    textShadow: ['0 0 0px rgba(255,255,255,0)', '0 0 8px rgba(255,255,255,0.3)', '0 0 0px rgba(255,255,255,0)']
                  }}
                  transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
                  className="text-[10px] font-bold text-foreground-secondary uppercase tracking-[0.15em] whitespace-nowrap"
                >
                  {loadingStep}
                </motion.span>
                <motion.span
                  animate={{ opacity: [0, 1, 0] }}
                  transition={{ duration: 1, repeat: Infinity, times: [0, 0.5, 1] }}
                  className="text-[10px] font-bold text-accent-blue ml-0.5"
                >
                  ...
                </motion.span>
              </motion.div>
            </GlassPanel>
          </FadeIn>
        )}

        <div ref={messagesEndRef} className="h-20" />
      </StaggerContainer>

      {/* Input Area - Floating Pill */}
      <div className="absolute bottom-6 left-6 right-6 z-20">
        <motion.div
          animate={{
            y: isFocused ? -4 : 0,
            scale: isFocused ? 1.01 : 1,
          }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        >
          <GlassPanel 
            intensity="heavy" 
            className={`p-1.5 flex items-center gap-2 border-white/10 shadow-2xl transition-all duration-500 ${
              isFocused ? 'ring-1 ring-accent-blue/30 shadow-blue-500/10' : ''
            }`}
          >
            <div className="flex items-center">
              <motion.button
                whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                whileTap={{ scale: 0.95 }}
                className="p-3 rounded-xl text-foreground-tertiary hover:text-foreground-secondary transition-colors"
              >
                <Plus size={20} />
              </motion.button>
            </div>

            <input
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
              placeholder="Message ATLAS..."
              className="flex-1 bg-transparent border-none focus:ring-0 text-foreground-primary placeholder-foreground-tertiary/50 py-3 text-sm font-medium outline-none"
            />

            <div className="flex items-center gap-1 pr-1">
              <motion.button
                whileHover={{ backgroundColor: 'rgba(255,255,255,0.05)' }}
                whileTap={{ scale: 0.95 }}
                className="p-3 rounded-xl text-foreground-tertiary hover:text-foreground-secondary transition-colors"
              >
                <Paperclip size={18} />
              </motion.button>
              
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={handleSendMessage}
                disabled={!inputValue.trim() || isLoading}
                className="p-3 rounded-xl bg-accent-blue text-white shadow-lg shadow-blue-500/20 disabled:opacity-50 disabled:grayscale transition-all"
              >
                <Send size={18} />
              </motion.button>
            </div>
          </GlassPanel>
        </motion.div>
      </div>
    </div>
  );
}
