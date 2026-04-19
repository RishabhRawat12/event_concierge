import React, { useState } from 'react';
import axios from 'axios';
import Layout from '../components/common/Layout';
import ItineraryForm from '../components/attendee/ItineraryForm';
import ItineraryDisplay from '../components/attendee/ItineraryDisplay';

const AttendeeView: React.FC = () => {
  const [itinerary, setItinerary] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGenerate = async (formData: any) => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.post(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/itinerary`, 
        formData
      );
      setItinerary(response.data);
      
      // Announce for screen readers
      const announcer = document.getElementById('a11y-announcer');
      if (announcer) announcer.textContent = 'Tactical itinerary generated successfully.';
    } catch (err: any) {
      console.error(err);
      setError('Operational failure: Unable to synthesize itinerary. Please verify your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout title="Event Concierge · Attendee Portal">
      <div className="max-w-4xl mx-auto py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-extrabold mb-4 bg-gradient-to-r from-[var(--neon-cyan)] to-[var(--neon-purple)] bg-clip-text text-transparent">
            Synthesize Your Experience
          </h2>
          <p className="text-[var(--text-secondary)] text-lg">
            Deploy advanced AI to orchestrate your event timeline based on real-time spatial data.
          </p>
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-lg bg-[var(--error)]/10 border border-[var(--error)]/20 text-[var(--error)] text-sm flex items-center gap-3">
            <span className="font-bold">ALERT:</span> {error}
          </div>
        )}

        <ItineraryForm onSubmit={handleGenerate} isLoading={loading} />
        
        <ItineraryDisplay itinerary={itinerary} />
      </div>
    </Layout>
  );
};

export default AttendeeView;
