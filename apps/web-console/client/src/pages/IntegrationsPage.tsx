import { motion } from 'framer-motion';
import { Zap, Globe, MessageSquare, Database, Shield, Cpu } from 'lucide-react';
import GlassCard from '@/components/GlassCard';

export default function IntegrationsPage() {
  const integrations = [
    {
      name: 'Google Workspace',
      description: 'Gmail, Calendar, Drive integration for automated workflows',
      icon: <Globe size={24} />,
      status: 'active',
      color: 'from-blue-500 to-cyan-500',
    },
    {
      name: 'Slack',
      description: 'Real-time notifications and interactive commands',
      icon: <MessageSquare size={24} />,
      status: 'pending',
      color: 'from-purple-500 to-pink-500',
    },
    {
      name: 'Elasticsearch',
      description: 'High-performance semantic search and indexing',
      icon: <Database size={24} />,
      status: 'active',
      color: 'from-orange-500 to-yellow-500',
    },
    {
      name: 'OAuth 2.0',
      description: 'Secure enterprise-grade authentication and authorization',
      icon: <Shield size={24} />,
      status: 'active',
      color: 'from-green-500 to-emerald-500',
    },
    {
      name: 'Nvidia CUDA',
      description: 'GPU-accelerated inference for complex orchestrations',
      icon: <Cpu size={24} />,
      status: 'inactive',
      color: 'from-emerald-500 to-teal-500',
    },
    {
      name: 'Custom Webhooks',
      description: 'Trigger external systems with execution lifecycle events',
      icon: <Zap size={24} />,
      status: 'active',
      color: 'from-blue-500 to-indigo-500',
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
        <h1 className="font-display text-3xl text-foreground mb-2">Integrations</h1>
        <p className="text-muted-foreground">Connect ATLAS to your favorite tools and platforms</p>
      </motion.div>

      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
      >
        {integrations.map((integration) => (
          <motion.div key={integration.name} variants={itemVariants}>
            <GlassCard variant="elevated" className="h-full flex flex-col">
              <div className={`inline-flex p-3 rounded-xl bg-gradient-to-r ${integration.color} mb-6 shadow-lg shadow-black/20`}>
                <div className="text-white">{integration.icon}</div>
              </div>
              <h3 className="font-heading text-lg text-foreground mb-2">{integration.name}</h3>
              <p className="text-sm text-muted-foreground mb-6 flex-1">
                {integration.description}
              </p>
              <div className="flex items-center justify-between mt-auto pt-4 border-t border-white/5">
                <div className="flex items-center gap-2">
                  <div className={`w-2 h-2 rounded-full ${
                    integration.status === 'active' ? 'bg-accent-green glow-success' : 
                    integration.status === 'pending' ? 'bg-accent-purple animate-pulse' : 
                    'bg-white/10'
                  }`} />
                  <span className="text-[10px] uppercase tracking-widest font-bold text-foreground-tertiary">
                    {integration.status}
                  </span>
                </div>
                <button className="text-xs font-bold text-accent-blue hover:text-accent-blue/80 transition-colors uppercase tracking-widest">
                  Manage
                </button>
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>
    </div>
  );
}
