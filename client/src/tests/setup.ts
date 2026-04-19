import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Global Mocks for Firebase
vi.mock('firebase/app', () => ({
  initializeApp: vi.fn(() => ({})),
}));

vi.mock('firebase/auth', () => ({
  getAuth: vi.fn(),
  signInWithPopup: vi.fn(),
  signOut: vi.fn(),
  GoogleAuthProvider: vi.fn(),
  onAuthStateChanged: vi.fn((auth, callback) => {
    callback(null);
    return vi.fn();
  }),
}));

vi.mock('firebase/firestore', () => ({
  getFirestore: vi.fn(() => ({})),
}));

// Mock ResizeObserver for framer-motion
global.ResizeObserver = vi.fn().mockImplementation(() => ({
    observe: vi.fn(),
    unobserve: vi.fn(),
    disconnect: vi.fn(),
}));

// Mock import.meta.env
vi.stubGlobal('import', {
  meta: {
    env: {
      VITE_FIREBASE_API_KEY: 'mock-key',
      VITE_FIREBASE_AUTH_DOMAIN: 'mock-domain',
      VITE_FIREBASE_PROJECT_ID: 'mock-id',
      VITE_FIREBASE_STORAGE_BUCKET: 'mock-bucket',
      VITE_FIREBASE_MESSAGING_SENDER_ID: 'mock-sender',
      VITE_FIREBASE_APP_ID: 'mock-app-id',
    }
  }
});
