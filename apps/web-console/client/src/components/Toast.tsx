import { motion } from 'framer-motion';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';
import { useEffect, useState } from 'react';

interface ToastProps {
  message: string;
  type?: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
  onClose?: () => void;
}

export default function Toast({
  message,
  type = 'info',
  duration = 4000,
  onClose,
}: ToastProps) {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      onClose?.();
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const typeConfig = {
    success: {
      icon: <CheckCircle size={18} />,
      color: 'text-accent-cyan glow-success',
      bg: 'bg-accent-cyan/10 border-accent-cyan/30',
    },
    error: {
      icon: <AlertCircle size={18} />,
      color: 'text-destructive',
      bg: 'bg-destructive/10 border-destructive/30',
    },
    info: {
      icon: <Info size={18} />,
      color: 'text-accent-neon-blue glow-blue',
      bg: 'bg-accent-neon-blue/10 border-accent-neon-blue/30',
    },
    warning: {
      icon: <AlertCircle size={18} />,
      color: 'text-accent-purple glow-ai',
      bg: 'bg-accent-purple/10 border-accent-purple/30',
    },
  };

  const config = typeConfig[type];

  return (
    <motion.div
      initial={{ opacity: 0, y: -20, scale: 0.95 }}
      animate={isVisible ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: -20, scale: 0.95 }}
      exit={{ opacity: 0, y: -20, scale: 0.95 }}
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
      className={`glass-panel border rounded-lg p-4 flex items-center gap-3 shadow-premium-lg ${config.bg}`}
    >
      <div className={config.color}>{config.icon}</div>
      <p className="font-body text-foreground flex-1">{message}</p>
      <motion.button
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={() => setIsVisible(false)}
        className="p-1 hover:bg-glass-opacity-2 rounded transition-colors"
      >
        <X size={16} className="text-muted-foreground" />
      </motion.button>
    </motion.div>
  );
}
