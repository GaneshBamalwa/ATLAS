import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, X, CheckCircle, Clock, AlertCircle, Zap, Terminal } from 'lucide-react';
import { useState } from 'react';
import { GlassPanel } from '@/ui/primitives/GlassPanel';
import { GlassCard } from '@/ui/primitives/GlassCard';
import { FadeIn, StaggerContainer } from '@/ui/animations/LayoutTransition';

interface ExecutionStep {
  id: string;
  tool: string;
  status: 'pending' | 'running' | 'completed' | 'error';
  startTime: Date;
  endTime?: Date;
  details?: string;
  result?: string;
}

interface ExecutionTracePanelProps {
  onToggle: () => void;
}

export default function ExecutionTracePanel({ onToggle }: ExecutionTracePanelProps) {
  const [expandedStep, setExpandedStep] = useState<string | null>(null);
  const [steps] = useState<ExecutionStep[]>([
    {
      id: '1',
      tool: 'Gmail Fetch',
      status: 'completed',
      startTime: new Date(Date.now() - 5000),
      endTime: new Date(Date.now() - 4000),
      details: 'Retrieved 42 emails from inbox',
      result: '42 emails fetched successfully',
    },
    {
      id: '2',
      tool: 'Memory Service',
      status: 'running',
      startTime: new Date(Date.now() - 3000),
      details: 'Analyzing email content and extracting context',
    },
    {
      id: '3',
      tool: 'Google Drive',
      status: 'pending',
      startTime: new Date(),
      details: 'Waiting to execute',
    },
  ]);

  const getStatusIcon = (status: ExecutionStep['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={14} className="text-accent-green" />;
      case 'running':
        return <Zap size={14} className="text-accent-purple animate-pulse" />;
      case 'error':
        return <AlertCircle size={14} className="text-accent-red" />;
      default:
        return <Clock size={14} className="text-foreground-tertiary" />;
    }
  };

  return (
    <div className="h-full flex flex-col relative">
      {/* Header */}
      <div className="p-6 border-b border-white/5 bg-white/[0.02] backdrop-blur-md z-10 sticky top-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-white/5 flex items-center justify-center border border-white/10">
              <Terminal size={16} className="text-foreground-secondary" />
            </div>
            <div>
              <h2 className="text-sm font-display tracking-tight text-foreground-primary">Trace Engine</h2>
              <p className="text-[10px] uppercase tracking-widest text-foreground-tertiary font-bold mt-0.5">Real-time Stream</p>
            </div>
          </div>
          <button 
            onClick={onToggle}
            className="p-2 rounded-lg hover:bg-white/5 text-foreground-tertiary transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      {/* Main Stream Area */}
      <StaggerContainer className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
        {steps.map((step, index) => (
          <FadeIn key={step.id}>
            <div className="relative group">
              {/* Timeline Connector */}
              {index < steps.length - 1 && (
                <div className="absolute left-[13px] top-8 bottom-[-24px] w-0.5 bg-gradient-to-b from-white/10 via-white/5 to-transparent" />
              )}
              
              <div className="flex gap-6">
                {/* Node Indicator */}
                <div className="relative flex-shrink-0 z-10">
                  <motion.div 
                    initial={false}
                    animate={{
                      scale: step.status === 'running' ? [1, 1.3, 1] : 1,
                      backgroundColor: step.status === 'completed' ? 'var(--accent-green)' : step.status === 'running' ? 'var(--accent-purple)' : 'transparent'
                    }}
                    className={`w-[26px] h-[26px] rounded-full border-2 border-white/10 flex items-center justify-center bg-depth-bg-secondary ${
                      step.status === 'running' ? 'shadow-[0_0_15px_rgba(191,90,242,0.4)]' : ''
                    }`}
                  >
                    {getStatusIcon(step.status)}
                  </motion.div>
                </div>

                {/* Step Content Card */}
                <div className="flex-1 min-w-0">
                  <GlassCard 
                    onClick={() => setExpandedStep(expandedStep === step.id ? null : step.id)}
                    className={`p-4 border-white/5 transition-all duration-500 cursor-pointer ${
                      expandedStep === step.id ? 'ring-1 ring-white/10 bg-white/10 shadow-2xl' : 'hover:bg-white/5'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="min-w-0">
                        <h4 className={`text-[13px] font-black uppercase tracking-widest transition-colors duration-300 ${
                          step.status === 'running' ? 'text-accent-purple' : 'text-foreground-primary'
                        }`}>
                          {step.tool}
                        </h4>
                        <p className="text-[11px] text-foreground-tertiary font-medium mt-1 leading-relaxed">
                          {step.details}
                        </p>
                      </div>
                      <ChevronDown 
                        size={14} 
                        className={`text-foreground-tertiary transition-transform duration-300 mt-1 ${expandedStep === step.id ? 'rotate-180' : ''}`}
                      />
                    </div>

                    <AnimatePresence>
                      {expandedStep === step.id && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: 'auto', opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden mt-4 pt-4 border-t border-white/5 space-y-4"
                        >
                          {step.result && (
                            <div className="space-y-2">
                              <p className="text-[10px] uppercase tracking-widest font-black text-accent-blue/60">Output Result</p>
                              <div className="bg-black/40 rounded-xl p-3 border border-white/5 font-code text-[11px] text-accent-cyan break-all leading-relaxed shadow-inner">
                                {step.result}
                              </div>
                            </div>
                          )}
                          
                          <div className="flex items-center gap-6">
                            <div>
                              <p className="text-[9px] uppercase tracking-widest font-black text-foreground-tertiary">Started At</p>
                              <p className="text-[11px] font-bold text-foreground-secondary mt-0.5">{step.startTime.toLocaleTimeString()}</p>
                            </div>
                            {step.endTime && (
                              <div>
                                <p className="text-[9px] uppercase tracking-widest font-black text-foreground-tertiary">Completed At</p>
                                <p className="text-[11px] font-bold text-foreground-secondary mt-0.5">{step.endTime.toLocaleTimeString()}</p>
                              </div>
                            )}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </GlassCard>
                </div>
              </div>
            </div>
          </FadeIn>
        ))}
      </StaggerContainer>

      {/* Summary Footer Statistics */}
      <div className="p-6 border-t border-white/5 bg-white/[0.02]">
        <div className="grid grid-cols-3 gap-3">
          {[
            { label: 'Completed', val: steps.filter(s => s.status === 'completed').length, color: 'text-accent-green' },
            { label: 'Processes', val: steps.filter(s => s.status === 'running').length, color: 'text-accent-purple' },
            { label: 'Queued', val: steps.filter(s => s.status === 'pending').length, color: 'text-foreground-tertiary' }
          ].map((stat) => (
            <div key={stat.label} className="bg-white/5 rounded-2xl p-3 border border-white/5 text-center shadow-inner">
              <p className="text-[10px] uppercase tracking-widest font-black text-foreground-tertiary mb-1">{stat.label}</p>
              <p className={`text-lg font-display tracking-tight ${stat.color}`}>{stat.val}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
