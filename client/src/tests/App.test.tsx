import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from '../App';

describe('App Root', () => {
  it('renders the AttendeeView by default', () => {
    render(<App />);
    expect(screen.getByText(/event concierge · attendee portal/i)).toBeInTheDocument();
  });

  it('renders the main heading', () => {
    render(<App />);
    expect(screen.getByText(/synthesize your experience/i)).toBeInTheDocument();
  });

  it('can navigate to the staff entrance', async () => {
    render(<App />);
    const staffLink = screen.getByText('Staff');
    fireEvent.click(staffLink);
    // Use findByText to handle the component loading state
    expect(await screen.findByText(/staff intelligence/i)).toBeInTheDocument();
  });
});
