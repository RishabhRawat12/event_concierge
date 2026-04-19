import React from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { MapPin, Clock, Star, Info } from 'lucide-react';
import { sanitizeHtml } from '../../utils/sanitizer';

interface ItineraryDisplayProps {
  itinerary: any;
}

const ItineraryDisplay: React.FC<ItineraryDisplayProps> = ({ itinerary }) => {
  const shouldReduceMotion = useReducedMotion();
  
  if (!itinerary) return null;

  return (
    <div 
      className="flex flex-col gap-8 mt-12"
      aria-live="polite"
      aria-relevant="additions text"
    >
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-3xl font-bold mb-2">Your Tactical Protocol</h2>
          <p className="text-[var(--text-secondary)]">Condition: <span className="neon-text-cyan">{itinerary.current_weather}</span></p>
        </div>
        {itinerary.simulated && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-yellow-500/10 border border-yellow-500/20 text-yellow-500 text-xs font-bold uppercase tracking-wider">
            <Info size={14} /> Simulated Protocol
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 gap-6" role="list">
        <AnimatePresence mode="popLayout">
          {itinerary.events.map((event: any, index: number) => (
            <motion.div
              key={event.id || index}
              role="listitem"
              initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -20 }}
              animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
              exit={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
              transition={{ delay: index * 0.1 }}
              className="glass-card p-6 flex flex-col md:flex-row gap-6 relative overflow-hidden group"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-[var(--neon-cyan)] to-[var(--neon-purple)]" />
              
              <div className="flex-1">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <span className="text-xs font-mono text-[var(--neon-cyan)] uppercase tracking-widest mb-1 block">
                      Node {index + 1}
                    </span>
                    <h3 className="text-xl font-bold group-hover:neon-text-cyan transition-colors">
                      {event.name}
                    </h3>
                  </div>
                  <div className="flex items-center gap-1 text-[var(--neon-purple)] bg-[var(--neon-purple)]/10 px-2 py-1 rounded">
                    <Star size={14} fill="currentColor" />
                    <span className="text-xs font-bold">{event.priority || 'High'}</span>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-[var(--text-secondary)] mb-4">
                  <div className="flex items-center gap-2">
                    <Clock size={16} aria-hidden="true" /> {event.start_time} - {event.end_time}
                  </div>
                  <div className="flex items-center gap-2">
                    <MapPin size={16} aria-hidden="true" /> {event.location_name || 'Moscone Center'}
                  </div>
                </div>

                <div 
                  className="text-sm prose prose-invert max-w-none"
                  dangerouslySetInnerHTML={{ __html: sanitizeHtml(event.description || '') }}
                />
              </div>

              <div className="md:w-48 bg-[var(--bg-dark)]/50 rounded-xl p-4 border border-[var(--glass-border)] flex flex-col justify-center gap-2">
                <span className="text-[10px] uppercase tracking-wider text-[var(--text-secondary)] font-bold">Spatial Intelligence</span>
                <div className="text-xs">
                  <span className="text-[var(--text-secondary)]">Zone:</span> <span className="text-white">Moscone {event.zone || 'South'}</span>
                </div>
                <div className="text-xs">
                  <span className="text-[var(--text-secondary)]">Density:</span> <span className="text-[var(--neon-cyan)]">Low-Impact</span>
                </div>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  );
};

export default ItineraryDisplay;
