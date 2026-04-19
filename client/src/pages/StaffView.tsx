import React, { useState, useEffect } from 'react';
import Layout from '../components/common/Layout';
import { motion, AnimatePresence } from 'framer-motion';
import { Shield, AlertTriangle, Users, Map } from 'lucide-react';
import { loginWithGoogle, subscribeToAuthChanges, getAuthToken } from '../services/auth';
import axios from 'axios';

const StaffView: React.FC = () => {
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [protocol, setProtocol] = useState<string | null>(null);

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((u) => {
      setUser(u);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  const handleAction = async (zone: string, alert: string) => {
    setActionLoading(true);
    try {
      const token = await getAuthToken();
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/staff/zone-action`,
        { zone_id: zone, alert_type: alert },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setProtocol(response.data.protocol);
    } catch (err) {
      console.error(err);
      alert('Tactical authorization failed.');
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) return <div className="min-h-screen bg-[var(--bg-dark)]" />;

  if (!user) {
    return (
      <Layout title="Staff Intelligence · Portal">
        <div className="max-w-md mx-auto py-24 text-center">
          <Shield size={64} className="mx-auto mb-6 text-[var(--neon-purple)]" />
          <h2 className="text-3xl font-bold mb-4">Tactical Access Required</h2>
          <p className="text-[var(--text-secondary)] mb-8">
            Personnel authentication is mandatory for venue synchronization and zone overrides.
          </p>
          <button onClick={loginWithGoogle} className="primary-button w-full py-4 text-lg">
            Authenticate via Command Center
          </button>
        </div>
      </Layout>
    );
  }

  return (
    <Layout title="Staff Intelligence · Active View">
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 py-8">
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className="glass-card p-6 border-l-4 border-[var(--neon-purple)]">
            <h3 className="text-xl font-bold flex items-center gap-2 mb-4">
              <Map size={20} className="text-[var(--neon-purple)]" /> Venue Tactical Twin
            </h3>
            <div className="aspect-video bg-black/40 rounded-lg flex items-center justify-center border border-[var(--glass-border)] relative overflow-hidden">
               <div className="absolute inset-0 opacity-20 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')]" />
               <div className="z-10 text-[var(--text-secondary)] font-mono text-sm">
                 [LIDAR TELEMETRY RECONSTRUCTING...]
               </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
             {['Gate 4', 'Moscone South', 'Main Exhibit', 'VIP Lounge'].map((zone) => (
               <div key={zone} className="glass-card p-6 group hover:neon-border-purple transition-all">
                  <div className="flex justify-between items-start mb-4">
                    <span className="font-bold text-lg">{zone}</span>
                    <span className="text-xs bg-green-500/20 text-green-500 px-2 py-1 rounded">Clear</span>
                  </div>
                  <button 
                    onClick={() => handleAction(zone, 'Crowd Alert')}
                    disabled={actionLoading}
                    className="w-full py-2 rounded bg-[var(--neon-purple)]/20 border border-[var(--neon-purple)]/30 text-[var(--neon-purple)] font-bold text-sm hover:bg-[var(--neon-purple)] hover:text-white transition-all"
                  >
                    Trigger Tactical Overlay
                  </button>
               </div>
             ))}
          </div>
        </div>

        <div className="flex flex-col gap-6">
           <div className="glass-card p-6 bg-red-500/5 border-red-500/20">
              <h3 className="text-xl font-bold flex items-center gap-2 mb-4 text-red-500">
                <AlertTriangle size={20} /> Active Alerts
              </h3>
              <p className="text-sm text-[var(--text-secondary)]">No active critical anomalies detected in Moscone perimeter.</p>
           </div>

           <AnimatePresence>
             {protocol && (
               <motion.div 
                 initial={{ opacity: 0, scale: 0.9 }}
                 animate={{ opacity: 1, scale: 1 }}
                 className="glass-card p-6 border-l-4 border-[var(--neon-cyan)]"
               >
                 <h3 className="text-lg font-bold mb-2 neon-text-cyan uppercase tracking-wider text-xs">Generated Protocol</h3>
                 <p className="text-sm font-mono leading-relaxed">{protocol}</p>
                 <button onClick={() => setProtocol(null)} className="mt-4 text-xs text-[var(--text-secondary)] hover:text-white">Acknowledge</button>
               </motion.div>
             )}
           </AnimatePresence>

           <div className="glass-card p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-full bg-[var(--neon-purple)]/20 flex items-center justify-center">
                  <Users size={20} className="text-[var(--neon-purple)]" />
                </div>
                <div>
                   <div className="font-bold text-sm">{user.displayName || 'Tactical Unit'}</div>
                   <div className="text-[10px] text-[var(--text-secondary)] uppercase">{user.email}</div>
                </div>
              </div>
           </div>
        </div>
      </div>
    </Layout>
  );
};

export default StaffView;
