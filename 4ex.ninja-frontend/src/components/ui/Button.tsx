import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
  enableMotion?: boolean;
}

const buttonVariants = {
  primary:
    'bg-primary-700 hover:bg-primary-800 active:bg-primary-900 text-white font-semibold border-transparent focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50',
  secondary:
    'bg-neutral-700 hover:bg-neutral-600 active:bg-neutral-500 text-white font-semibold border-transparent focus:ring-2 focus:ring-neutral-400 focus:ring-opacity-50',
  outline:
    'bg-transparent hover:bg-primary-700/10 active:bg-primary-700/20 text-primary-400 font-semibold border border-primary-400 hover:border-primary-300 hover:text-primary-300 focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50',
  ghost:
    'bg-transparent hover:bg-neutral-800 active:bg-neutral-700 text-white font-medium border-transparent focus:ring-2 focus:ring-neutral-400 focus:ring-opacity-30',
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
  enableMotion = false,
  ...props
}) => {
  const baseClasses =
    'rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-opacity-50 transition-all duration-200 inline-flex items-center justify-center';
  const variantClasses = buttonVariants[variant];
  const sizeClasses = buttonSizes[size];
  const disabledClasses = disabled || loading ? 'opacity-50 cursor-not-allowed' : '';

  // Hardware-accelerated hover effects using CSS
  const motionClasses =
    enableMotion && !disabled && !loading
      ? 'transform hover:scale-[1.02] active:scale-[0.98] will-change-transform gpu-accelerated'
      : '';

  const buttonClasses =
    `${baseClasses} ${variantClasses} ${sizeClasses} ${disabledClasses} ${motionClasses} ${className}`.trim();

  // Use CSS transitions for better performance instead of framer-motion for simple interactions
  return (
    <button className={buttonClasses} disabled={disabled || loading} {...props}>
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
    </button>
  );
};
