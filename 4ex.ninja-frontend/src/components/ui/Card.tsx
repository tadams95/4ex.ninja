import { motion } from 'framer-motion';
import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'elevated' | 'outlined';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hover?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  padding = 'md',
  hover = false,
}) => {
  const baseClasses = 'bg-neutral-800 rounded-lg transition-colors duration-200';

  const variantClasses = {
    default: '',
    elevated: 'shadow-lg',
    outlined: 'border border-neutral-600',
  };

  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const cardClasses =
    `${baseClasses} ${variantClasses[variant]} ${paddingClasses[padding]} ${className}`.trim();

  if (hover) {
    return (
      <motion.div
        className={cardClasses}
        whileHover={{ scale: 1.02, backgroundColor: 'rgb(55, 65, 81)' }}
        transition={{ duration: 0.2 }}
      >
        {children}
      </motion.div>
    );
  }

  return <div className={cardClasses}>{children}</div>;
};
