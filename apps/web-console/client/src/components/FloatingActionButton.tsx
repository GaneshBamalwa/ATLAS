import { motion } from 'framer-motion';
import { Plus } from 'lucide-react';
import { ReactNode } from 'react';

interface FloatingActionButtonProps {
  icon?: ReactNode;
  onClick?: () => void;
  className?: string;
  variant?: 'primary' | 'secondary';
}

export default function FloatingActionButton({
  icon = <Plus size={24} />,
  onClick,
  className = '',
  variant = 'primary',
}: FloatingActionButtonProps) {
  const variantClasses = {
    primary:
      'bg-gradient-to-r from-accent-neon-blue to-accent-purple text-white glow-blue hover:shadow-premium-xl',
    secondary:
      'glass-panel-interactive text-foreground hover:bg-glass-opacity-3 border-glass-border',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={`fixed bottom-8 right-8 w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-premium-lg ${variantClasses[variant]} ${className}`}
    >
      <motion.div
        animate={{ rotate: [0, 360] }}
        transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}
        className="absolute inset-0 rounded-full bg-gradient-to-r from-accent-purple/20 to-accent-neon-blue/20 blur-xl"
      />
      <motion.div
        animate={{ scale: [1, 1.1, 1] }}
        transition={{ duration: 2, repeat: Infinity }}
        className="relative z-10"
      >
        {icon}
      </motion.div>
    </motion.button>
  );
}
