import { motion } from 'framer-motion';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  variant?: 'default' | 'pulse' | 'orbit';
}

export default function LoadingSpinner({
  size = 'md',
  variant = 'default',
}: LoadingSpinnerProps) {
  const sizeMap = {
    sm: 24,
    md: 40,
    lg: 56,
  };

  const dimension = sizeMap[size];

  if (variant === 'pulse') {
    return (
      <div className="flex items-center justify-center gap-2">
        {[0, 0.2, 0.4].map((delay) => (
          <motion.div
            key={delay}
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ duration: 1, repeat: Infinity, delay }}
            className="w-2 h-2 rounded-full bg-gradient-to-r from-accent-purple to-accent-neon-blue"
          />
        ))}
      </div>
    );
  }

  if (variant === 'orbit') {
    return (
      <div className="relative" style={{ width: dimension, height: dimension }}>
        {/* Outer orbit */}
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 3, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-0 rounded-full border-2 border-transparent border-t-accent-neon-blue border-r-accent-purple"
        />
        {/* Inner orbit */}
        <motion.div
          animate={{ rotate: -360 }}
          transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          className="absolute inset-2 rounded-full border-2 border-transparent border-b-accent-cyan border-l-accent-purple"
        />
        {/* Center dot */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-1.5 h-1.5 rounded-full bg-gradient-to-r from-accent-purple to-accent-neon-blue glow-ai" />
        </div>
      </div>
    );
  }

  // Default spinner
  return (
    <motion.div
      animate={{ rotate: 360 }}
      transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
      className="relative"
      style={{ width: dimension, height: dimension }}
    >
      <svg
        className="w-full h-full"
        viewBox="0 0 50 50"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          <linearGradient id="spinnerGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#007AFF" />
            <stop offset="50%" stopColor="#BF5AF2" />
            <stop offset="100%" stopColor="#64D2FF" />
          </linearGradient>
        </defs>
        <circle
          cx="25"
          cy="25"
          r="20"
          stroke="url(#spinnerGradient)"
          strokeWidth="3"
          strokeDasharray="31.4 125.6"
          strokeLinecap="round"
        />
      </svg>
    </motion.div>
  );
}
