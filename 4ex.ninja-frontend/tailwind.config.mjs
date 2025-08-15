import { designTokens } from './src/styles/tokens.ts';

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  darkMode: ['class'],
  safelist: ['dark'],
  theme: {
    extend: {
      // Design Token Integration
      colors: {
        // Keep existing CSS custom properties
        background: 'var(--background)',
        foreground: 'var(--foreground)',

        // Add design token colors
        primary: designTokens.colors.primary,
        neutral: designTokens.colors.neutral,
        semantic: designTokens.colors.semantic,

        // Enhanced: Add new color categories
        accent: designTokens.colors.accent,
        interactive: designTokens.colors.interactive,

        // Semantic aliases for better DX
        success: designTokens.colors.semantic.success,
        warning: designTokens.colors.semantic.warning,
        error: designTokens.colors.semantic.error,
        info: designTokens.colors.semantic.info,
        positive: designTokens.colors.semantic.positive,
        destructive: designTokens.colors.semantic.destructive,
      },

      // Typography
      fontFamily: {
        sans: designTokens.typography.fontFamilies.sans,
        mono: designTokens.typography.fontFamilies.mono,
      },
      fontSize: designTokens.typography.fontSizes,
      fontWeight: designTokens.typography.fontWeights,
      lineHeight: designTokens.typography.lineHeights,
      letterSpacing: designTokens.typography.letterSpacing,

      // Spacing (extends default Tailwind spacing)
      spacing: designTokens.spacing,

      // Border Radius
      borderRadius: designTokens.borderRadius,

      // Box Shadow
      boxShadow: designTokens.shadows,

      // Animation & Transitions
      transitionDuration: designTokens.transitions.duration,
      transitionTimingFunction: designTokens.transitions.timing,

      // Z-Index
      zIndex: designTokens.zIndex,

      // Breakpoints (screens in Tailwind)
      screens: designTokens.breakpoints,
    },
  },
  plugins: [],
};
