import { motion } from 'framer-motion';
import { Bell, Menu, Settings } from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'wouter';
import Sidebar from './Sidebar';

interface ConsoleLayoutProps {
  children?: React.ReactNode;
}

export default function ConsoleLayout({ children }: ConsoleLayoutProps) {
  const [location, setLocation] = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const isHome = location === '/';

  return (
    <div className="h-screen bg-background text-foreground selection:bg-primary/25 selection:text-foreground">
      <div className="flex h-screen overflow-hidden">
        <motion.aside
          animate={{ width: sidebarOpen ? 288 : 0, opacity: sidebarOpen ? 1 : 0 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="hidden border-r border-white/5 bg-[#0c0c0d] md:block"
        >
          <div className="h-full w-72 overflow-hidden">
            <Sidebar onToggle={() => setSidebarOpen(!sidebarOpen)} />
          </div>
        </motion.aside>

        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">
          <header className="flex h-16 items-center justify-between border-b border-white/5 px-5 md:px-8">
            <div className="flex items-center gap-4">
              <motion.button
                whileHover={{ opacity: 0.75 }}
                whileTap={{ scale: 0.97 }}
                onClick={() => setSidebarOpen(!sidebarOpen)}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/5 text-foreground-secondary transition-colors duration-150 hover:text-foreground"
              >
                <Menu size={18} />
              </motion.button>
              <div>
                <p className="text-[10px] uppercase tracking-[0.32em] text-muted-foreground">ATLAS</p>
                <h1 className="text-sm font-medium tracking-tight text-foreground">Orchestrator</h1>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <button className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/5 text-foreground-secondary transition-colors duration-150 hover:bg-white/[0.03] hover:text-foreground">
                <Bell size={16} />
              </button>
              <button
                onClick={() => setLocation('/settings')}
                className="inline-flex h-9 w-9 items-center justify-center rounded-full border border-white/5 text-foreground-secondary transition-colors duration-150 hover:bg-white/[0.03] hover:text-foreground"
              >
                <Settings size={16} />
              </button>
            </div>
          </header>

          <main className={isHome ? 'flex-1 min-h-0 overflow-hidden bg-background' : 'flex-1 min-h-0 overflow-hidden bg-background p-4 md:p-6'}>
            {isHome ? (
              <div className="h-full min-h-0 overflow-hidden">{children}</div>
            ) : (
              <div className="h-full min-h-0 overflow-hidden rounded-[28px] border border-white/5 bg-[#0e0e0f]">
                {children}
              </div>
            )}
          </main>
        </div>
      </div>
    </div>
  );
}
