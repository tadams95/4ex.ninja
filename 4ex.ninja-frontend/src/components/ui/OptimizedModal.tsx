'use client';

import { useConditionalMotion } from '@/utils/animation';
import React, { useEffect, useState } from 'react';

export interface OptimizedModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl';
  className?: string;
  /**
   * Use CSS animations instead of framer-motion for better performance
   */
  useCSS?: boolean;
}

/**
 * Optimized Modal component that uses CSS animations for better performance
 * Falls back to framer-motion for complex animations when needed
 */
export const OptimizedModal: React.FC<OptimizedModalProps> = ({
  isOpen,
  onClose,
  title,
  children,
  size = 'md',
  className = '',
  useCSS = true,
}) => {
  const { motion, AnimatePresence, isLoaded, prefersReduced, loadMotion } = useConditionalMotion();
  const [isVisible, setIsVisible] = useState(false);
  const [shouldRender, setShouldRender] = useState(false);

  const sizeClasses = {
    sm: 'max-w-sm',
    md: 'max-w-md',
    lg: 'max-w-lg',
    xl: 'max-w-xl',
  };

  // Handle visibility state for CSS animations
  useEffect(() => {
    if (isOpen) {
      setShouldRender(true);
      // Small delay to trigger CSS animation
      setTimeout(() => setIsVisible(true), 10);
    } else {
      setIsVisible(false);
      // Wait for animation to complete before unmounting
      setTimeout(() => setShouldRender(false), 200);
    }
  }, [isOpen]);

  // Handle ESC key press
  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  // CSS-based modal implementation for better performance
  if (useCSS || prefersReduced) {
    if (!shouldRender) return null;

    const backdropClasses = `
      fixed inset-0 bg-black transition-opacity duration-200 gpu-accelerated
      ${isVisible ? 'opacity-75' : 'opacity-0'}
    `;

    const modalClasses = `
      relative bg-neutral-800 rounded-lg shadow-xl w-full mx-4 
      transform transition-all duration-200 gpu-accelerated will-change-transform
      ${sizeClasses[size]} ${className}
      ${isVisible ? 'opacity-100 scale-100 translate-y-0' : 'opacity-0 scale-95 translate-y-4'}
    `;

    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center">
        {/* Backdrop */}
        <div className={backdropClasses} onClick={onClose} />

        {/* Modal */}
        <div className={modalClasses}>
          {title && (
            <div className="flex items-center justify-between p-4 border-b border-neutral-600">
              <h3 className="text-lg font-semibold text-white">{title}</h3>
              <button
                onClick={onClose}
                className="text-neutral-400 hover:text-white transition-colors duration-200"
                aria-label="Close modal"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M6 18L18 6M6 6l12 12"
                  />
                </svg>
              </button>
            </div>
          )}

          <div className="p-4">{children}</div>
        </div>
      </div>
    );
  }

  // Load framer-motion for complex animations
  useEffect(() => {
    if (!useCSS) {
      loadMotion();
    }
  }, [useCSS, loadMotion]);

  // Framer-motion fallback for complex animations
  if (!isLoaded || !motion || !AnimatePresence) {
    // Use CSS fallback while motion loads
    return useCSS ? null : (
      <OptimizedModal {...{ isOpen, onClose, title, children, size, className }} useCSS={true} />
    );
  }

  const backdropVariants = {
    visible: { opacity: 1 },
    hidden: { opacity: 0 },
  };

  const modalVariants = {
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
    },
    hidden: {
      opacity: 0,
      scale: 0.95,
      y: 20,
    },
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 bg-black bg-opacity-75"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className={`relative bg-neutral-800 rounded-lg shadow-xl w-full mx-4 ${sizeClasses[size]} ${className}`}
            variants={modalVariants}
            initial="hidden"
            animate="visible"
            exit="hidden"
            transition={{ duration: 0.2 }}
          >
            {title && (
              <div className="flex items-center justify-between p-4 border-b border-neutral-600">
                <h3 className="text-lg font-semibold text-white">{title}</h3>
                <button
                  onClick={onClose}
                  className="text-neutral-400 hover:text-white transition-colors duration-200"
                  aria-label="Close modal"
                >
                  <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            )}

            <div className="p-4">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
