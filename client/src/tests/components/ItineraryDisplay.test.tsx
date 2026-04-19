import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import ItineraryDisplay from '../../components/attendee/ItineraryDisplay';

const mockItinerary = {
  current_weather: 'Clear',
  simulated: false,
  events: [
    {
      id: 'e1',
      name: 'Keynote',
      start_time: '10:00 AM',
      end_time: '11:30 AM',
      description: '<strong>Amazing</strong> keynote',
      zone: 'South',
      priority: 'High'
    },
    {
      id: 'e2',
      name: 'Workshop',
      start_time: '01:00 PM',
      end_time: '02:30 PM',
      description: 'Hands-on session',
      zone: 'North',
      priority: 'Medium'
    }
  ]
};

describe('ItineraryDisplay', () => {
  it('renders nothing when itinerary is null', () => {
    const { container } = render(<ItineraryDisplay itinerary={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders weather condition', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText('Clear')).toBeInTheDocument();
  });

  it('renders all event names', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText('Keynote')).toBeInTheDocument();
    expect(screen.getByText('Workshop')).toBeInTheDocument();
  });

  it('renders sanitized HTML descriptions', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    const strong = screen.getByText('Amazing');
    expect(strong.tagName).toBe('STRONG');
  });

  it('shows simulated badge when appropriate', () => {
    const simulated = { ...mockItinerary, simulated: true };
    render(<ItineraryDisplay itinerary={simulated} />);
    expect(screen.getByText(/simulated protocol/i)).toBeInTheDocument();
  });

  it('does not show simulated badge for real itineraries', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.queryByText(/simulated protocol/i)).not.toBeInTheDocument();
  });

  it('displays event times correctly', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText(/10:00 AM - 11:30 AM/)).toBeInTheDocument();
  });

  it('renders zone information', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText(/Moscone South/i)).toBeInTheDocument();
    expect(screen.getByText(/Moscone North/i)).toBeInTheDocument();
  });

  it('applies priority highlights', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText('High')).toBeInTheDocument();
    expect(screen.getByText('Medium')).toBeInTheDocument();
  });

  it('renders node sequence identifying markers', () => {
    render(<ItineraryDisplay itinerary={mockItinerary} />);
    expect(screen.getByText(/Node 1/i)).toBeInTheDocument();
    expect(screen.getByText(/Node 2/i)).toBeInTheDocument();
  });

  it('handles missing descriptions gracefully', () => {
    const missingDesc = { ...mockItinerary, events: [{ ...mockItinerary.events[0], description: undefined }] };
    render(<ItineraryDisplay itinerary={missingDesc} />);
    expect(screen.getByText('Keynote')).toBeInTheDocument();
  });
});
