/**
 * Progressive Enhancement Utility
 *
 * Provides utilities for progressive enhancement and graceful degradation
 * when JavaScript is disabled or fails to load.
 */

import React from 'react';

// Component that only renders children when JavaScript is enabled
export const JavaScriptOnly: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [jsEnabled, setJsEnabled] = React.useState(false);

  React.useEffect(() => {
    setJsEnabled(true);
  }, []);

  return jsEnabled ? <>{children}</> : null;
};

// Component that provides fallback content when JavaScript is disabled
export const NoScriptFallback: React.FC<{
  children: React.ReactNode;
  fallback?: React.ReactNode;
}> = ({ children, fallback }) => (
  <>
    <JavaScriptOnly>{children}</JavaScriptOnly>
    <noscript>
      {fallback || (
        <div className="bg-yellow-500/20 text-yellow-400 p-4 rounded-md border border-yellow-500/30">
          <p className="font-medium">JavaScript Required</p>
          <p className="text-sm mt-1">
            This application requires JavaScript to function properly. Please enable JavaScript in
            your browser settings.
          </p>
        </div>
      )}
    </noscript>
  </>
);

// Progressive enhancement wrapper for forms
export const ProgressiveForm: React.FC<{
  children: React.ReactNode;
  action?: string;
  method?: string;
  className?: string;
}> = ({ children, action, method = 'POST', className }) => (
  <form action={action} method={method} className={className}>
    {children}
    <noscript>
      <div className="mt-4 p-3 bg-blue-500/20 text-blue-400 rounded-md text-sm">
        <p>Note: Some features may be limited without JavaScript enabled.</p>
      </div>
    </noscript>
  </form>
);

// Enhanced button that works without JavaScript
export const ProgressiveButton: React.FC<{
  children: React.ReactNode;
  onClick?: () => void;
  href?: string;
  type?: 'button' | 'submit' | 'reset';
  className?: string;
  disabled?: boolean;
}> = ({ children, onClick, href, type = 'button', className, disabled }) => {
  if (href) {
    return (
      <>
        <JavaScriptOnly>
          <button type={type} className={className} onClick={onClick} disabled={disabled}>
            {children}
          </button>
        </JavaScriptOnly>
        <noscript>
          <a href={href} className={className}>
            {children}
          </a>
        </noscript>
      </>
    );
  }

  return (
    <button type={type} className={className} onClick={onClick} disabled={disabled}>
      {children}
    </button>
  );
};
