import { motion, useMotionValue, useTransform } from 'framer-motion';
import { Menu, Settings, Bell, MoreVertical } from 'lucide-react';
import { useState, useRef } from 'react';
import { useLocation } from 'wouter';
import ChatPanel from './ChatPanel';
import Sidebar from './Sidebar';
import { GlassPanel } from '@/ui/primitives/GlassPanel';

interface ConsoleLayoutProps {
  children?: React.ReactNode;
}

export default function ConsoleLayout({ children }: ConsoleLayoutProps) {
  const [location, setLocation] = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Dynamic visibility logic
  const isGraphPage = location.startsWith('/graph');
  const isSettingsPage = location === '/settings';

  const containerRef = useRef<HTMLDivElement>(null);
  
  // Refined Parallax effect
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  
  // FIXED: Hooks must be at the top level, not in JSX/props
  const headerY = useTransform(mouseY, (v) => v * 0.5);
  const contentY = useTransform(mouseY, (v) => v * 0.8);

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) * 0.005;
    const y = (e.clientY - rect.top - rect.height / 2) * 0.005;
    mouseX.set(x);
    mouseY.set(y);
  };

  return (
    <div
      ref={containerRef}
      onMouseMove={handleMouseMove}
      className="min-h-screen bg-depth-bg-primary overflow-hidden relative selection:bg-accent-blue/30"
    >
      {/* BACKGROUND LAYER: iOS style ambient lighting */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <motion.div
          animate={{
            opacity: [0.4, 0.6, 0.4],
            scale: [1, 1.1, 1],
          }}
          transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
          className="absolute -top-[20%] -left-[10%] w-[60%] h-[60%] bg-gradient-radial from-accent-purple/15 to-transparent rounded-full blur-[100px]"
        />
        
        <motion.div
          animate={{
            opacity: [0.3, 0.5, 0.3],
            scale: [1, 1.2, 1],
          }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear", delay: 2 }}
          className="absolute -bottom-[20%] -right-[10%] w-[60%] h-[60%] bg-gradient-radial from-accent-blue/10 to-transparent rounded-full blur-[100px]"
        />
        
        <div className="absolute inset-0 opacity-[0.03] mix-blend-overlay" style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 400 400' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' seed='2'/%3E%3C/filter%3E%3Crect width='400' height='400' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
        }} />
      </div>

      {/* MAIN INTERFACE */}
      <div className="relative flex h-screen z-10 p-4 gap-4">
        {/* Sidebar - Floating Glass Dock */}
        <motion.div
          initial={{ x: -300, opacity: 0, scale: 0.95 }}
          animate={{ 
            x: sidebarOpen ? 0 : -320, 
            opacity: sidebarOpen ? 1 : 0,
            scale: sidebarOpen ? 1 : 0.95
          }}
          transition={{ type: 'spring', stiffness: 200, damping: 25 }}
          style={{ x: mouseX }}
          className="w-72 flex-shrink-0"
        >
          <GlassPanel intensity="heavy" className="h-full flex flex-col elevation-4 border-white/10 shadow-2xl">
            <Sidebar onToggle={() => setSidebarOpen(!sidebarOpen)} />
          </GlassPanel>
        </motion.div>

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col gap-4 overflow-hidden">
          {/* Header */}
          <GlassPanel 
            intensity="medium" 
            className="h-16 px-6 flex items-center justify-between z-40 elevation-3 border-white/10"
            style={{ y: headerY }}
          >
            <div className="flex items-center gap-4">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="p-2 hover:bg-white/5 rounded-lg transition-colors"
              >
                <Menu size={20} className="text-foreground-primary" />
              </motion.button>
              <div className="flex items-baseline gap-2">
                <h1 className="font-display text-xl tracking-tight text-foreground-primary leading-none">ATLAS</h1>
                <span className="h-3 w-px bg-white/10 self-center" />
                <p className="text-[10px] uppercase tracking-widest text-foreground-tertiary font-medium">Orchestrator</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <motion.button
                whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.05)' }}
                whileTap={{ scale: 0.95 }}
                className="p-2.5 rounded-lg text-foreground-secondary hover:text-foreground-primary transition-all relative"
              >
                <Bell size={18} />
                <motion.span
                  animate={{ scale: [1, 1.2, 1], opacity: [1, 0.5, 1] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-accent-blue rounded-full shadow-[0_0_8px_#007AFF]"
                />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.05)' }}
                whileTap={{ scale: 0.95 }}
                onClick={() => setLocation('/settings')}
                className="p-2.5 rounded-lg text-foreground-secondary hover:text-foreground-primary transition-all"
              >
                <Settings size={18} />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05, backgroundColor: 'rgba(255,255,255,0.05)' }}
                whileTap={{ scale: 0.95 }}
                className="p-2.5 rounded-lg text-foreground-secondary hover:text-foreground-primary transition-all"
              >
                <MoreVertical size={18} />
              </motion.button>
            </div>
          </GlassPanel>

          {/* Content Panels */}
          <div className="flex-1 flex gap-4 overflow-hidden relative">
            {/* Always mount Chat and Trace panels to preserve state, but hide when not on home */}
            <div className={`w-full h-full flex gap-4 absolute inset-0 transition-opacity duration-300 ${location === '/' ? 'opacity-100 z-10' : 'opacity-0 pointer-events-none -z-10'}`}>
              <GlassPanel 
                intensity="light" 
                className="flex-1 flex flex-col elevation-5 border-white/10"
                style={{ y: contentY }}
              >
                <ChatPanel />
              </GlassPanel>
            </div>

            <motion.div 
              style={{ y: contentY }}
              className={`flex-1 overflow-hidden relative transition-opacity duration-300 ${location === '/' ? 'opacity-0 pointer-events-none -z-10' : 'opacity-100 z-20 bg-depth-bg-primary'}`}
            >
              {children}
            </motion.div>
          </div>

        </div>
      </div>

      {/* FOREGROUND LAYER: Floating Action Elements */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="fixed bottom-8 right-8 z-50 pointer-events-none"
      >
        <motion.div
          animate={{
            scale: [1, 1.1, 1],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{ duration: 4, repeat: Infinity }}
          className="absolute inset-0 -m-4 bg-gradient-to-r from-accent-purple/20 to-accent-blue/20 rounded-full blur-2xl pointer-events-none"
        />
      </motion.div>
    </div>
  );
}
