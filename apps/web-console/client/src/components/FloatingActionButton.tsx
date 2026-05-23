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
    primary: 'bg-primary text-white hover:bg-primary/90',
    secondary: 'glass-panel-interactive text-foreground hover:bg-white/[0.05] border border-white/8',
  };

  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={`fixed bottom-8 right-8 w-14 h-14 rounded-full flex items-center justify-center transition-all shadow-premium-lg ${variantClasses[variant]} ${className}`}
    >
      <motion.div animate={{ opacity: [0.35, 0.55, 0.35] }} transition={{ duration: 3, repeat: Infinity, ease: 'easeInOut' }} className="absolute inset-0 rounded-full bg-white/5 blur-xl" />
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
