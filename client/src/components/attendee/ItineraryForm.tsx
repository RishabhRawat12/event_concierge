import React, { useState } from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { MapPin, Clock, Search } from 'lucide-react';
import { useValidation } from '../../hooks/useValidation';

interface ItineraryFormProps {
  onSubmit: (data: any) => void;
  isLoading: boolean;
}

const ItineraryForm: React.FC<ItineraryFormProps> = ({ onSubmit, isLoading }) => {
  const shouldReduceMotion = useReducedMotion();
  const [formData, setFormData] = useState({
    latitude: 37.7858,
    longitude: -122.4008,
    start_time: '10:00 AM',
    end_time: '06:00 PM',
    preferred_topics: ['AI', 'Cloud', 'Design'],
  });

  const { errors, validate } = useValidation();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const isValid = validate(formData, {
      latitude: (v) => (!v || v < -90 || v > 90 ? 'Invalid latitude' : null),
      longitude: (v) => (!v || v < -180 || v > 180 ? 'Invalid longitude' : null),
      start_time: (v) => (!v || !/^\d{1,2}:\d{2} [AP]M$/.test(v) ? 'Invalid time format (HH:MM AM/PM)' : null),
      end_time: (v) => (!v || !/^\d{1,2}:\d{2} [AP]M$/.test(v) ? 'Invalid time format (HH:MM AM/PM)' : null),
    });

    if (isValid) {
      onSubmit(formData);
    }
  };

  return (
    <motion.form 
      onSubmit={handleSubmit}
      className="glass-card p-8 flex flex-col gap-6"
      initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, scale: 0.95 }}
      animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, scale: 1 }}
      aria-label="Itinerary Constraints Form"
    >
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="flex flex-col gap-2">
          <label htmlFor="latitude" className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
            <MapPin size={16} className="text-[var(--neon-cyan)]" aria-hidden="true" /> Latitude
          </label>
          <input
            id="latitude"
            type="number"
            step="any"
            value={formData.latitude}
            onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
            className={`bg-[var(--bg-dark)] border ${errors.latitude ? 'border-[var(--error)]' : 'border-[var(--glass-border)]'} p-3 rounded-lg focus:outline-none focus:border-[var(--neon-cyan)] transition-colors`}
            aria-invalid={!!errors.latitude}
            aria-describedby={errors.latitude ? "lat-error" : undefined}
          />
          {errors.latitude && <span id="lat-error" className="text-[var(--error)] text-xs">{errors.latitude}</span>}
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="longitude" className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
            <MapPin size={16} className="text-[var(--neon-cyan)]" aria-hidden="true" /> Longitude
          </label>
          <input
            id="longitude"
            type="number"
            step="any"
            value={formData.longitude}
            onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
            className={`bg-[var(--bg-dark)] border ${errors.longitude ? 'border-[var(--error)]' : 'border-[var(--glass-border)]'} p-3 rounded-lg focus:outline-none focus:border-[var(--neon-cyan)] transition-colors`}
            aria-invalid={!!errors.longitude}
            aria-describedby={errors.longitude ? "lon-error" : undefined}
          />
          {errors.longitude && <span id="lon-error" className="text-[var(--error)] text-xs">{errors.longitude}</span>}
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="start_time" className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
            <Clock size={16} className="text-[var(--neon-purple)]" aria-hidden="true" /> Start Time (HH:MM AM/PM)
          </label>
          <input
            id="start_time"
            type="text"
            placeholder="10:00 AM"
            value={formData.start_time}
            onChange={(e) => setFormData({ ...formData, start_time: e.target.value })}
            className={`bg-[var(--bg-dark)] border ${errors.start_time ? 'border-[var(--error)]' : 'border-[var(--glass-border)]'} p-3 rounded-lg focus:outline-none focus:border-[var(--neon-purple)] transition-colors`}
            aria-invalid={!!errors.start_time}
          />
        </div>

        <div className="flex flex-col gap-2">
          <label htmlFor="end_time" className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
            <Clock size={16} className="text-[var(--neon-purple)]" aria-hidden="true" /> End Time (HH:MM AM/PM)
          </label>
          <input
            id="end_time"
            type="text"
            placeholder="06:00 PM"
            value={formData.end_time}
            onChange={(e) => setFormData({ ...formData, end_time: e.target.value })}
            className={`bg-[var(--bg-dark)] border ${errors.end_time ? 'border-[var(--error)]' : 'border-[var(--glass-border)]'} p-3 rounded-lg focus:outline-none focus:border-[var(--neon-purple)] transition-colors`}
            aria-invalid={!!errors.end_time}
          />
        </div>
      </div>

      <div className="flex flex-col gap-2">
        <label htmlFor="topics" className="text-sm font-medium text-[var(--text-secondary)] flex items-center gap-2">
          <Search size={16} className="text-[var(--neon-pink)]" aria-hidden="true" /> Preferred Topics
        </label>
        <input
          id="topics"
          type="text"
          value={formData.preferred_topics.join(', ')}
          onChange={(e) => setFormData({ ...formData, preferred_topics: e.target.value.split(',').map(s => s.trim()) })}
          placeholder="e.g. AI, Cloud, Design"
          className="bg-[var(--bg-dark)] border border-[var(--glass-border)] p-3 rounded-lg focus:outline-none focus:border-[var(--neon-pink)] transition-colors"
        />
      </div>

      <button
        type="submit"
        disabled={isLoading}
        className={`primary-button flex items-center justify-center gap-2 mt-4 ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}`}
        aria-busy={isLoading}
      >
        {isLoading ? (
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full"
            role="status"
            aria-label="Loading"
          />
        ) : (
          <>Generate Tactical Itinerary</>
        )}
      </button>
    </motion.form>
  );
};

export default ItineraryForm;
