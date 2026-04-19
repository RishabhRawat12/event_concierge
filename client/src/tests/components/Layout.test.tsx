import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import Layout from '../../components/common/Layout';
import { BrowserRouter } from 'react-router-dom';

describe('Layout Component', () => {
  it('renders title correctly', () => {
    render(
      <BrowserRouter>
        <Layout title="Test Page"><div>Content</div></Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('Test Page')).toBeInTheDocument();
  });

  it('contains main-content id for skip links/navigation', () => {
    render(
      <BrowserRouter>
        <Layout title="Title"><div>Content</div></Layout>
      </BrowserRouter>
    );
    expect(document.getElementById('main-content')).toBeInTheDocument();
  });

  it('has accessibility live region', () => {
    render(
      <BrowserRouter>
        <Layout title="Title"><div>Content</div></Layout>
      </BrowserRouter>
    );
    const announcer = document.getElementById('a11y-announcer');
    expect(announcer).toBeInTheDocument();
    expect(announcer).toHaveAttribute('aria-live', 'polite');
  });

  it('renders navigation links', () => {
    render(
      <BrowserRouter>
        <Layout title="Title"><div>Content</div></Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('Attendee')).toBeInTheDocument();
    expect(screen.getByText('Staff')).toBeInTheDocument();
  });
  
  it('nav links have correct hrefs', () => {
    render(
      <BrowserRouter>
        <Layout title="Title"><div>Content</div></Layout>
      </BrowserRouter>
    );
    expect(screen.getByText('Attendee').closest('a')).toHaveAttribute('href', '/');
    expect(screen.getByText('Staff').closest('a')).toHaveAttribute('href', '/staff');
  });

  it('renders dynamic background blur elements', () => {
    const { container } = render(
      <BrowserRouter>
        <Layout title="Title"><div>Content</div></Layout>
      </BrowserRouter>
    );
    const blurElement = container.querySelector('.blur-\\[120px\\]');
    expect(blurElement).toBeInTheDocument();
  });
});
