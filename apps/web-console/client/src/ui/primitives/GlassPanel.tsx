import { motion, HTMLMotionProps } from 'framer-motion';
import { cn } from '@/lib/utils';
import { ReactNode } from 'react';

interface GlassPanelProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
  intensity?: 'thin' | 'light' | 'medium' | 'heavy';
  showHighlight?: boolean;
}

export const GlassPanel = ({ 
  children, 
  intensity = 'light', 
  showHighlight = true,
  className, 
  ...props 
}: GlassPanelProps) => {
  const intensityClasses = {
    thin: 'glass-thin',
    light: 'glass-light',
    medium: 'glass-medium',
    heavy: 'glass-heavy',
  };

  return (
    <motion.div
      className={cn(
        'relative rounded-2xl overflow-hidden',
        intensityClasses[intensity],
        showHighlight && 'glass-light-edge',
        className
      )}
      {...props}
    >
      {children}
    </motion.div>
  );
};
