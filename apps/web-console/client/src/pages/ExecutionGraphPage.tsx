import { motion, AnimatePresence } from 'framer-motion';
import { 
  GitBranch, Activity, Database, CheckCircle2, AlertCircle, RefreshCcw, 
  History, Search, Layout, Clock, Workflow, List, Maximize2 
} from 'lucide-react';
import { useEffect, useState, useMemo, useCallback } from 'react';
import { useLocation, useRoute } from 'wouter';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  addEdge,
  Connection,
  Edge,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { GlassPanel } from '@/ui/primitives/GlassPanel';
import { GlassCard } from '@/ui/primitives/GlassCard';
import { FadeIn, StaggerContainer } from '@/ui/animations/LayoutTransition';
import { CustomNode } from '@/components/Graph/CustomNodes';
interface RecentTrace {
  execution_id: string;
  status: string;
  node_count: number;
  timestamp: string;
}

interface TimelineEvent {
  timestamp: string;
  type: string;
  message: string;
  status?: string;
  node_id?: string;
}

const nodeTypes = {
  customNode: CustomNode,
};

export default function ExecutionGraphPage() {
  const [location, setLocation] = useLocation();
  const [match, params] = useRoute("/graph/:id");
  const executionId = params?.id;

  const [viewMode, setViewMode] = useState<'graph' | 'timeline'>('graph');
  const [recentTraces, setRecentTraces] = useState<RecentTrace[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  const fetchGraphData = useCallback(async () => {
    if (!executionId) return;
    try {
      setLoading(true);
      const response = await fetch(`http://localhost:9000/trace/${executionId}/graph`);
      if (!response.ok) throw new Error('Trace not found');
      const data = await response.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
      setError(null);
    } catch (err) {
      console.error('Fetch error:', err);
      setError('Trace data unreachable.');
    } finally {
      setLoading(false);
    }
  }, [executionId, setNodes, setEdges]);

  const fetchTimelineData = useCallback(async () => {
    if (!executionId) return;
    try {
      const response = await fetch(`http://localhost:9000/trace/${executionId}/timeline`);
      if (response.ok) {
        const data = await response.json();
        setTimelineEvents(data);
      }
    } catch (err) {
      console.error('Timeline fetch error:', err);
    }
  }, [executionId]);

  const fetchRecentTraces = async () => {
    try {
      const response = await fetch('http://localhost:9000/api/traces/recent');
      if (response.ok) {
        const data = await response.json();
        setRecentTraces(data);
      }
    } catch (err) {
      console.error('Failed to fetch history:', err);
    }
  };

  useEffect(() => {
    fetchGraphData();
    fetchTimelineData();
    fetchRecentTraces();
  }, [executionId, fetchGraphData, fetchTimelineData]);

  // Handle graph connection
  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div className="flex h-full overflow-hidden">
        {/* History Sidebar */}
        <div className="w-80 border-r border-white/[0.05] flex flex-col glass-heavy z-10">
          <div className="p-8 border-b border-white/[0.05]">
              <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <History size={18} className="text-accent-blue" />
                    <h2 className="text-[11px] font-black uppercase tracking-[0.2em] text-white/60">Lattice History</h2>
                </div>
                <button onClick={fetchRecentTraces} className="p-2 rounded-lg hover:bg-white/5 text-white/20">
                    <RefreshCcw size={14} />
                </button>
              </div>
              <div className="relative">
                <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-white/10" />
                <input 
                  type="text" 
                  placeholder="Filter sessions..." 
                  className="w-full bg-white/[0.02] border border-white/5 rounded-xl py-3 pl-10 pr-4 text-[11px] text-white placeholder-white/20 focus:border-accent-blue/30 transition-all outline-none"
                />
              </div>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-2 scrollbar-hide">
              {recentTraces.map((trace) => (
                <motion.button
                  key={trace.execution_id}
                  whileHover={{ x: 4, backgroundColor: 'rgba(255,255,255,0.02)' }}
                  onClick={() => setLocation(`/graph/${trace.execution_id}`)}
                  className={`w-full text-left p-4 rounded-3xl border transition-all duration-500 ${
                    executionId === trace.execution_id 
                      ? 'border-accent-blue/40 bg-accent-blue/10 shadow-[0_4px_24px_rgba(0,122,255,0.1)]' 
                      : 'border-transparent hover:border-white/5'
                  }`}
                >
                    <div className="flex items-center justify-between mb-3">
                      <span className={`w-2 h-2 rounded-full ${trace.status === 'success' ? 'bg-accent-green shadow-[0_0_12px_#30D158]' : trace.status === 'running' ? 'bg-accent-blue animate-pulse shadow-[0_0_12px_#007AFF]' : 'bg-white/10'}`} />
                      <span className="text-[9px] font-mono text-white/20">{trace.execution_id.split('-')[0].toUpperCase()}</span>
                    </div>
                    <p className="text-xs font-bold text-white/80 truncate">
                      {trace.node_count > 5 ? 'Architectural Sequence' : 'Atomic Operation'}
                    </p>
                    <div className="flex items-center justify-between mt-3 pt-3 border-t border-white/[0.03]">
                      <span className="text-[9px] text-white/30 font-bold">{new Date(trace.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      <span className="text-[9px] text-accent-purple/80 font-black">{trace.node_count} CORES</span>
                    </div>
                </motion.button>
              ))}
          </div>
        </div>

        {/* Main content area */}
        <div className="flex-1 flex flex-col relative overflow-hidden">
          {/* Persistent Workspace Header */}
          <div className="p-8 border-b border-white/[0.05] flex items-center justify-between glass-medium z-20">
            <div className="flex items-center gap-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-accent-blue/10 flex items-center justify-center border border-accent-blue/20 text-accent-blue">
                    <Workflow size={20} />
                  </div>
                  <div>
                      <h1 className="text-sm font-display text-white">Topological Observer</h1>
                      <p className="text-[9px] uppercase tracking-[0.3em] text-white/30 font-black mt-0.5">Execution Reference: {executionId || 'IDLE'}</p>
                  </div>
                </div>

                <div className="h-8 w-px bg-white/10 mx-2" />

                {/* View Switches */}
                <div className="flex bg-black/40 rounded-xl p-1 border border-white/5">
                  {[
                    { id: 'graph', label: 'Lattice Graph', icon: Layout },
                    { id: 'timeline', label: 'Timeline Flow', icon: List }
                  ].map(mode => (
                    <button
                      key={mode.id}
                      onClick={() => setViewMode(mode.id as any)}
                      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-[10px] uppercase font-black tracking-widest transition-all ${
                        viewMode === mode.id ? 'bg-accent-blue text-white shadow-lg shadow-blue-500/20' : 'text-white/20 hover:text-white/40'
                      }`}
                    >
                      <mode.icon size={14} />
                      {mode.label}
                    </button>
                  ))}
                </div>
            </div>

            <div className="flex items-center gap-3">
                <button 
                  onClick={fetchGraphData}
                  className="p-2.5 rounded-xl border border-white/5 hover:bg-white/5 text-white/40 transition-colors"
                  title="Force Re-synchronization"
                >
                  <RefreshCcw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>
          </div>

          {/* View Surface */}
          <div className="flex-1 bg-black/20">
            {!executionId ? (
                <div className="h-full flex flex-col items-center justify-center space-y-8 animate-in fade-in duration-1000">
                  <div className="relative">
                      <div className="w-32 h-32 rounded-full bg-accent-blue/5 border border-accent-blue/10 flex items-center justify-center text-accent-blue">
                        <GitBranch size={48} className="opacity-40" />
                      </div>
                      <motion.div animate={{ scale: [1, 1.4, 1], opacity: [0, 0.2, 0] }} transition={{ duration: 4, repeat: Infinity }} className="absolute inset-0 rounded-full bg-accent-blue" />
                  </div>
                  <div className="text-center space-y-2">
                      <h2 className="text-2xl font-display text-white">Inert Observability</h2>
                      <p className="text-[11px] text-white/30 uppercase tracking-[0.4em] font-black">Select an active lattice from the history</p>
                  </div>
                </div>
            ) : (
                <AnimatePresence mode="wait">
                  {viewMode === 'graph' ? (
                      <motion.div 
                        key="graph-view"
                        initial={{ opacity: 0, scale: 0.98 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 1.02 }}
                        className="w-full h-full"
                      >
                        <ReactFlow
                          nodes={nodes}
                          edges={edges}
                          onNodesChange={onNodesChange}
                          onEdgesChange={onEdgesChange}
                          onConnect={onConnect}
                          nodeTypes={nodeTypes}
                          colorMode="dark"
                          fitView
                          className="bg-dot-pattern"
                        >
                          <Background color="#1a1a1a" gap={24} size={1} />
                          <Controls className="!bg-black/40 !border-white/5 !rounded-xl !overflow-hidden !fill-white" />
                        </ReactFlow>
                      </motion.div>
                  ) : (
                      <motion.div 
                        key="timeline-view"
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -20 }}
                        className="w-full h-full p-12 overflow-y-scroll custom-scrollbar"
                      >
                        <div className="max-w-3xl mx-auto relative">
                            {/* Central Glowing Line */}
                            <div className="absolute left-[23px] top-4 bottom-0 w-[1px] bg-gradient-to-b from-accent-blue via-accent-purple to-transparent opacity-40 shadow-[0_0_12px_rgba(0,122,255,0.8)]" />

                            <div className="space-y-10 relative">
                                {timelineEvents.map((event, i) => (
                                  <motion.div 
                                    key={i}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: i * 0.05 }}
                                    className="flex items-start gap-10 group"
                                  >
                                    {/* Event Node */}
                                    <div className="relative flex-shrink-0 z-10">
                                        <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border transition-all duration-700 bg-black ${
                                          event.status === 'success' ? 'border-accent-green/50 text-accent-green shadow-[0_0_15px_rgba(48,209,88,0.2)]' :
                                          event.status === 'failed' ? 'border-accent-red/50 text-accent-red shadow-[0_0_15px_rgba(255,69,58,0.2)]' :
                                          'border-white/10 text-white/30'
                                        }`}>
                                          <Clock size={20} />
                                        </div>
                                    </div>

                                    {/* Event Data */}
                                    <div className="flex-1 space-y-2 pt-2">
                                        <div className="flex items-center justify-between">
                                          <p className={`text-[10px] uppercase font-black tracking-widest ${
                                              event.status === 'success' ? 'text-accent-green/60' : 
                                              event.status === 'failed' ? 'text-accent-red/60' : 
                                              'text-white/20'
                                          }`}>
                                            {event.type.replace('_', ' ')}
                                          </p>
                                          <span className="text-[10px] font-mono text-white/10">{event.timestamp.split('T')[1].split('.')[0]}</span>
                                        </div>
                                        <h4 className="text-[14px] text-white/80 font-bold group-hover:text-white transition-colors">{event.message}</h4>
                                        <p className="text-[11px] text-white/20 font-medium leading-relaxed max-w-xl">
                                          Logical node event recorded at core orchestrator lattice. Status confirmed: verified.
                                        </p>
                                    </div>
                                  </motion.div>
                                ))}

                                {timelineEvents.length === 0 && (
                                  <div className="h-64 flex items-center justify-center">
                                    <p className="text-[11px] uppercase tracking-[0.4em] font-black text-white/10">No chronological artifacts found</p>
                                  </div>
                                )}
                            </div>
                        </div>
                      </motion.div>
                  )}
                </AnimatePresence>
            )}
          </div>
        </div>
      </div>
  );
}
