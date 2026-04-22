import { motion } from 'framer-motion';
import { Activity, Cpu, Zap, Network } from 'lucide-react';

interface MetricProps {
  label: string;
  value: string | number;
  unit?: string;
  icon: React.ReactNode;
  status: 'healthy' | 'warning' | 'critical';
}

function MetricCard({ label, value, unit, icon, status }: MetricProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-accent-cyan glow-success';
      case 'warning':
        return 'text-accent-purple';
      case 'critical':
        return 'text-destructive';
    }
  };

  const getStatusBg = () => {
    switch (status) {
      case 'healthy':
        return 'bg-accent-cyan/10 border-accent-cyan/30';
      case 'warning':
        return 'bg-accent-purple/10 border-accent-purple/30';
      case 'critical':
        return 'bg-destructive/10 border-destructive/30';
    }
  };

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={`glass-panel-elevated rounded-lg p-4 border ${getStatusBg()}`}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-metadata text-muted-foreground">{label}</span>
        <div className={`p-1.5 rounded-lg ${getStatusColor()}`}>{icon}</div>
      </div>
      <div className="flex items-baseline gap-1">
        <span className={`text-lg font-heading ${getStatusColor()}`}>{value}</span>
        {unit && <span className="text-xs text-muted-foreground">{unit}</span>}
      </div>
    </motion.div>
  );
}

export default function SystemStatus() {
  const metrics: MetricProps[] = [
    {
      label: 'API Health',
      value: '99.8',
      unit: '%',
      icon: <Activity size={16} />,
      status: 'healthy',
    },
    {
      label: 'Memory Usage',
      value: '64',
      unit: '%',
      icon: <Cpu size={16} />,
      status: 'healthy',
    },
    {
      label: 'Active Tasks',
      value: '12',
      icon: <Zap size={16} />,
      status: 'healthy',
    },
    {
      label: 'Network Latency',
      value: '42',
      unit: 'ms',
      icon: <Network size={16} />,
      status: 'healthy',
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

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-2 gap-3"
    >
      {metrics.map((metric) => (
        <motion.div
          key={metric.label}
          variants={{
            hidden: { opacity: 0, y: 10 },
            visible: { opacity: 1, y: 0 },
          }}
        >
          <MetricCard {...metric} />
        </motion.div>
      ))}
    </motion.div>
  );
}
