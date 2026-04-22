import { motion } from 'framer-motion';
import { Bell, Lock, Palette, User, LogOut } from 'lucide-react';
import GlassCard from '@/components/GlassCard';
import AnimatedButton from '@/components/AnimatedButton';

export default function SettingsPage() {
  const settingsSections = [
    {
      title: 'Profile',
      icon: <User size={20} />,
      items: [
        { label: 'Name', value: 'John Doe' },
        { label: 'Email', value: 'john@ATLAS.ai' },
        { label: 'Role', value: 'Administrator' },
      ],
    },
    {
      title: 'Notifications',
      icon: <Bell size={20} />,
      items: [
        { label: 'Email Alerts', toggle: true, enabled: true },
        { label: 'Tool Execution Updates', toggle: true, enabled: true },
        { label: 'System Notifications', toggle: true, enabled: false },
      ],
    },
    {
      title: 'Security',
      icon: <Lock size={20} />,
      items: [
        { label: 'Two-Factor Authentication', toggle: true, enabled: true },
        { label: 'Session Timeout', value: '30 minutes' },
        { label: 'Last Login', value: 'Today at 2:30 PM' },
      ],
    },
    {
      title: 'Appearance',
      icon: <Palette size={20} />,
      items: [
        { label: 'Theme', value: 'Dark' },
        { label: 'Accent Color', value: 'Blue' },
        { label: 'Font Size', value: 'Medium' },
      ],
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.05,
      },
    },
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <div className="h-full overflow-y-auto p-8 custom-scrollbar">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="mb-12"
      >
        <h1 className="font-display text-3xl text-foreground mb-2">Settings</h1>
        <p className="text-muted-foreground">Manage your preferences and account settings</p>
      </motion.div>

      {/* Settings Sections */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12"
      >
        {settingsSections.map((section) => (
          <motion.div key={section.title} variants={itemVariants}>
            <GlassCard variant="elevated">
              <div className="flex items-center gap-3 mb-4">
                <div className="p-2 rounded-lg bg-gradient-to-r from-accent-neon-blue to-accent-purple">
                  <div className="text-white">{section.icon}</div>
                </div>
                <h2 className="font-heading text-foreground">{section.title}</h2>
              </div>

              <div className="space-y-3">
                {section.items.map((item, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.1 + index * 0.05 }}
                    className="flex items-center justify-between py-2 border-b border-glass-border last:border-0"
                  >
                    <span className="text-sm font-body text-muted-foreground">
                      {item.label}
                    </span>
                    {item.toggle ? (
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        className={`w-10 h-6 rounded-full transition-all ${
                          item.enabled
                            ? 'bg-gradient-to-r from-accent-neon-blue to-accent-purple'
                            : 'bg-glass-opacity-2'
                        }`}
                      >
                        <motion.div
                          animate={{ x: item.enabled ? 16 : 2 }}
                          className="w-5 h-5 rounded-full bg-white m-0.5"
                        />
                      </motion.button>
                    ) : (
                      <span className="text-sm font-code text-accent-neon-blue">
                        {item.value}
                      </span>
                    )}
                  </motion.div>
                ))}
              </div>
            </GlassCard>
          </motion.div>
        ))}
      </motion.div>

      {/* Danger Zone */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="glass-panel rounded-2xl p-8 border-destructive/30"
      >
        <h2 className="font-heading text-destructive mb-4">Danger Zone</h2>
        <p className="text-sm text-muted-foreground mb-4">
          These actions cannot be undone. Please proceed with caution.
        </p>
        <div className="flex gap-4">
          <AnimatedButton variant="danger" size="md">
            <LogOut size={16} />
            Logout All Sessions
          </AnimatedButton>
          <AnimatedButton variant="danger" size="md">
            Delete Account
          </AnimatedButton>
        </div>
      </motion.div>
    </div>
  );
}
