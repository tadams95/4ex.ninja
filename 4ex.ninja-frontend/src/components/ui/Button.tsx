import { motion } from 'framer-motion';
import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

const buttonVariants = {
  primary: 'bg-primary-700 hover:bg-primary-800 text-white font-semibold border-transparent',
  secondary: 'bg-neutral-700 hover:bg-neutral-800 text-white font-semibold border-transparent',
  outline:
    'bg-transparent hover:bg-neutral-800 text-white font-semibold border border-neutral-600 hover:border-neutral-500',
  ghost: 'bg-transparent hover:bg-neutral-800 text-white font-medium border-transparent',
};

const buttonSizes = {
  sm: 'py-1.5 px-3 text-sm',
  md: 'py-2 px-4 text-base',
  lg: 'py-3 px-6 text-lg',
};

export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'md',
  loading = false,
  disabled,
  children,
  className = '',
  ...props
}) => {
  const baseClasses =
    'rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50 transition-colors duration-200 inline-flex items-center justify-center';
  const variantClasses = buttonVariants[variant];
  const sizeClasses = buttonSizes[size];
  const disabledClasses = disabled || loading ? 'opacity-50 cursor-not-allowed' : '';

  const buttonClasses =
    `${baseClasses} ${variantClasses} ${sizeClasses} ${disabledClasses} ${className}`.trim();

  const MotionButton = motion.button;

  return (
    <MotionButton
      className={buttonClasses}
      disabled={disabled || loading}
      whileHover={disabled || loading ? {} : { scale: 1.02 }}
      whileTap={disabled || loading ? {} : { scale: 0.98 }}
      {...(props as any)}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          ></circle>
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
      )}
      {children}
    </MotionButton>
  );
};
