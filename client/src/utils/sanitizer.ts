import DOMPurify from 'dompurify';

/**
 * Sanitizes AI-generated HTML content to protect against XSS vectors.
 * Implements strict policy focusing on structure and safe formatting.
 */
export const sanitizeHtml = (html: string): string => {
  return DOMPurify.sanitize(html, {
    ALLOWED_TAGS: [
      'b', 'i', 'em', 'strong', 'a', 'p', 'br', 'ul', 'ol', 'li', 'h3', 'h4', 'span'
    ],
    ALLOWED_ATTR: ['href', 'target', 'rel', 'class'],
    FORBID_TAGS: ['script', 'style', 'iframe', 'form', 'object', 'embed'],
    RETURN_DOM_FRAGMENT: false,
    RETURN_DOM_IMPORT: false,
  });
};
