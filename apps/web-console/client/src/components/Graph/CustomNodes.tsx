import { useState, useRef, useEffect } from 'react';
import { Handle, Position } from '@xyflow/react';
import { motion } from 'framer-motion';
import { GitBranch, Activity, Database, CheckCircle2, AlertCircle, Clock, Terminal, ChevronRight } from 'lucide-react';

export const CustomNode = ({ data }: any) => {
  const isRunning = data.status === 'running';
  const isSuccess = data.status === 'success' || data.status === 'completed';
  const isFailed = data.status === 'failed' || data.status === 'error';

  const [isLocked, setIsLocked] = useState(false);
  const nodeRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (nodeRef.current && !nodeRef.current.contains(event.target as Node)) {
        setIsLocked(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleNodeClick = (e: React.MouseEvent) => {
    // Avoid double toggling if clicking inside the details container itself
    const target = e.target as HTMLElement;
    if (target.closest('.details-tooltip')) {
      return;
    }
    setIsLocked((prev) => !prev);
  };

  return (
    <div 
      ref={nodeRef}
      onClick={handleNodeClick}
      className="relative group p-[1px] rounded-2xl overflow-visible shadow-2xl transition-all duration-300 hover:scale-[1.03]"
    >
      {/* Dynamic Glow Border */}
      <div className={`absolute inset-0 rounded-2xl transition-opacity duration-500 ${
        isRunning ? 'opacity-100' : 'opacity-20 group-hover:opacity-60'
      } bg-gradient-to-br ${
        isSuccess ? 'from-accent-green/30 to-transparent' :
        isRunning ? 'from-accent-blue/30 to-transparent animate-pulse' :
        isFailed ? 'from-accent-red/30 to-transparent' :
        'from-white/5 to-transparent'
      }`} />

      {/* Compact Main Node */}
      <div className="relative glass-heavy rounded-2xl p-3 w-[220px] border border-white/[0.05] flex items-center gap-3 cursor-pointer">
        <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-accent-blue !border-none !opacity-80" />
        
        {/* Status Indicator Icon */}
        <div className={`w-9 h-9 rounded-xl flex items-center justify-center border transition-all duration-500 flex-shrink-0 ${
          isSuccess ? 'bg-accent-green/10 border-accent-green/20 text-accent-green' :
          isRunning ? 'bg-accent-blue/10 border-accent-blue/40 text-accent-blue shadow-[0_0_15px_rgba(0,122,255,0.3)] animate-pulse' :
          isFailed ? 'bg-accent-red/10 border-accent-red/20 text-accent-red' :
          'bg-white/5 border-white/10 text-white/40'
        }`}>
          {isSuccess ? <CheckCircle2 size={16} /> :
           isRunning ? <Activity size={16} className="animate-spin-slow" /> :
           isFailed ? <AlertCircle size={16} /> :
           <Database size={16} />}
        </div>

        {/* Small Label & Info */}
        <div className="flex-1 min-w-0 flex flex-col justify-center">
           <span className="text-[7px] uppercase tracking-[0.2em] font-black text-white/30 block truncate">
              {data.node_type === "dag_node" ? (data.tool_name || "TOOL") : (data.node_type || 'Operation')}
           </span>
           <h3 className="text-xs font-semibold font-display text-white/90 tracking-tight leading-none truncate mt-0.5">
             {data.label || data.node_name || 'Processing...'}
           </h3>
           <div className="flex items-center gap-1.5 mt-1">
             <div className={`w-1.5 h-1.5 rounded-full ${
               isSuccess ? 'bg-accent-green' :
               isRunning ? 'bg-accent-blue animate-pulse' :
               isFailed ? 'bg-accent-red' : 'bg-white/20'
             }`} />
             <span className="text-[8px] font-mono text-white/40 truncate">
               {isRunning ? 'Executing...' : 
                isSuccess ? (data.latency_ms ? `${data.latency_ms.toFixed(0)}ms` : 'Success') : 
                isFailed ? 'Failed' : 'Pending'}
             </span>
           </div>
        </div>

        {/* Hover/Click Execution Details Tooltip */}
        <div 
          className={`details-tooltip absolute left-full ml-4 top-1/2 -translate-y-1/2 flex flex-col w-[320px] glass-heavy p-4 rounded-2xl border border-white/10 shadow-[0_20px_50px_rgba(0,0,0,0.6)] backdrop-blur-xl z-50 animate-in fade-in slide-in-from-left-2 duration-200 ${
            isLocked ? 'flex pointer-events-auto' : 'hidden group-hover:flex pointer-events-none'
          }`}
        >
             {/* Header */}
             <div className="flex items-start justify-between gap-4 pb-3 border-b border-white/10">
                 <div className="min-w-0">
                     <span className="text-[8px] uppercase tracking-[0.3em] font-black text-accent-cyan block">
                         {data.node_type === "dag_node" ? `Tool: ${data.tool_name}` : (data.node_type || 'Operation')}
                     </span>
                     <h4 className="text-sm font-display font-semibold text-white truncate mt-1">
                         {data.label || data.node_name}
                     </h4>
                 </div>
                 <span className={`text-[8px] px-2 py-0.5 rounded-full uppercase tracking-wider font-bold border ${
                     isSuccess ? 'bg-accent-green/10 border-accent-green/20 text-accent-green' :
                     isRunning ? 'bg-accent-blue/10 border-accent-blue/20 text-accent-blue' :
                     isFailed ? 'bg-accent-red/10 border-accent-red/20 text-accent-red' :
                     'bg-white/5 border-white/10 text-white/40'
                 }`}>
                     {data.status || 'pending'}
                 </span>
             </div>

             {/* Timing Details */}
             <div className="flex flex-col gap-1.5 my-3 text-[10px] text-white/60">
                 <div className="flex items-center gap-2">
                     <Clock size={12} className="text-white/40" />
                     <span>Duration:</span>
                     <span className="font-mono text-accent-blue font-bold ml-auto">
                         {data.latency_ms ? `${data.latency_ms.toFixed(1)}ms` : 'N/A'}
                     </span>
                 </div>
                 {(data.start_time || data.end_time) && (
                     <div className="flex flex-col gap-1 pl-5 border-l border-white/5 text-[9px] text-white/40">
                         {data.start_time && (
                             <div className="flex justify-between">
                                 <span>Started:</span>
                                 <span className="font-mono">{new Date(data.start_time).toLocaleTimeString()}</span>
                             </div>
                         )}
                         {data.end_time && (
                             <div className="flex justify-between">
                                 <span>Completed:</span>
                                 <span className="font-mono">{new Date(data.end_time).toLocaleTimeString()}</span>
                             </div>
                         )}
                     </div>
                 )}
             </div>

             {/* Inputs / Parameters */}
             {data.inputs && Object.keys(data.inputs).length > 0 && (
                 <div className="mt-2 text-left">
                     <span className="text-[9px] text-white/40 uppercase font-black tracking-widest block mb-1">Inputs</span>
                     <pre className="text-[10px] text-accent-cyan/90 bg-black/40 p-2.5 rounded-xl border border-white/5 overflow-x-auto max-h-32 scrollbar-thin">
                         {JSON.stringify(data.inputs, null, 2)}
                     </pre>
                 </div>
             )}

             {/* Outputs / Results */}
             {data.outputs && (
                 <div className="mt-3 text-left">
                     <span className="text-[9px] text-white/40 uppercase font-black tracking-widest block mb-1">Outputs</span>
                     <pre className="text-[10px] text-accent-green/90 bg-black/40 p-2.5 rounded-xl border border-white/5 overflow-x-auto max-h-32 scrollbar-thin">
                         {JSON.stringify(data.outputs, null, 2)}
                     </pre>
                 </div>
             )}

             {/* Error Message */}
             {data.error && (
                 <div className="mt-3 text-left">
                     <span className="text-[9px] text-accent-red uppercase font-black tracking-widest block mb-1">Error</span>
                     <div className="text-[10px] text-accent-red/90 bg-accent-red/10 border border-accent-red/20 p-2.5 rounded-xl max-h-24 overflow-y-auto">
                         {data.error}
                     </div>
                 </div>
             )}
        </div>

        <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-accent-purple !border-none !opacity-80" />
      </div>
    </div>
  );
};
