import { CheckCheck, Clock, AlertCircle } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { PipelineGraph } from './PipelineGraph';

interface MessageBubbleProps {
  message: {
    id: string;
    type: 'user' | 'ai';
    content: string;
    timestamp: Date;
    status?: 'sending' | 'sent' | 'error';
    tools?: string[];
    pipeline?: {
      nodes: { id: string; label: string; status: string; duration: number; error?: string }[];
      edges: { source: string; target: string; type: string }[];
      execution_time_ms: number;
    };
  };
  index: number;
}

// Minimal custom components for markdown
const components = {
  h1: ({ children }: any) => <h1 style={{ fontSize: '1.8em', fontWeight: 'bold', margin: '20px 0 12px 0' }}>{children}</h1>,
  h2: ({ children }: any) => <h2 style={{ fontSize: '1.4em', fontWeight: 'bold', margin: '16px 0 8px 0' }}>{children}</h2>,
  h3: ({ children }: any) => <h3 style={{ fontSize: '1.2em', fontWeight: 'bold', margin: '12px 0 4px 0' }}>{children}</h3>,
  p: ({ children }: any) => <p style={{ margin: '8px 0' }}>{children}</p>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
  em: ({ children }: any) => <em style={{ fontStyle: 'italic' }}>{children}</em>,
  blockquote: ({ children }: any) => (
    <blockquote style={{ borderLeft: '4px solid #4a9eff', paddingLeft: '16px', margin: '12px 0', color: '#bbb', fontStyle: 'italic' }}>
      {children}
    </blockquote>
  ),
  code: ({ inline, children }: any) => {
    if (inline) {
      return <code style={{ background: '#2a2a2a', padding: '2px 6px', borderRadius: '3px', fontFamily: 'monospace', fontSize: '0.9em', color: '#e0e0e0' }}>{children}</code>;
    }
    return (
      <pre style={{ background: '#1a1a1a', padding: '12px', borderRadius: '4px', margin: '8px 0', overflow: 'auto' }}>
        <code style={{ fontFamily: 'monospace', fontSize: '0.85em', color: '#e0e0e0' }}>{children}</code>
      </pre>
    );
  },
  ul: ({ children }: any) => <ul style={{ marginLeft: '24px', margin: '8px 0' }}>{children}</ul>,
  ol: ({ children }: any) => <ol style={{ marginLeft: '24px', margin: '8px 0' }}>{children}</ol>,
  li: ({ children }: any) => <li style={{ margin: '4px 0' }}>{children}</li>,
  a: ({ href, children }: any) => <a href={href} style={{ color: '#4a9eff', textDecoration: 'underline', cursor: 'pointer' }}>{children}</a>,
};

export default function MessageBubble({ message, index }: MessageBubbleProps) {
  const isUser = message.type === 'user';

  // DEBUG: Check what the component receives
  if (message.type === 'ai' && message.content.length > 50) {
    console.log("=== MESSAGEBUBBLE RECEIVED ===");
    console.log("Content length:", message.content.length);
    console.log("Has newlines:", message.content.includes('\n'));
    console.log("Newline count:", (message.content.match(/\n/g) || []).length);
    console.log("First 200 chars (JSON):", JSON.stringify(message.content.substring(0, 200)));
    if (message.content.includes('Email')) {
      console.log("Contains Email: YES");
    }
    console.log("============================");
  }

  const statusIcon = {
    sending: <Clock size={12} className="text-muted-foreground animate-spin" />,
    sent: <CheckCheck size={12} className="text-primary" />,
    error: <AlertCircle size={12} className="text-destructive" />,
  };

  return (
    <div className="group flex w-full gap-4 border-b border-white/5 py-4 last:border-0">
      <div className="w-16 shrink-0 text-[10px] uppercase tracking-[0.28em] text-muted-foreground">
        {isUser ? 'You' : 'Atlas'}
      </div>
      <div className="min-w-0 flex-1">
        <div className={`border-l pl-4 ${isUser ? 'border-primary/50' : 'border-white/10'}`}>
          {/* Pipeline graph (AI messages only) */}
          {!isUser && message.pipeline && message.pipeline.nodes.length > 0 && (
            <PipelineGraph pipeline={message.pipeline as any} />
          )}

          {/* CRITICAL: Raw markdown passed directly to ReactMarkdown */}
          <div style={{ fontSize: '0.875rem', lineHeight: '1.6', color: '#fff' }}>
            <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
              {message.content}
            </ReactMarkdown>
          </div>

          <div className="mt-3 flex items-center gap-3 text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
            <span>
              {message.timestamp.toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit',
              })}
            </span>
            {message.status && <span className="opacity-70">{message.status}</span>}
            {message.status && <span>{statusIcon[message.status as keyof typeof statusIcon]}</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
