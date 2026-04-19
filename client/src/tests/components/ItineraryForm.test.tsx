import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import ItineraryForm from '../../components/attendee/ItineraryForm';

describe('ItineraryForm', () => {
  it('renders input fields correctly', () => {
    render(<ItineraryForm onSubmit={vi.fn()} isLoading={false} />);
    
    expect(screen.getByLabelText(/latitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/longitude/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/start time/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/end time/i)).toBeInTheDocument();
  });

  it('shows error message on invalid latitude', () => {
    const handleSubmit = vi.fn();
    render(<ItineraryForm onSubmit={handleSubmit} isLoading={false} />);
    
    const latInput = screen.getByLabelText(/latitude/i);
    fireEvent.change(latInput, { target: { value: '100' } });
    
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);
    
    expect(screen.getByText(/invalid latitude/i)).toBeInTheDocument();
    expect(handleSubmit).not.toHaveBeenCalled();
  });

  it('calls onSubmit with valid data', () => {
    const handleSubmit = vi.fn();
    render(<ItineraryForm onSubmit={handleSubmit} isLoading={false} />);
    
    const submitBtn = screen.getByRole('button', { name: /generate/i });
    fireEvent.click(submitBtn);
    
    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      latitude: 37.7858,
      longitude: -122.4008
    }));
  });

  it('shows error on missing longitude', () => {
    render(<ItineraryForm onSubmit={vi.fn()} isLoading={false} />);
    const lonInput = screen.getByLabelText(/longitude/i);
    fireEvent.change(lonInput, { target: { value: '' } });
    
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(screen.getByText(/invalid longitude/i)).toBeInTheDocument();
  });

  it('shows error on out-of-bounds longitude', () => {
    render(<ItineraryForm onSubmit={vi.fn()} isLoading={false} />);
    const lonInput = screen.getByLabelText(/longitude/i);
    fireEvent.change(lonInput, { target: { value: '200' } });
    
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(screen.getByText(/invalid longitude/i)).toBeInTheDocument();
  });

  it('updates preferred topics on input change', () => {
    const handleSubmit = vi.fn();
    render(<ItineraryForm onSubmit={handleSubmit} isLoading={false} />);
    const topicsInput = screen.getByLabelText(/preferred topics/i);
    fireEvent.change(topicsInput, { target: { value: 'Hardware, Security' } });
    
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      preferred_topics: ['Hardware', 'Security']
    }));
  });

  it('trims whitespace from topics', () => {
    const handleSubmit = vi.fn();
    render(<ItineraryForm onSubmit={handleSubmit} isLoading={false} />);
    const topicsInput = screen.getByLabelText(/preferred topics/i);
    fireEvent.change(topicsInput, { target: { value: ' AI , Cloud ' } });
    
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      preferred_topics: ['AI', 'Cloud']
    }));
  });

  it('handles negative coordinates correctly', () => {
    const handleSubmit = vi.fn();
    render(<ItineraryForm onSubmit={handleSubmit} isLoading={false} />);
    fireEvent.change(screen.getByLabelText(/latitude/i), { target: { value: '-33.86' } });
    fireEvent.change(screen.getByLabelText(/longitude/i), { target: { value: '151.20' } });
    
    fireEvent.click(screen.getByRole('button', { name: /generate/i }));
    expect(handleSubmit).toHaveBeenCalledWith(expect.objectContaining({
      latitude: -33.86,
      longitude: 151.20
    }));
  });

  it('shows loading spinner when isLoading is true', () => {
    render(<ItineraryForm onSubmit={vi.fn()} isLoading={true} />);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
    // The spinner is a motion div with certain classes/roles if defined, 
    // but here we just check it doesn't have the text
    expect(screen.queryByText(/generate tactical itinerary/i)).not.toBeInTheDocument();
  });
});
