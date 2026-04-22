import { motion } from 'framer-motion';
import { Mail, HardDrive, Calendar, Plus } from 'lucide-react';
import ToolCard from '@/components/ToolCard';
import SystemStatus from '@/components/SystemStatus';

export default function ToolsPage() {
  const tools = [
    {
      name: 'Gmail',
      status: 'connected' as const,
      lastUsed: new Date(Date.now() - 3600000),
      icon: <Mail size={20} />,
    },
    {
      name: 'Google Drive',
      status: 'connected' as const,
      lastUsed: new Date(Date.now() - 7200000),
      icon: <HardDrive size={20} />,
    },
    {
      name: 'Calendar',
      status: 'disconnected' as const,
      icon: <Calendar size={20} />,
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
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
          <h1 className="font-display text-3xl text-foreground mb-2">Integrated Tools</h1>
          <p className="text-muted-foreground">Manage and monitor your connected services</p>
        </motion.div>

        {/* System Status */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.1 }}
          className="mb-12"
        >
          <h2 className="font-heading text-foreground mb-4">System Status</h2>
          <SystemStatus />
        </motion.div>

        {/* Tools Grid */}
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12"
        >
          {tools.map((tool) => (
            <motion.div key={tool.name} variants={itemVariants}>
              <ToolCard {...tool} />
            </motion.div>
          ))}

          {/* Add New Tool */}
          <motion.button
            variants={itemVariants}
            whileHover={{ scale: 1.02, y: -4 }}
            whileTap={{ scale: 0.98 }}
            className="glass-panel-elevated rounded-xl p-4 h-full flex flex-col items-center justify-center gap-3 hover:shadow-premium-lg transition-all"
          >
            <div className="p-3 rounded-lg bg-gradient-to-r from-accent-neon-blue to-accent-purple">
              <Plus size={24} className="text-white" />
            </div>
            <span className="font-heading text-foreground">Add Tool</span>
            <span className="text-xs text-muted-foreground">Connect new service</span>
          </motion.button>
        </motion.div>

        {/* Tool Details */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="glass-panel rounded-2xl p-8"
        >
          <h2 className="font-heading text-foreground mb-4">Connected Services Overview</h2>
          <div className="space-y-4">
            {tools
              .filter((t) => t.status === 'connected')
              .map((tool, index) => (
                <motion.div
                  key={tool.name}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.4 + index * 0.1 }}
                  className="flex items-center justify-between p-4 glass-panel-elevated rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-gradient-to-r from-accent-neon-blue to-accent-purple">
                      <div className="text-white">{tool.icon}</div>
                    </div>
                    <div>
                      <p className="font-heading text-foreground">{tool.name}</p>
                      <p className="text-xs text-muted-foreground">
                        Last used: {tool.lastUsed?.toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                  <div className="w-3 h-3 rounded-full bg-accent-cyan glow-success" />
                </motion.div>
              ))}
          </div>
        </motion.div>
    </div>
  );
}
