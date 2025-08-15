/**
 * Design Tokens for 4ex.ninja
 *
 * This file contains all design tokens used throughout the application.
 * These tokens ensure consistency and make it easy to maintain the design system.
 */

// Color Palette
export const colors = {
  // Primary colors (Green - brand color)
  primary: {
    50: '#f0fdf4',
    100: '#dcfce7',
    200: '#bbf7d0',
    300: '#86efac',
    400: '#4ade80',
    500: '#22c55e', // Main green
    600: '#16a34a',
    700: '#15803d', // Current primary green
    800: '#166534',
    900: '#14532d',
    950: '#052e16',
  },

  // Neutral colors (Grays) - Enhanced for better accessibility
  neutral: {
    50: '#f9fafb',
    100: '#f3f4f6',
    200: '#e5e7eb',
    300: '#d1d5db',
    400: '#9ca3af',
    500: '#6b7280',
    600: '#4b5563',
    700: '#374151',
    800: '#1f2937',
    900: '#111827',
    925: '#0c1220', // Enhanced: Softer than pure black
    950: '#080b14', // Enhanced: New darkest level
    975: '#040507', // Enhanced: Near black but not pure
  },

  // Enhanced semantic colors with better accessibility
  semantic: {
    success: '#22c55e', // Green - kept for brand consistency
    warning: '#f59e0b', // Amber
    error: '#ef4444', // Red
    info: '#3b82f6', // Blue
    // New additions for better semantic range
    neutral: '#6b7280', // For neutral actions
    'info-secondary': '#06b6d4', // Cyan for secondary info
    destructive: '#dc2626', // Stronger red for destructive actions
    positive: '#059669', // Emerald for positive feedback
  },

  // Enhanced background colors with smoother transitions
  background: {
    primary: '#080b14', // Enhanced: Softer than pure black
    secondary: '#0c1220', // Enhanced: Better transition
    tertiary: '#1f2937', // Current gray-800
    quaternary: '#374151', // Current gray-700 - added level
    elevated: '#4b5563', // Enhanced: For elevated components
  },

  // Enhanced text colors with better contrast ratios
  text: {
    primary: '#f8fafc', // Enhanced: Softer white for better readability
    secondary: '#e2e8f0', // Enhanced: Better contrast
    tertiary: '#cbd5e1', // Enhanced: Improved hierarchy
    muted: '#94a3b8', // Enhanced: Better muted text
    'on-primary': '#ffffff', // Enhanced: Text on primary green
    'on-surface': '#f1f5f9', // Enhanced: General surface text
    disabled: '#64748b', // Enhanced: Clear disabled state
  },

  // Enhanced border colors with better definition
  border: {
    primary: '#334155', // Enhanced: Better visibility
    secondary: '#475569', // Enhanced: Secondary borders
    muted: '#1e293b', // Enhanced: Subtle borders
    focus: '#3b82f6', // Enhanced: Dedicated focus color
    'focus-ring': 'rgba(59, 130, 246, 0.5)', // Enhanced: Focus ring
  },

  // New: Interactive state colors for better UX
  interactive: {
    'hover-primary': 'rgba(34, 197, 94, 0.1)', // Green hover overlay
    'hover-secondary': 'rgba(148, 163, 184, 0.1)', // Neutral hover
    'hover-surface': 'rgba(248, 250, 252, 0.05)', // Surface hover
    'active-primary': 'rgba(34, 197, 94, 0.2)', // Green active state
    'active-secondary': 'rgba(148, 163, 184, 0.2)', // Neutral active
  },

  // New: Accent colors for better variety and color-blind accessibility
  accent: {
    blue: '#3b82f6', // Complementary to green
    purple: '#8b5cf6', // Additional accent
    cyan: '#06b6d4', // Info accent
    orange: '#f97316', // Warning accent
    pink: '#ec4899', // Special accent
  },
} as const;

// Typography Scale
export const typography = {
  fontFamilies: {
    sans: [
      'Exo',
      'system-ui',
      '-apple-system',
      'BlinkMacSystemFont',
      'Segoe UI',
      'Roboto',
      'Helvetica Neue',
      'Arial',
      'sans-serif',
    ],
    mono: [
      'ui-monospace',
      'SFMono-Regular',
      'Monaco',
      'Consolas',
      'Liberation Mono',
      'Courier New',
      'monospace',
    ],
  },

  fontSizes: {
    xs: '0.75rem', // 12px
    sm: '0.875rem', // 14px
    base: '1rem', // 16px
    lg: '1.125rem', // 18px
    xl: '1.25rem', // 20px
    '2xl': '1.5rem', // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem', // 36px
  },

  fontWeights: {
    light: '300',
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },

  lineHeights: {
    tight: '1.25',
    snug: '1.375',
    normal: '1.5',
    relaxed: '1.625',
    loose: '2',
  },

  letterSpacing: {
    tighter: '-0.05em',
    tight: '-0.025em',
    normal: '0',
    wide: '0.025em',
    wider: '0.05em',
    widest: '0.1em',
  },
} as const;

// Spacing Scale (consistent with Tailwind's default scale)
export const spacing = {
  0: '0',
  px: '1px',
  0.5: '0.125rem', // 2px
  1: '0.25rem', // 4px
  1.5: '0.375rem', // 6px
  2: '0.5rem', // 8px
  2.5: '0.625rem', // 10px
  3: '0.75rem', // 12px
  3.5: '0.875rem', // 14px
  4: '1rem', // 16px
  5: '1.25rem', // 20px
  6: '1.5rem', // 24px
  7: '1.75rem', // 28px
  8: '2rem', // 32px
  9: '2.25rem', // 36px
  10: '2.5rem', // 40px
  11: '2.75rem', // 44px
  12: '3rem', // 48px
  14: '3.5rem', // 56px
  16: '4rem', // 64px
  20: '5rem', // 80px
  24: '6rem', // 96px
  28: '7rem', // 112px
  32: '8rem', // 128px
} as const;

// Border Radius Values
export const borderRadius = {
  none: '0',
  sm: '0.25rem', // 4px
  base: '0.375rem', // 6px (default)
  md: '0.5rem', // 8px
  lg: '0.75rem', // 12px
  xl: '1rem', // 16px
  '2xl': '1.5rem', // 24px
  '3xl': '2rem', // 32px
  full: '9999px',
} as const;

// Shadow/Elevation System
export const shadows = {
  xs: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  sm: '0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1)',
  base: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  none: '0 0 #0000',
} as const;

// Animation/Transition Tokens
export const transitions = {
  duration: {
    fast: '150ms',
    normal: '200ms',
    slow: '300ms',
    slower: '500ms',
  },

  timing: {
    ease: 'cubic-bezier(0.4, 0, 0.2, 1)',
    easeIn: 'cubic-bezier(0.4, 0, 1, 1)',
    easeOut: 'cubic-bezier(0, 0, 0.2, 1)',
    easeInOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
  },
} as const;

// Breakpoints (responsive design)
export const breakpoints = {
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// Z-Index Scale
export const zIndex = {
  hide: -1,
  auto: 'auto',
  base: 0,
  docked: 10,
  dropdown: 1000,
  sticky: 1100,
  banner: 1200,
  overlay: 1300,
  modal: 1400,
  popover: 1500,
  skipLink: 1600,
  toast: 1700,
  tooltip: 1800,
} as const;

// Design Tokens Export
export const designTokens = {
  colors,
  typography,
  spacing,
  borderRadius,
  shadows,
  transitions,
  breakpoints,
  zIndex,
} as const;

// Type definitions for TypeScript
export type ColorToken = keyof typeof colors;
export type TypographyToken = keyof typeof typography;
export type SpacingToken = keyof typeof spacing;
export type BorderRadiusToken = keyof typeof borderRadius;
export type ShadowToken = keyof typeof shadows;
export type TransitionToken = keyof typeof transitions;
export type BreakpointToken = keyof typeof breakpoints;
export type ZIndexToken = keyof typeof zIndex;
