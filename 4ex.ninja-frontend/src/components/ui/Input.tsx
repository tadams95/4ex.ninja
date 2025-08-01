import React from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  variant?: 'default' | 'rounded';
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  variant = 'default',
  className = '',
  id,
  ...props
}) => {
  const baseClasses =
    'appearance-none relative block w-full px-3 py-2 border bg-neutral-700 text-white placeholder-neutral-400 focus:outline-none focus:ring-primary-500 focus:border-primary-500 transition-colors duration-200';

  const variantClasses = {
    default: 'rounded-md',
    rounded: 'rounded-full',
  };

  const errorClasses = error
    ? 'border-error focus:ring-error focus:border-error'
    : 'border-neutral-600';

  const inputClasses =
    `${baseClasses} ${variantClasses[variant]} ${errorClasses} ${className}`.trim();

  const inputId = id || label?.toLowerCase().replace(/\s+/g, '-');

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-neutral-300 mb-1">
          {label}
        </label>
      )}
      <input id={inputId} className={inputClasses} {...props} />
      {error && (
        <p className="mt-1 text-sm text-error" role="alert">
          {error}
        </p>
      )}
      {helperText && !error && <p className="mt-1 text-sm text-neutral-400">{helperText}</p>}
    </div>
  );
};
