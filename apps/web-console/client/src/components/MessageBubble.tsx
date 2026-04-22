import { motion } from 'framer-motion';
import { CheckCheck, Clock, AlertCircle } from 'lucide-react';
import { GlassPanel } from '@/ui/primitives/GlassPanel';

import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface MessageBubbleProps {
  message: {
    id: string;
    type: 'user' | 'ai';
    content: string;
    timestamp: Date;
    status?: 'sending' | 'sent' | 'error';
    tools?: string[];
  };
  index: number;
}

export default function MessageBubble({ message, index }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  const statusIcon = {
    sending: <Clock size={12} className="text-foreground-tertiary animate-spin" />,
    sent: <CheckCheck size={12} className="text-accent-blue shadow-blue-500/20" />,
    error: <AlertCircle size={12} className="text-accent-red" />,
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} w-full group`}>
      <GlassPanel
        intensity={isUser ? 'heavy' : 'light'}
        className={`max-w-[85%] lg:max-w-[70%] px-5 py-4 shadow-xl border-white/5 transition-all duration-300 ${
          isUser
            ? 'rounded-3xl rounded-tr-sm bg-gradient-to-br from-white/10 to-transparent'
            : 'rounded-3xl rounded-tl-sm bg-white/5'
        }`}
      >
        <div className="text-sm font-medium text-foreground-primary leading-relaxed antialiased prose prose-invert prose-p:my-1 prose-ul:my-1 prose-li:my-0">
          <ReactMarkdown remarkPlugins={[remarkGfm]}>
            {message.content}
          </ReactMarkdown>
        </div>

        {/* Metadata section */}
        <div className="mt-3 flex items-center justify-between gap-4 opacity-40 group-hover:opacity-100 transition-opacity duration-300">
          <span className="text-[10px] uppercase tracking-widest font-bold text-foreground-tertiary">
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </span>
          <div className="flex items-center gap-1">
            {message.status && statusIcon[message.status as keyof typeof statusIcon]}
          </div>
        </div>
      </GlassPanel>
    </div>
  );
}
