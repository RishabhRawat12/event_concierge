import React from 'react';
import { motion, useReducedMotion } from 'framer-motion';
import { Link } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
  title: string;
}

const Layout: React.FC<LayoutProps> = ({ children, title }) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div className="min-h-screen relative">
      {/* Dynamic Background Elements */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none -z-10">
        <div className="absolute top-[-10%] left-[-5%] w-[40%] h-[40%] bg-[var(--neon-purple)] opacity-10 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-5%] w-[40%] h-[40%] bg-[var(--neon-cyan)] opacity-10 blur-[120px]" />
      </div>

      <header className="p-6 border-b border-[var(--glass-border)] glass-card rounded-none sticky top-0 z-50">
        <div className="max-w-7xl mx-auto flex justify-between items-center">
          <motion.h1 
            initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, x: -20 }}
            animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, x: 0 }}
            className="text-2xl font-bold neon-text-cyan"
            id="main-nav-title"
          >
            {title}
          </motion.h1>
          <nav aria-labelledby="main-nav-title">
            <ul className="flex space-x-6 list-none">
              <li><Link to="/" className="text-white hover:text-[var(--neon-cyan)] transition-colors">Attendee</Link></li>
              <li><Link to="/staff" className="text-white hover:text-[var(--neon-purple)] transition-colors">Staff</Link></li>
            </ul>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6" id="main-content">
        <motion.div
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 20 }}
          animate={shouldReduceMotion ? { opacity: 1 } : { opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {children}
        </motion.div>
      </main>

      {/* Accessibility Live Region for Dynamic Updates */}
      <div className="sr-only" aria-live="polite" id="a11y-announcer"></div>
    </div>
  );
};

export default Layout;
