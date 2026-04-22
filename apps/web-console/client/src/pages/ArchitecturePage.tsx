import { motion } from 'framer-motion';
import { ArrowRight, Database, Zap, Brain, Network } from 'lucide-react';
import GlassCard from '@/components/GlassCard';
export default function ArchitecturePage() {
  const components = [
    {
      name: 'Frontend',
      description: 'React + Vite',
      icon: <Zap size={24} />,
      color: 'from-accent-neon-blue to-accent-cyan',
    },
    {
      name: 'Orchestrator',
      description: 'FastAPI',
      icon: <Brain size={24} />,
      color: 'from-accent-purple to-accent-neon-blue',
    },
    {
      name: 'Memory Service',
      description: 'Semantic Context',
      icon: <Database size={24} />,
      color: 'from-accent-cyan to-accent-purple',
    },
    {
      name: 'MCP Tools',
      description: 'Gmail, Drive, Calendar',
      icon: <Network size={24} />,
      color: 'from-accent-purple to-accent-cyan',
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="h-full overflow-y-auto p-8 custom-scrollbar">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="mb-12"
      >
        <h1 className="font-display text-3xl text-foreground mb-2">System Architecture</h1>
        <p className="text-muted-foreground">Microservices-based AI orchestration platform</p>
      </motion.div>

      {/* Architecture Diagram */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12"
      >
        {components.map((component, index) => (
          <motion.div key={component.name} variants={itemVariants}>
            <GlassCard variant="elevated">
              <div className={`inline-flex p-3 rounded-lg bg-gradient-to-r ${component.color} mb-4`}>
                <div className="text-white">{component.icon}</div>
              </div>
              <h3 className="font-heading text-foreground mb-1">{component.name}</h3>
              <p className="text-xs text-muted-foreground">{component.description}</p>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>

      {/* Data Flow */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="glass-panel rounded-2xl p-10 mb-12 border-white/5"
      >
        <h2 className="font-heading text-xl text-foreground mb-8 flex items-center gap-3">
          <Network size={20} className="text-accent-blue" />
          System Control Flow
        </h2>
        <div className="space-y-6 relative">
          {/* Background Line */}
          <div className="absolute left-4 top-4 bottom-4 w-px bg-white/10" />
          
          {[
            'User sends message via Chat Interface',
            'Orchestrator receives request and analyzes intent',
            'Memory Service retrieves relevant context',
            'MCP Tools execute required actions',
            'Results aggregated and returned to user',
            'Execution trace updated in real-time',
          ].map((step, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.6 + index * 0.1 }}
              className="flex items-center gap-6 group"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue/20 to-accent-purple/20 border border-white/10 flex items-center justify-center text-white font-heading text-sm z-10 group-hover:border-accent-blue/50 transition-colors">
                {index + 1}
              </div>
              <p className="font-body text-foreground-secondary flex-1 group-hover:text-foreground-primary transition-colors">{step}</p>
              {index < 5 && (
                <motion.div
                  animate={{ x: [0, 5, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                >
                  <ArrowRight size={16} className="text-white/10 group-hover:text-accent-blue transition-colors" />
                </motion.div>
              )}
            </motion.div>
          ))}
        </div>
      </motion.div>

      {/* Key Features */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
        className="grid grid-cols-1 md:grid-cols-2 gap-6"
      >
        {[
          {
            title: 'Scalable Microservices',
            description: 'Independent services for orchestration, memory, and tool execution',
          },
          {
            title: 'Real-time Execution Tracking',
            description: 'Monitor tool execution with live timeline and status updates',
          },
          {
            title: 'Semantic Memory',
            description: 'Context-aware memory service for intelligent decision making',
          },
          {
            title: 'Multi-tool Integration',
            description: 'Seamless integration with Gmail, Google Drive, Calendar, and more',
          },
        ].map((feature, index) => (
          <motion.div
            key={feature.title}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 1.2 + index * 0.1 }}
          >
            <GlassCard variant="interactive">
              <h3 className="font-heading text-foreground mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.description}</p>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
