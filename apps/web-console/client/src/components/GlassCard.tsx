import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface GlassCardProps {
  children: ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'interactive';
  onClick?: () => void;
  hover?: boolean;
}

export default function GlassCard({
  children,
  className = '',
  variant = 'default',
  onClick,
  hover = true,
}: GlassCardProps) {
  const variantClasses = {
    default: 'glass-panel',
    elevated: 'glass-panel-elevated',
    interactive: 'glass-panel-interactive',
  };

  return (
    <motion.div
      whileHover={hover ? { scale: 1.02, y: -4 } : undefined}
      whileTap={hover ? { scale: 0.98 } : undefined}
      onClick={onClick}
      className={`${variantClasses[variant]} rounded-xl p-4 transition-all ${
        hover ? 'cursor-pointer hover:shadow-premium-lg' : ''
      } ${className}`}
    >
      {children}
    </motion.div>
  );
}
