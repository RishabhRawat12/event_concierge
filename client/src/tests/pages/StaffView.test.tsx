import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import StaffView from '../../pages/StaffView';
import { subscribeToAuthChanges, loginWithGoogle } from '../../services/auth';
import { BrowserRouter } from 'react-router-dom';

vi.mock('../../services/auth');
const mockedAuth = vi.mocked({ subscribeToAuthChanges, loginWithGoogle });

describe('StaffView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login prompt when not authenticated', () => {
    mockedAuth.subscribeToAuthChanges.mockImplementation((cb: any) => {
      cb(null);
      return () => {};
    });

    render(<BrowserRouter><StaffView /></BrowserRouter>);
    expect(screen.getByText(/tactical access required/i)).toBeInTheDocument();
    expect(screen.getByText(/authenticate via command center/i)).toBeInTheDocument();
  });

  it('calls login function on button click', () => {
    mockedAuth.subscribeToAuthChanges.mockImplementation((cb: any) => {
      cb(null);
      return () => {};
    });

    render(<BrowserRouter><StaffView /></BrowserRouter>);
    fireEvent.click(screen.getByText(/authenticate via command center/i));
    expect(mockedAuth.loginWithGoogle).toHaveBeenCalled();
  });

  it('renders tactical dashboard when authenticated', () => {
    mockedAuth.subscribeToAuthChanges.mockImplementation((cb: any) => {
      cb({ displayName: 'Officer Alice', email: 'alice@event.com' });
      return () => {};
    });

    render(<BrowserRouter><StaffView /></BrowserRouter>);
    expect(screen.getByText(/venue tactical twin/i)).toBeInTheDocument();
    expect(screen.getByText('Officer Alice')).toBeInTheDocument();
  });

  it('contains zone trigger buttons', () => {
     mockedAuth.subscribeToAuthChanges.mockImplementation((cb: any) => {
      cb({ displayName: 'Officer Alice', email: 'alice@event.com' });
      return () => {};
    });

    render(<BrowserRouter><StaffView /></BrowserRouter>);
    expect(screen.getByText('Gate 4')).toBeInTheDocument();
    expect(screen.getAllByText(/trigger tactical overlay/i)).toHaveLength(4);
  });
});
