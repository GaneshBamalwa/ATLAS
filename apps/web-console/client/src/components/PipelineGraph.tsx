import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle2, AlertCircle, Clock, ChevronRight, Zap } from 'lucide-react';
import type { PipelineData } from '@/contexts/ChatContext';

interface PipelineGraphProps {
  pipeline: PipelineData;
}

export const PipelineGraph: React.FC<PipelineGraphProps> = ({ pipeline }) => {
  const [expanded, setExpanded] = useState(false);
  const { nodes, edges, execution_time_ms } = pipeline;

  if (!nodes || nodes.length === 0) return null;

  const successCount = nodes.filter((n) => n.status === 'success').length;
  const errorCount   = nodes.filter((n) => n.status === 'error').length;

  const statusStyles = {
    success: {
      bg: 'rgba(48,209,88,0.08)',
      border: 'rgba(48,209,88,0.25)',
      dot: '#30D158',
      text: '#30D158',
    },
    error: {
      bg: 'rgba(255,69,58,0.08)',
      border: 'rgba(255,69,58,0.25)',
      dot: '#FF453A',
      text: '#FF453A',
    },
    pending: {
      bg: 'rgba(255,255,255,0.03)',
      border: 'rgba(255,255,255,0.08)',
      dot: 'rgba(255,255,255,0.3)',
      text: 'rgba(255,255,255,0.35)',
    },
  };

  const StatusIcon = ({ status }: { status: string }) => {
    const sz = 11;
    switch (status) {
      case 'success': return <CheckCircle2 size={sz} style={{ color: '#30D158', flexShrink: 0 }} />;
      case 'error':   return <AlertCircle  size={sz} style={{ color: '#FF453A', flexShrink: 0 }} />;
      default:        return <Clock        size={sz} style={{ color: 'rgba(255,255,255,0.3)', flexShrink: 0 }} />;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: 'easeOut' }}
      onClick={() => setExpanded((p) => !p)}
      style={{
        background: 'rgba(0,122,255,0.04)',
        border: '1px solid rgba(0,122,255,0.12)',
        borderRadius: '14px',
        padding: '10px 14px',
        marginBottom: '10px',
        cursor: 'pointer',
        userSelect: 'none',
      }}
    >
      {/* ── Header row ── */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '7px' }}>
          <Zap size={11} style={{ color: '#007AFF' }} />
          <span style={{
            fontSize: '9px', fontWeight: 900, letterSpacing: '0.22em',
            textTransform: 'uppercase', color: 'rgba(0,122,255,0.85)',
          }}>
            Execution Pipeline
          </span>
          <span style={{
            fontSize: '9px', color: 'rgba(255,255,255,0.22)',
            letterSpacing: '0.08em',
          }}>
            {nodes.length} tool{nodes.length !== 1 ? 's' : ''}
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {successCount > 0 && (
            <span style={{ fontSize: '9px', color: '#30D158', fontWeight: 800, letterSpacing: '0.05em' }}>
              {successCount} ✓
            </span>
          )}
          {errorCount > 0 && (
            <span style={{ fontSize: '9px', color: '#FF453A', fontWeight: 800, letterSpacing: '0.05em' }}>
              {errorCount} ✗
            </span>
          )}
          {execution_time_ms > 0 && (
            <span style={{ fontSize: '9px', color: 'rgba(255,255,255,0.22)', fontFamily: 'monospace' }}>
              {execution_time_ms.toFixed(0)}ms
            </span>
          )}
          <motion.div
            animate={{ rotate: expanded ? 90 : 0 }}
            transition={{ duration: 0.18 }}
          >
            <ChevronRight size={12} style={{ color: 'rgba(255,255,255,0.2)' }} />
          </motion.div>
        </div>
      </div>

      {/* ── Always-visible compact chip row ── */}
      <div style={{
        display: 'flex', alignItems: 'center', flexWrap: 'wrap',
        gap: '4px', marginTop: '9px',
      }}>
        {nodes.map((node, idx) => {
          const s = statusStyles[node.status as keyof typeof statusStyles] ?? statusStyles.pending;
          return (
            <React.Fragment key={node.id}>
              <div style={{
                display: 'flex', alignItems: 'center', gap: '5px',
                background: s.bg,
                border: `1px solid ${s.border}`,
                borderRadius: '8px',
                padding: '3px 8px',
              }}>
                <div style={{
                  width: 5, height: 5, borderRadius: '50%',
                  background: s.dot, flexShrink: 0,
                }} />
                <span style={{
                  fontSize: '10px', fontWeight: 600,
                  color: 'rgba(255,255,255,0.8)', whiteSpace: 'nowrap',
                }}>
                  {node.label}
                </span>
              </div>
              {idx < nodes.length - 1 && (
                <ChevronRight size={10} style={{ color: 'rgba(255,255,255,0.12)', flexShrink: 0 }} />
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ── Expanded details ── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            key="details"
            initial={{ opacity: 0, height: 0, marginTop: 0 }}
            animate={{ opacity: 1, height: 'auto', marginTop: 10 }}
            exit={{ opacity: 0, height: 0, marginTop: 0 }}
            transition={{ duration: 0.2, ease: 'easeOut' }}
            style={{ overflow: 'hidden' }}
          >
            <div style={{
              borderTop: '1px solid rgba(255,255,255,0.05)',
              paddingTop: '10px',
              display: 'flex',
              flexDirection: 'column',
              gap: '6px',
            }}>
              {nodes.map((node) => {
                const s = statusStyles[node.status as keyof typeof statusStyles] ?? statusStyles.pending;
                return (
                  <div key={node.id} style={{
                    display: 'flex', alignItems: 'flex-start', gap: '8px',
                    background: s.bg,
                    border: `1px solid ${s.border}`,
                    borderRadius: '10px',
                    padding: '7px 10px',
                  }}>
                    <StatusIcon status={node.status} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                        <span style={{
                          fontSize: '11px', fontWeight: 700,
                          color: 'rgba(255,255,255,0.85)',
                        }}>
                          {node.label}
                        </span>
                        {node.duration > 0 && (
                          <span style={{
                            fontSize: '9px', fontFamily: 'monospace',
                            color: 'rgba(255,255,255,0.25)', flexShrink: 0,
                          }}>
                            {node.duration.toFixed(0)}ms
                          </span>
                        )}
                      </div>
                      {node.error && (
                        <p style={{
                          fontSize: '10px', color: '#FF453A',
                          marginTop: '3px', lineHeight: 1.4,
                          overflow: 'hidden', textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical' as const,
                        }}>
                          {node.error}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}

              {/* Dependency edges (only "dependency" type edges) */}
              {edges.filter((e) => e.type === 'dependency').length > 0 && (
                <div style={{ marginTop: '4px' }}>
                  <p style={{
                    fontSize: '8px', fontWeight: 900, textTransform: 'uppercase',
                    letterSpacing: '0.2em', color: 'rgba(255,255,255,0.2)',
                    marginBottom: '4px',
                  }}>
                    Data Dependencies
                  </p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {edges
                      .filter((e) => e.type === 'dependency')
                      .map((e, i) => (
                        <span key={i} style={{
                          fontSize: '9px', fontFamily: 'monospace',
                          color: 'rgba(0,122,255,0.7)',
                          background: 'rgba(0,122,255,0.06)',
                          border: '1px solid rgba(0,122,255,0.15)',
                          borderRadius: '6px',
                          padding: '2px 7px',
                        }}>
                          {e.source} → {e.target}
                        </span>
                      ))}
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};
