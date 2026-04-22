import { motion } from 'framer-motion';
import { ReactNode } from 'react';

interface AnimatedButtonProps {
  children: ReactNode;
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  onClick?: () => void;
  disabled?: boolean;
  className?: string;
  icon?: ReactNode;
}

export default function AnimatedButton({
  children,
  variant = 'primary',
  size = 'md',
  onClick,
  disabled = false,
  className = '',
  icon,
}: AnimatedButtonProps) {
  const baseClasses =
    'font-heading rounded-lg transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2';

  const variantClasses = {
    primary:
      'bg-gradient-to-r from-accent-neon-blue to-accent-purple text-white hover:shadow-premium-lg glow-blue',
    secondary:
      'glass-panel-interactive text-foreground hover:bg-glass-opacity-3 border-glass-border',
    ghost: 'text-foreground hover:bg-glass-opacity-2',
    danger: 'bg-destructive/20 text-destructive border border-destructive/50 hover:bg-destructive/30',
  };

  const sizeClasses = {
    sm: 'px-3 py-2 text-xs',
    md: 'px-4 py-2.5 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  return (
    <motion.button
      whileHover={{ scale: disabled ? 1 : 1.05 }}
      whileTap={{ scale: disabled ? 1 : 0.95 }}
      onClick={onClick}
      disabled={disabled}
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
    >
      {icon && <motion.div animate={{ rotate: [0, 360] }}>{icon}</motion.div>}
      {children}
    </motion.button>
  );
}
