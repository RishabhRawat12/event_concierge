import { describe, it, expect } from 'vitest';
import { sanitizeHtml } from '../../utils/sanitizer';

describe('HTML Sanitizer Utility', () => {
  it('allows safe tags', () => {
    const input = '<h3>Title</h3><p>Hello <b>World</b></p>';
    expect(sanitizeHtml(input)).toBe(input);
  });

  it('removes script tags', () => {
    const input = '<p>Hello</p><script>alert("xss")</script>';
    expect(sanitizeHtml(input)).toBe('<p>Hello</p>');
  });

  it('removes event handlers from attributes', () => {
    const input = '<button onclick="alert(\'xss\')">Click me</button>';
    // Button itself might be forbidden depending on the policy, let's check
    // In our policy: ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h3', 'h4', 'span']
    expect(sanitizeHtml(input)).toBe('Click me');
  });

  it('removes iframes and objects', () => {
    const input = '<div><iframe src="evil.com"></iframe><object data="evil"></object></div>';
    // div is not in allowed tags, so it might be stripped too or its content kept
    expect(sanitizeHtml(input)).toBe('');
  });

  it('allows safe attributes on links', () => {
    const input = '<a href="https://google.com" target="_blank" rel="noopener">Link</a>';
    expect(sanitizeHtml(input)).toContain('href="https://google.com"');
    expect(sanitizeHtml(input)).toContain('target="_blank"');
    expect(sanitizeHtml(input)).toContain('rel="noopener"');
  });

  it('handles malformed HTML gracefully', () => {
    const input = '<p>Unclosed tag<b>';
    expect(sanitizeHtml(input)).toBe('<p>Unclosed tag<b></b></p>');
  });

  it('strips style tags', () => {
    const input = '<style>body { color: red; }</style><p>Content</p>';
    expect(sanitizeHtml(input)).toBe('<p>Content</p>');
  });

  it('prevents javascript: pseudo-protocol in href', () => {
    const input = '<a href="javascript:alert(1)">Click</a>';
    expect(sanitizeHtml(input)).toBe('<a>Click</a>');
  });
});
