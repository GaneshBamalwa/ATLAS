import { motion } from 'framer-motion';

interface NotificationBadgeProps {
  count?: number;
  variant?: 'info' | 'success' | 'warning' | 'error';
  pulse?: boolean;
}

export default function NotificationBadge({
  count,
  variant = 'info',
  pulse = true,
}: NotificationBadgeProps) {
  const variantColors = {
    info: 'bg-accent-neon-blue',
    success: 'bg-accent-cyan',
    warning: 'bg-accent-purple',
    error: 'bg-destructive',
  };

  const variantGlow = {
    info: 'glow-blue',
    success: 'glow-success',
    warning: 'glow-ai',
    error: 'shadow-lg',
  };

  return (
    <motion.div
      animate={pulse ? { scale: [1, 1.2, 1] } : undefined}
      transition={pulse ? { duration: 2, repeat: Infinity } : undefined}
      className={`inline-flex items-center justify-center w-5 h-5 rounded-full text-xs font-heading text-white ${variantColors[variant]} ${variantGlow[variant]}`}
    >
      {count !== undefined && count > 9 ? '9+' : count}
    </motion.div>
  );
}
