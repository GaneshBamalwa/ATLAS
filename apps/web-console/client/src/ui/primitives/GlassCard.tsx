import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface GlassCardProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
  elevation?: 1 | 2 | 3 | 4 | 5;
}

export const GlassCard = ({ 
  children, 
  elevation = 2,
  className, 
  ...props 
}: GlassCardProps) => {
  return (
    <motion.div
      whileHover={{ y: -2, scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      className={cn(
        'glass-medium rounded-xl p-4 transition-all duration-300',
        `elevation-${elevation}`,
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
};
