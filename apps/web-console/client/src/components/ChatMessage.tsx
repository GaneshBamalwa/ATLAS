import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dark } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface ChatMessageProps {
  message: string;
  isUser: boolean;
}

const markdownComponents = {
  h1: ({ children, ...props }: React.ComponentProps<'h1'>) => (
    <h1 {...props} className="mb-2 mt-3 text-lg font-semibold tracking-tight text-foreground first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children, ...props }: React.ComponentProps<'h2'>) => (
    <h2 {...props} className="mb-2 mt-3 text-base font-semibold tracking-tight text-foreground first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children, ...props }: React.ComponentProps<'h3'>) => (
    <h3 {...props} className="mb-1 mt-3 text-sm font-semibold tracking-tight text-foreground first:mt-0">
      {children}
    </h3>
  ),
  ul: ({ children, ...props }: React.ComponentProps<'ul'>) => (
    <ul {...props} className="my-2 ml-5 list-disc space-y-1 text-foreground/90">
      {children}
    </ul>
  ),
  ol: ({ children, ...props }: React.ComponentProps<'ol'>) => (
    <ol {...props} className="my-2 ml-5 list-decimal space-y-1 text-foreground/90">
      {children}
    </ol>
  ),
  li: ({ children, ...props }: React.ComponentProps<'li'>) => (
    <li {...props} className="leading-7 text-foreground/90">
      {children}
    </li>
  ),
  p: ({ children, ...props }: React.ComponentProps<'p'>) => (
    <p {...props} className="my-2 leading-7 text-foreground/90 first:mt-0 last:mb-0">
      {children}
    </p>
  ),
  blockquote: ({ children, ...props }: React.ComponentProps<'blockquote'>) => (
    <blockquote {...props} className="my-2 border-l-4 border-white/15 pl-4 italic text-foreground/70">
      {children}
    </blockquote>
  ),
  table: ({ children, ...props }: React.ComponentProps<'table'>) => (
    <div className="my-4 overflow-x-auto rounded-xl border border-white/10">
      <table {...props} className="min-w-full border-collapse text-sm text-foreground/90">
        {children}
      </table>
    </div>
  ),
  th: ({ children, ...props }: React.ComponentProps<'th'>) => (
    <th {...props} className="border-b border-white/10 bg-white/5 px-3 py-2 text-left font-semibold text-foreground">
      {children}
    </th>
  ),
  td: ({ children, ...props }: React.ComponentProps<'td'>) => (
    <td {...props} className="border-b border-white/10 px-3 py-2 align-top text-foreground/90">
      {children}
    </td>
  ),
  code: ({ inline, className, children, ...props }: React.ComponentProps<'code'> & { inline?: boolean }) => {
    const match = /language-(\w+)/.exec(className || '');

    if (!inline && match) {
      return (
        <SyntaxHighlighter
          {...props}
          language={match[1]}
          style={dark}
          PreTag="div"
          customStyle={{
            margin: '10px 0',
            borderRadius: '12px',
            padding: '14px',
            background: '#0f172a',
            fontSize: '0.8125rem',
            lineHeight: '1.5',
          }}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      );
    }

    return (
      <code
        {...props}
        className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-[0.92em] text-foreground"
      >
        {children}
      </code>
    );
  },
};

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, isUser }) => {
  if (isUser) {
    return <div className="whitespace-pre-wrap text-sm leading-7 text-foreground">{message}</div>;
  }

  return (
    <div className="chat-message assistant prose prose-invert max-w-none prose-headings:scroll-mt-2 prose-p:my-2 prose-ul:my-2 prose-ol:my-2 prose-li:my-1 prose-blockquote:my-2">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={markdownComponents}>
        {message}
      </ReactMarkdown>
    </div>
  );
};
