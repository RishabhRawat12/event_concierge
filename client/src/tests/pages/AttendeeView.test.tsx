import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AttendeeView from '../../pages/AttendeeView';
import axios from 'axios';
import { BrowserRouter } from 'react-router-dom';

vi.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

describe('AttendeeView Integration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  const renderView = () => {
    return render(
      <BrowserRouter>
        <AttendeeView />
      </BrowserRouter>
    );
  };

  it('renders initial state with form', () => {
    renderView();
    expect(screen.getByText(/synthesize your experience/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /generate/i })).toBeInTheDocument();
  });

  it('handles successful itinerary generation', async () => {
    const mockData = {
      current_weather: 'Sunny',
      itinerary: [],
      events: [
        { name: 'Success Event', start_time: '1:00 PM', end_time: '2:00 PM', walking_directions: 'Walk', transition_time_seconds: 0 }
      ]
    };
    mockedAxios.post.mockResolvedValueOnce({ data: mockData });

    renderView();
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText('Success Event')).toBeInTheDocument();
    });
    expect(screen.getByText('Sunny')).toBeInTheDocument();
  });

  it('shows error message on API failure', async () => {
    mockedAxios.post.mockRejectedValueOnce(new Error('API Failure'));

    renderView();
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(screen.getByText(/operational failure/i)).toBeInTheDocument();
    });
  });

  it('displays loading state during request', async () => {
    mockedAxios.post.mockImplementationOnce(() => new Promise(resolve => setTimeout(() => resolve({ data: { events: [], current_weather: 'Done' } }), 100)));

    renderView();
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);

    // Form handles loading state by disabling button or showing spinner
    // In our ItineraryForm, the button is disabled and shows a spinner div
    expect(submitBtn).toBeDisabled();
    
    await waitFor(() => {
      expect(submitBtn).not.toBeDisabled();
    });
  });

  it('announces success to screen readers', async () => {
    mockedAxios.post.mockResolvedValueOnce({ data: { events: [], current_weather: 'Global' } });

    renderView();
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);

    await waitFor(() => {
      const announcer = document.getElementById('a11y-announcer');
      expect(announcer?.textContent).toBe('Tactical itinerary generated successfully.');
    });
  });
});
