import { Handle, Position } from '@xyflow/react';
import { motion } from 'framer-motion';
import { GitBranch, Activity, Database, CheckCircle2, AlertCircle } from 'lucide-react';

export const CustomNode = ({ data }: any) => {
  const isRunning = data.status === 'running';
  const isSuccess = data.status === 'success' || data.status === 'completed';
  const isFailed = data.status === 'failed' || data.status === 'error';

  return (
    <div className="relative group p-[1px] rounded-3xl overflow-hidden shadow-2xl">
      {/* Dynamic Glow Border */}
      <div className={`absolute inset-0 transition-opacity duration-1000 ${
        isRunning ? 'opacity-100' : 'opacity-40 group-hover:opacity-80'
      } bg-gradient-to-br ${
        isSuccess ? 'from-accent-green/40 to-transparent' :
        isRunning ? 'from-accent-blue/40 to-transparent animate-pulse' :
        isFailed ? 'from-accent-red/40 to-transparent' :
        'from-white/10 to-transparent'
      }`} />

      <div className="relative glass-heavy rounded-3xl p-6 min-w-[280px] border border-white/[0.05] flex items-center gap-6">
        <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-accent-blue !border-none" />
        
        <div className={`w-14 h-14 rounded-2xl flex items-center justify-center border transition-all duration-500 ${
          isSuccess ? 'bg-accent-green/10 border-accent-green/20 text-accent-green' :
          isRunning ? 'bg-accent-blue/10 border-accent-blue/40 text-accent-blue shadow-[0_0_20px_rgba(0,122,255,0.3)]' :
          isFailed ? 'bg-accent-red/10 border-accent-red/20 text-accent-red' :
          'bg-white/5 border-white/10 text-white/20'
        }`}>
           {isSuccess ? <CheckCircle2 size={24} /> :
            isRunning ? <Activity size={24} className="animate-spin-slow" /> :
            isFailed ? <AlertCircle size={24} /> :
            <Database size={24} />}
        </div>

        <div className="flex-1 space-y-1">
           <span className="text-[8px] uppercase tracking-[0.3em] font-black text-white/20 block">
              {data.node_type || 'Operation'}
           </span>
           <h3 className="text-sm font-display text-white tracking-tight leading-tight">{data.node_name || 'Processing...'}</h3>
           {data.latency_ms && (
             <span className="text-[9px] font-mono text-accent-blue/60">{data.latency_ms.toFixed(0)}ms</span>
           )}
        </div>

        <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-accent-purple !border-none" />
      </div>
    </div>
  );
};
