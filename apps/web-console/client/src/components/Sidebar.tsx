import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, Code2, GitBranch, Layers, LogOut, MessageSquare, Settings, Zap } from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'wouter';

interface SidebarProps {
  onToggle: () => void;
}

export default function Sidebar({ onToggle }: SidebarProps) {
  const [location, setLocation] = useLocation();
  const [expandedMenu, setExpandedMenu] = useState<string | null>(null);

  const menuItems = [
    { id: 'console', label: 'Console', icon: MessageSquare, href: '/' },
    { id: 'execution', label: 'Execution Graph', icon: GitBranch, href: '/graph' },
    { id: 'architecture', label: 'Architecture', icon: Layers, href: '/architecture' },
    { id: 'tools', label: 'Tools', icon: Code2, submenu: true, href: '/tools' },
    { id: 'integrations', label: 'Integrations', icon: Zap, submenu: true, href: '/integrations' },
  ];

  const toolsSubmenu = [
    { id: 'gmail', label: 'Gmail', status: 'connected' },
    { id: 'drive', label: 'Google Drive', status: 'connected' },
    { id: 'calendar', label: 'Calendar', status: 'disconnected' },
  ];

  return (
    <div className="flex h-full flex-col px-5 py-6">
      <div className="pb-8">
        <motion.button
          className="flex items-center gap-3 text-left"
          whileHover={{ opacity: 0.85 }}
          onClick={() => setLocation('/')}
        >
          <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/[0.03] text-foreground">
            <Zap size={18} />
          </div>
          <div>
            <h2 className="text-sm font-medium tracking-[0.24em] text-foreground">ATLAS</h2>
            <p className="text-[10px] uppercase tracking-[0.28em] text-muted-foreground">Orchestrator</p>
          </div>
        </motion.button>
      </div>

      <div className="flex-1 overflow-y-auto pr-1">
        {menuItems.map((item) => {
          const isSelected = item.href === '/' 
            ? location === '/' 
            : item.href && location.startsWith(item.href);
          
          return (
            <div key={item.id} className="mb-2">
              <motion.button
                onClick={() => {
                  if (item.href) setLocation(item.href);
                  if (item.submenu) setExpandedMenu(expandedMenu === item.id ? null : item.id);
                }}
                whileHover={{ opacity: 0.85 }}
                whileTap={{ scale: 0.99 }}
                className={`relative flex w-full items-center justify-between rounded-lg px-3 py-3 transition-colors duration-150 ${
                  isSelected ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                {isSelected && (
                  <motion.div
                    layoutId="active-indicator"
                    transition={{ duration: 0.18, ease: 'easeOut' }}
                    className="absolute left-0 top-2.5 h-6 w-px bg-primary"
                  />
                )}
                
                <div className="flex items-center gap-3">
                  <item.icon 
                    size={18} 
                    className={isSelected ? 'text-foreground' : 'text-muted-foreground'}
                  />
                  <span className="text-sm font-medium tracking-tight">
                    {item.label}
                  </span>
                </div>
                
                {item.submenu && (
                  <ChevronDown 
                    size={14} 
                    className={`text-muted-foreground transition-transform duration-150 ${expandedMenu === item.id ? 'rotate-180' : ''}`}
                  />
                )}
              </motion.button>

            <AnimatePresence>
              {item.submenu && expandedMenu === item.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="mt-1 ml-3 overflow-hidden border-l border-white/5 pl-4 space-y-1"
                >
                  {item.id === 'tools' && toolsSubmenu.map((tool) => (
                    <motion.button
                      key={tool.id}
                      whileHover={{ opacity: 0.85 }}
                      onClick={() => setLocation('/tools')}
                      className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-[13px] text-muted-foreground transition-colors duration-150 hover:text-foreground"
                    >
                      {tool.label}
                      <span className={`h-1.5 w-1.5 rounded-full ${tool.status === 'connected' ? 'bg-foreground' : 'bg-white/15'}`} />
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>

      <div className="mt-6 border-t border-white/5 pt-5 space-y-2">
        <motion.button
          whileHover={{ opacity: 0.85 }}
          onClick={() => setLocation('/settings')}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-3 text-muted-foreground transition-colors duration-150 hover:text-foreground"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.03]">
            <Settings size={15} />
          </div>
          <span className="text-sm font-medium">System Settings</span>
        </motion.button>
        
        <motion.button
          whileHover={{ opacity: 0.9 }}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-3 text-muted-foreground transition-colors duration-150 hover:text-foreground"
        >
          <div className="flex h-8 w-8 items-center justify-center rounded-full border border-white/10 bg-white/[0.03]">
            <LogOut size={15} />
          </div>
          <span className="text-sm font-medium">Terminate Session</span>
        </motion.button>
      </div>
    </div>
  );
}
