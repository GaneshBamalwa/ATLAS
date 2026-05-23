import { type ReactNode, useEffect, useMemo, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, HardDrive, Mail, RefreshCcw } from 'lucide-react';
import { getActiveUserId, setActiveUserId } from '@/lib/authUser';

type ServiceKey = 'gmail' | 'drive' | 'calendar';

type ServiceState = {
  authenticated: boolean;
  loading: boolean;
  error?: string;
};

const MCP_BASE_URL = import.meta.env.VITE_GOOGLE_MCP_BASE_URL || 'http://localhost:8000';

const SERVICES: Array<{ key: ServiceKey; label: string; description: string; icon: ReactNode }> = [
  {
    key: 'gmail',
    label: 'Gmail',
    description: 'Read, draft, and send email through ATLAS workflows.',
    icon: <Mail size={16} />,
  },
  {
    key: 'drive',
    label: 'Google Drive',
    description: 'Search, read, and share files from connected Drive.',
    icon: <HardDrive size={16} />,
  },
  {
    key: 'calendar',
    label: 'Google Calendar',
    description: 'Read events and create or update meetings.',
    icon: <Calendar size={16} />,
  },
];

const getUrlParams = () => {
  if (typeof window === 'undefined') {
    return { userId: '', service: '' };
  }

  const params = new URLSearchParams(window.location.search);
  return {
    userId: params.get('user_id') || '',
    service: params.get('service') || '',
  };
};

export default function IntegrationsPage() {
  const initialUserId = getUrlParams().userId || getActiveUserId();
  const [userIdInput, setUserIdInput] = useState(initialUserId);
  const [activeUserId, setActiveUser] = useState(initialUserId);
  const [serviceState, setServiceState] = useState<Record<ServiceKey, ServiceState>>({
    gmail: { authenticated: false, loading: true },
    drive: { authenticated: false, loading: true },
    calendar: { authenticated: false, loading: true },
  });
  const [pendingService, setPendingService] = useState<ServiceKey | null>(() => {
    const { service } = getUrlParams();
    return service === 'gmail' || service === 'drive' || service === 'calendar' ? service : null;
  });

  const connectedCount = useMemo(
    () => Object.values(serviceState).filter((service) => service.authenticated).length,
    [serviceState],
  );

  const updateServiceState = (service: ServiceKey, patch: Partial<ServiceState>) => {
    setServiceState((previous) => ({
      ...previous,
      [service]: {
        ...previous[service],
        ...patch,
      },
    }));
  };

  const fetchServiceStatus = async (service: ServiceKey, userId: string) => {
    updateServiceState(service, { loading: true, error: undefined });
    try {
      const response = await fetch(`${MCP_BASE_URL}/auth/status/${service}/${encodeURIComponent(userId)}`);
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || 'Failed to fetch status.');
      }

      updateServiceState(service, {
        loading: false,
        authenticated: Boolean(data?.authenticated),
        error: undefined,
      });
    } catch (error) {
      updateServiceState(service, {
        loading: false,
        authenticated: false,
        error: error instanceof Error ? error.message : 'Unknown status error.',
      });
    }
  };

  const refreshAllStatuses = async (userId: string) => {
    await Promise.all(SERVICES.map((service) => fetchServiceStatus(service.key, userId)));
  };

  useEffect(() => {
    const { userId, service } = getUrlParams();
    if (userId && userId !== activeUserId) {
      setUserIdInput(userId);
      setActiveUser(userId);
      setActiveUserId(userId);
    }
    if (service === 'gmail' || service === 'drive' || service === 'calendar') {
      setPendingService(service);
    }
  }, []);

  useEffect(() => {
    void refreshAllStatuses(activeUserId);
  }, [activeUserId]);

  useEffect(() => {
    if (!pendingService) return;
    void fetchServiceStatus(pendingService, activeUserId);
    setPendingService(null);
  }, [pendingService, activeUserId]);

  const isPlaceholderUser = (id: string) => {
    if (!id) return true;
    const lower = id.toLowerCase();
    return (
      lower === 'default_user' ||
      lower === 'admin@example.com' ||
      lower.startsWith('unknown_user_')
    );
  };

  const handleConnect = (service: ServiceKey) => {
    window.location.href = `${MCP_BASE_URL}/auth/login/${service}`;
  };

  const handleDisconnect = async (service: ServiceKey) => {
    updateServiceState(service, { loading: true, error: undefined });
    try {
      const response = await fetch(`${MCP_BASE_URL}/auth/logout/${service}/${encodeURIComponent(activeUserId)}`, {
        method: 'POST',
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data?.detail || 'Disconnect failed.');
      }

      updateServiceState(service, { authenticated: false, loading: false, error: undefined });
    } catch (error) {
      updateServiceState(service, {
        loading: false,
        error: error instanceof Error ? error.message : 'Disconnect failed.',
      });
    }
  };

  const handleUserIdSave = () => {
    const trimmed = userIdInput.trim();
    if (!trimmed) return;
    setActiveUserId(trimmed);
    setActiveUser(trimmed);
  };

  return (
    <div className="h-full overflow-y-auto p-8 custom-scrollbar">
      <motion.div
        initial={{ opacity: 0, y: -12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeInOut' }}
        className="mb-8"
      >
        <h1 className="font-display text-3xl text-foreground mb-2">Integrations</h1>
        <p className="text-muted-foreground">Connect or disconnect your Google tools.</p>
      </motion.div>

      <div className="mb-6 rounded-2xl border border-white/8 bg-white/[0.02] p-5">
        <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
          <div className="flex-1">
            <p className="text-[10px] uppercase tracking-[0.3em] text-muted-foreground mb-2">Active User</p>
            <div className="flex items-center gap-2">
              <input
                value={userIdInput}
                onChange={(event) => setUserIdInput(event.target.value)}
                className="h-10 w-full rounded-xl border border-white/8 bg-white/[0.02] px-3 text-sm text-foreground outline-none focus:border-primary/60"
                placeholder="Enter account email"
              />
              <button
                onClick={handleUserIdSave}
                className="h-10 rounded-xl border border-white/8 px-4 text-xs uppercase tracking-[0.24em] text-foreground transition-colors duration-150 hover:bg-white/[0.05]"
              >
                Save
              </button>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <p className="text-xs text-muted-foreground">{connectedCount}/3 connected</p>
            <button
              onClick={() => void refreshAllStatuses(activeUserId)}
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-white/8 text-muted-foreground transition-colors duration-150 hover:bg-white/[0.05] hover:text-foreground"
              aria-label="Refresh integration status"
            >
              <RefreshCcw size={16} />
            </button>
          </div>
        </div>

        {isPlaceholderUser(activeUserId) && (
          <div className="mb-4 rounded-lg border border-yellow-400/20 bg-yellow-100/5 p-3 text-sm text-yellow-300">
            No valid Google account detected. Please connect your Google account via the "Connect" button or enter your email above and click "Save".
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {SERVICES.map((service) => {
          const state = serviceState[service.key];
          const isConnected = state.authenticated;

          return (
            <motion.div
              key={service.key}
              initial={{ opacity: 0, y: 14 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2, ease: 'easeInOut' }}
              className="rounded-2xl border border-white/8 bg-white/[0.02] p-5"
            >
              <div className="mb-4 flex items-center justify-between">
                <div className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 bg-white/[0.03] text-foreground">
                  {service.icon}
                </div>
                <div className="flex items-center gap-2">
                  <span className={`h-1.5 w-1.5 rounded-full ${isConnected ? 'bg-foreground' : 'bg-white/20'}`} />
                  <span className="text-[10px] uppercase tracking-[0.24em] text-muted-foreground">
                    {state.loading ? 'Checking' : isConnected ? 'Connected' : 'Disconnected'}
                  </span>
                </div>
              </div>

              <h2 className="text-base font-medium text-foreground tracking-tight mb-2">{service.label}</h2>
              <p className="text-sm text-muted-foreground leading-6 min-h-[72px]">{service.description}</p>

              {state.error && (
                <p className="mt-2 text-xs text-destructive">{state.error}</p>
              )}

              <div className="mt-5 flex items-center gap-2">
                {!isConnected && (
                  <button
                    onClick={() => handleConnect(service.key)}
                    disabled={state.loading}
                    className="h-9 rounded-lg border border-white/8 px-4 text-xs uppercase tracking-[0.22em] text-foreground transition-colors duration-150 hover:bg-white/[0.05] disabled:opacity-50"
                  >
                    Connect
                  </button>
                )}
                {isConnected && (
                  <button
                    onClick={() => void handleDisconnect(service.key)}
                    disabled={state.loading}
                    className="h-9 rounded-lg border border-white/8 px-4 text-xs uppercase tracking-[0.22em] text-muted-foreground transition-colors duration-150 hover:bg-white/[0.05] hover:text-foreground disabled:opacity-40"
                  >
                    Disconnect
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
