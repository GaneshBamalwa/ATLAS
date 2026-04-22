import { motion, AnimatePresence } from 'framer-motion';
import {
  ChevronDown,
  Code2,
  GitBranch,
  Layers,
  LogOut,
  MessageSquare,
  Settings,
  Zap,
} from 'lucide-react';
import { useState } from 'react';
import { useLocation } from 'wouter';
import { GlassPanel } from '@/ui/primitives/GlassPanel';

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
    <div className="h-full flex flex-col">
      {/* Branding Section */}
      <div className="p-8 pb-4">
        <motion.div 
          className="flex items-center gap-4 group cursor-pointer"
          whileHover={{ x: 4 }}
          onClick={() => setLocation('/')}
        >
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center shadow-xl shadow-blue-500/20 group-hover:shadow-blue-500/40 transition-shadow duration-500">
            <Zap size={24} className="text-white fill-white/20" />
          </div>
          <div>
            <h2 className="text-lg font-display tracking-tight text-foreground-primary">ATLAS</h2>
            <p className="text-[10px] uppercase tracking-[0.2em] font-black text-accent-blue/60 mt-0.5">Control v1.0</p>
          </div>
        </motion.div>
      </div>

      {/* Main Navigation */}
      <div className="flex-1 px-4 py-6 space-y-2 overflow-y-auto scrollbar-hide">
        {menuItems.map((item) => {
          const isSelected = item.href === '/' 
            ? location === '/' 
            : item.href && location.startsWith(item.href);
          
          return (
            <div key={item.id}>
              <motion.button
                onClick={() => {
                  if (item.href) setLocation(item.href);
                  if (item.submenu) setExpandedMenu(expandedMenu === item.id ? null : item.id);
                }}
                whileHover={{ x: 4 }}
                whileTap={{ scale: 0.98 }}
                className={`w-full group flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-300 relative ${
                  isSelected 
                    ? 'bg-white/[0.08] shadow-inner border border-white/5' 
                    : 'hover:bg-white/[0.03]'
                }`}
              >
                {isSelected && (
                  <motion.div 
                    layoutId="active-indicator"
                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                    className="absolute left-0 w-1 h-6 bg-accent-blue rounded-full shadow-[0_0_8px_#007AFF]"
                  />
                )}
                
                <div className="flex items-center gap-4">
                  <item.icon 
                    size={18} 
                    className={`transition-colors duration-300 ${
                      isSelected ? 'text-accent-blue' : 'text-foreground-tertiary group-hover:text-foreground-primary'
                    }`} 
                  />
                  <span className={`text-sm font-medium transition-colors duration-300 ${
                    isSelected ? 'text-foreground-primary' : 'text-foreground-tertiary group-hover:text-foreground-primary'
                  }`}>
                    {item.label}
                  </span>
                </div>
                
                {item.submenu && (
                  <ChevronDown 
                    size={14} 
                    className={`text-foreground-tertiary transition-transform duration-300 ${expandedMenu === item.id ? 'rotate-180' : ''}`}
                  />
                )}
              </motion.button>

            <AnimatePresence>
              {item.submenu && expandedMenu === item.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden ml-4 pl-4 border-l border-white/5 mt-1 space-y-1"
                >
                  {item.id === 'tools' && toolsSubmenu.map((tool) => (
                    <motion.button
                      key={tool.id}
                      whileHover={{ x: 4, backgroundColor: 'rgba(255,255,255,0.02)' }}
                      onClick={() => setLocation('/tools')}
                      className="w-full text-left px-4 py-2.5 rounded-lg text-[13px] font-medium text-foreground-tertiary hover:text-foreground-secondary flex items-center justify-between group"
                    >
                      {tool.label}
                      <span className={`w-1.5 h-1.5 rounded-full ${tool.status === 'connected' ? 'bg-accent-green shadow-[0_0_8px_#32D74B]' : 'bg-white/10'}`} />
                    </motion.button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        );
      })}
    </div>

      {/* Profile / Bottom Section */}
      <div className="p-6 border-t border-white/5 space-y-3">
        <motion.button
          whileHover={{ backgroundColor: 'rgba(255,255,255,0.03)' }}
          onClick={() => setLocation('/settings')}
          className="w-full flex items-center gap-4 px-4 py-3 rounded-xl text-foreground-tertiary hover:text-foreground-primary transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center overflow-hidden border border-white/10">
            <Settings size={16} />
          </div>
          <span className="text-sm font-medium">System Settings</span>
        </motion.button>
        
        <motion.button
          whileHover={{ backgroundColor: 'rgba(255,59,48,0.05)' }}
          className="w-full flex items-center gap-4 px-4 py-3 rounded-xl text-accent-red/60 hover:text-accent-red transition-colors"
        >
          <div className="w-8 h-8 rounded-full bg-accent-red/10 flex items-center justify-center overflow-hidden border border-accent-red/10">
            <LogOut size={16} />
          </div>
          <span className="text-sm font-medium">Terminate Session</span>
        </motion.button>
      </div>
    </div>
  );
}
