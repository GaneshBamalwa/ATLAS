import MessageBubble from '@/components/MessageBubble';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

// Minimal components for testing
const testComponents = {
  h1: ({ children }: any) => <h1 style={{ fontSize: '1.5em', fontWeight: 'bold', margin: '16px 0 12px 0' }}>{children}</h1>,
  h2: ({ children }: any) => <h2 style={{ fontSize: '1.25em', fontWeight: 'bold', margin: '12px 0 8px 0' }}>{children}</h2>,
  p: ({ children }: any) => <p style={{ margin: '8px 0' }}>{children}</p>,
  strong: ({ children }: any) => <strong style={{ fontWeight: 'bold' }}>{children}</strong>,
  blockquote: ({ children }: any) => (
    <blockquote style={{ borderLeft: '3px solid #666', paddingLeft: '12px', margin: '8px 0', fontStyle: 'italic', color: '#aaa' }}>
      {children}
    </blockquote>
  ),
};

export default function MarkdownDebugPage() {
  // === BYPASS TEST (STEP 4) ===
  const testMarkdown = `# Heading

**Bold Text**

## Section

> Blockquote works`;

  console.log("=== BYPASS TEST HARDCODED MARKDOWN ===");
  console.log(testMarkdown);
  console.log("=== BYPASS TEST REPR ===");
  console.log(JSON.stringify(testMarkdown));

  return (
    <div style={{ padding: '20px', maxWidth: '800px', color: '#fff' }}>
      <h2>Step 4: Bypass Test (Hardcoded Markdown)</h2>
      <p>If below renders with heading, bold, blockquote → ReactMarkdown works</p>
      <div style={{ whiteSpace: 'normal', wordWrap: 'break-word', border: '1px solid #666', padding: '10px', margin: '20px 0' }}>
        <ReactMarkdown remarkPlugins={[remarkGfm]} components={testComponents}>
          {testMarkdown}
        </ReactMarkdown>
      </div>

      <h2>Existing Messages Test</h2>
      <p>Check console for FRONTEND RAW MESSAGE output</p>
      
      {/* Test with actual message */}
      <div style={{ border: '1px solid #ccc', padding: '10px', margin: '20px 0' }}>
        <MessageBubble 
          message={{
            id: '1',
            type: 'ai',
            content: `# Email Sent Successfully

The email was sent successfully with the details below:

**To:** ganeshbamalwa89@gmail.com
**Subject:** Best Wishes
**Message ID:** \`19dda4741484cf23\`

## Body Preview

> Hi Ganesh, this is a reminder.`,
            timestamp: new Date(),
          }}
          index={0}
        />
      </div>
    </div>
  );
}
