/**
 * Theme Utility Functions
 *
 * This module provides utility functions for working with the design token system
 * and CSS custom properties. These utilities help bridge the gap between TypeScript
 * and CSS for dynamic theming and consistent styling.
 */

import { designTokens } from '../styles/tokens';

/**
 * Get a CSS custom property value
 * @param property - The CSS custom property name (without --)
 * @returns The CSS custom property value as a string
 */
export function getCSSCustomProperty(property: string): string {
  return `var(--${property})`;
}

/**
 * Get a design token as a CSS custom property
 * @param tokenPath - The path to the token (e.g., 'color.primary.600')
 * @returns The CSS custom property value
 */
export function getTokenAsCSSVar(tokenPath: string): string {
  const cssVarName = tokenPath.replace(/\./g, '-');
  return getCSSCustomProperty(cssVarName);
}

/**
 * Theme utilities for common patterns
 */
export const theme = {
  /**
   * Color utilities
   */
  colors: {
    primary: (
      shade:
        | '50'
        | '100'
        | '200'
        | '300'
        | '400'
        | '500'
        | '600'
        | '700'
        | '800'
        | '900'
        | '950' = '600'
    ) => getCSSCustomProperty(`color-primary-${shade}`),
    neutral: (
      shade:
        | '50'
        | '100'
        | '200'
        | '300'
        | '400'
        | '500'
        | '600'
        | '700'
        | '800'
        | '900'
        | '950' = '500'
    ) => getCSSCustomProperty(`color-neutral-${shade}`),
    success: () => getCSSCustomProperty('color-success'),
    warning: () => getCSSCustomProperty('color-warning'),
    error: () => getCSSCustomProperty('color-error'),
    info: () => getCSSCustomProperty('color-info'),
    background: {
      primary: () => getCSSCustomProperty('color-background-primary'),
      secondary: () => getCSSCustomProperty('color-background-secondary'),
      tertiary: () => getCSSCustomProperty('color-background-tertiary'),
    },
    text: {
      primary: () => getCSSCustomProperty('color-text-primary'),
      secondary: () => getCSSCustomProperty('color-text-secondary'),
      tertiary: () => getCSSCustomProperty('color-text-tertiary'),
      muted: () => getCSSCustomProperty('color-text-muted'),
    },
    border: {
      primary: () => getCSSCustomProperty('color-border-primary'),
      secondary: () => getCSSCustomProperty('color-border-secondary'),
      muted: () => getCSSCustomProperty('color-border-muted'),
    },
  },

  /**
   * Typography utilities
   */
  typography: {
    fontSize: (size: keyof typeof designTokens.typography.fontSizes) =>
      getCSSCustomProperty(`font-size-${String(size)}`),
    fontWeight: (weight: keyof typeof designTokens.typography.fontWeights) =>
      getCSSCustomProperty(`font-weight-${String(weight)}`),
    lineHeight: (height: keyof typeof designTokens.typography.lineHeights) =>
      getCSSCustomProperty(`line-height-${String(height)}`),
  },

  /**
   * Spacing utilities
   */
  spacing: (size: keyof typeof designTokens.spacing) =>
    getCSSCustomProperty(`spacing-${String(size)}`),

  /**
   * Border radius utilities
   */
  radius: (size: keyof typeof designTokens.borderRadius) =>
    getCSSCustomProperty(`radius-${String(size)}`),

  /**
   * Shadow utilities
   */
  shadow: (size: keyof typeof designTokens.shadows) =>
    getCSSCustomProperty(`shadow-${String(size)}`),

  /**
   * Transition utilities
   */
  transition: {
    duration: (speed: keyof typeof designTokens.transitions.duration) =>
      getCSSCustomProperty(`transition-${String(speed)}`),
    easing: (type: keyof typeof designTokens.transitions.timing) =>
      getCSSCustomProperty(`transition-${String(type)}`),
  },

  /**
   * Z-index utilities
   */
  zIndex: (layer: keyof typeof designTokens.zIndex) => getCSSCustomProperty(`z-${String(layer)}`),
};

/**
 * Create inline styles using design tokens
 * @param styles - Object with CSS properties using design tokens
 * @returns React CSSProperties object
 */
export function createTokenStyles(styles: Record<string, string>): Record<string, string> {
  return styles;
}

/**
 * Responsive utilities for breakpoints
 */
export const breakpoints = {
  isMobile: () => `(max-width: ${designTokens.breakpoints.sm})`,
  isTablet: () =>
    `(min-width: ${designTokens.breakpoints.sm}) and (max-width: ${designTokens.breakpoints.lg})`,
  isDesktop: () => `(min-width: ${designTokens.breakpoints.lg})`,
  isLarge: () => `(min-width: ${designTokens.breakpoints.xl})`,
};

/**
 * Animation helpers
 */
export const animations = {
  /**
   * Create a transition string with design tokens
   */
  createTransition: (
    property: string = 'all',
    duration: keyof typeof designTokens.transitions.duration = 'normal',
    easing: keyof typeof designTokens.transitions.timing = 'ease'
  ) => {
    return `${property} ${theme.transition.duration(duration)} ${theme.transition.easing(easing)}`;
  },

  /**
   * Common transition presets
   */
  presets: {
    fast: 'all var(--transition-fast) var(--transition-ease)',
    normal: 'all var(--transition-normal) var(--transition-ease)',
    slow: 'all var(--transition-slow) var(--transition-ease)',
    colors:
      'color var(--transition-normal) var(--transition-ease), background-color var(--transition-normal) var(--transition-ease), border-color var(--transition-normal) var(--transition-ease)',
    transform: 'transform var(--transition-normal) var(--transition-ease)',
    opacity: 'opacity var(--transition-normal) var(--transition-ease)',
  },
};

/**
 * CSS-in-JS helpers for styled-components or emotion
 */
export const css = {
  /**
   * Helper for CSS-in-JS libraries
   */
  theme: (tokenPath: string) => getTokenAsCSSVar(tokenPath),

  /**
   * Common CSS patterns using design tokens
   */
  patterns: {
    card: `
      background-color: ${theme.colors.background.secondary()};
      border: 1px solid ${theme.colors.border.primary()};
      border-radius: ${theme.radius('md')};
      box-shadow: ${theme.shadow('sm')};
      transition: ${animations.presets.normal};
    `,
    button: `
      border-radius: ${theme.radius('base')};
      font-weight: ${theme.typography.fontWeight('medium')};
      transition: ${animations.presets.colors};
    `,
    input: `
      border: 1px solid ${theme.colors.border.primary()};
      border-radius: ${theme.radius('base')};
      background-color: ${theme.colors.background.secondary()};
      color: ${theme.colors.text.primary()};
      transition: ${animations.presets.colors};
    `,
  },
};

export default theme;
