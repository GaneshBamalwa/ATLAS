import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const components = {
  h1: ({ children }: any) => <h1 style={{ fontSize: '1.5em', fontWeight: 'bold', margin: '16px 0 12px 0' }}>{children}</h1>,
  h2: ({ children }: any) => <h2 style={{ fontSize: '1.25em', fontWeight: 'bold', margin: '12px 0 8px 0' }}>{children}</h2>,
  p: ({ children }: any) => <p style={{ margin: '8px 0' }}>{children}</p>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
  blockquote: ({ children }: any) => (
    <blockquote style={{ borderLeft: '3px solid #666', paddingLeft: '12px', margin: '8px 0', fontStyle: 'italic', color: '#aaa' }}>
      {children}
    </blockquote>
  ),
  code: ({ inline, children }: any) => {
    if (inline) {
      return <code style={{ background: '#333', padding: '2px 6px', borderRadius: '3px', fontFamily: 'monospace' }}>{children}</code>;
    }
    return <pre style={{ background: '#1a1a1a', padding: '12px', borderRadius: '4px', margin: '8px 0', overflow: 'auto' }}><code>{children}</code></pre>;
  },
};

export default function MarkdownTest() {
  const testMarkdown = `# Email Sent Successfully

The email was sent successfully with the details below:

**To:** ganeshbamalwa89@gmail.com
**Subject:** Test Email
**Message ID:** \`19dda4741484cf23\`

## Body Preview

> This is a test blockquote
> It spans multiple lines
> And should be properly formatted`;

  return (
    <div style={{ padding: '20px', maxWidth: '600px', color: '#fff', whiteSpace: 'normal', wordWrap: 'break-word' }}>
      <h3>Markdown Test Component</h3>
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {testMarkdown}
      </ReactMarkdown>
    </div>
  );
}
