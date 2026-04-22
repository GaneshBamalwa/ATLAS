import { motion } from 'framer-motion';
import { Mail, HardDrive, Calendar, Link2, ChevronRight } from 'lucide-react';

interface ToolCardProps {
  name: string;
  status: 'connected' | 'disconnected' | 'error';
  lastUsed?: Date;
  icon?: React.ReactNode;
  onClick?: () => void;
}

export default function ToolCard({
  name,
  status,
  lastUsed,
  icon,
  onClick,
}: ToolCardProps) {
  const getStatusColor = () => {
    switch (status) {
      case 'connected':
        return 'text-accent-cyan glow-success';
      case 'error':
        return 'text-destructive';
      default:
        return 'text-muted-foreground';
    }
  };

  const getStatusBgColor = () => {
    switch (status) {
      case 'connected':
        return 'bg-accent-cyan/10 border-accent-cyan/30';
      case 'error':
        return 'bg-destructive/10 border-destructive/30';
      default:
        return 'bg-glass-opacity-2 border-glass-border';
    }
  };

  const getIcon = () => {
    if (icon) return icon;
    switch (name.toLowerCase()) {
      case 'gmail':
        return <Mail size={20} />;
      case 'google drive':
        return <HardDrive size={20} />;
      case 'calendar':
        return <Calendar size={20} />;
      default:
        return <Link2 size={20} />;
    }
  };

  return (
    <motion.button
      whileHover={{ scale: 1.02, y: -4 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="w-full glass-panel-elevated rounded-xl p-4 transition-all hover:shadow-premium-lg"
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3 flex-1 text-left">
          {/* Icon */}
          <div
            className={`p-2 rounded-lg ${getStatusBgColor()} ${getStatusColor()} flex-shrink-0 mt-0.5`}
          >
            {getIcon()}
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            <h3 className="font-heading text-foreground">{name}</h3>
            <div className="flex items-center gap-2 mt-1">
              <div
                className={`w-2 h-2 rounded-full ${
                  status === 'connected'
                    ? 'bg-accent-cyan glow-success'
                    : status === 'error'
                      ? 'bg-destructive'
                      : 'bg-muted-foreground'
                }`}
              />
              <span className={`text-xs font-metadata ${getStatusColor()}`}>
                {status === 'connected' && 'Connected'}
                {status === 'disconnected' && 'Disconnected'}
                {status === 'error' && 'Error'}
              </span>
            </div>
            {lastUsed && (
              <p className="text-xs text-muted-foreground mt-2">
                Last used: {lastUsed.toLocaleDateString()}
              </p>
            )}
          </div>
        </div>

        {/* Chevron */}
        <motion.div
          animate={{ x: [0, 4, 0] }}
          transition={{ duration: 2, repeat: Infinity }}
          className="flex-shrink-0 mt-1"
        >
          <ChevronRight size={16} className="text-muted-foreground" />
        </motion.div>
      </div>
    </motion.button>
  );
}
