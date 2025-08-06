// Global Jest DOM type definitions for TypeScript
import '@testing-library/jest-dom';

declare global {
  namespace jest {
    interface Matchers<R> {
      toBeInTheDocument(): R;
      toHaveClass(className: string): R;
      toHaveStyle(style: string | object): R;
      toHaveAttribute(attr: string, value?: string): R;
      toBeVisible(): R;
      toBeDisabled(): R;
      toBeEnabled(): R;
      toHaveValue(value: string | number): R;
      toHaveDisplayValue(value: string | string[]): R;
      toBeChecked(): R;
      toHaveFocus(): R;
      toHaveTextContent(text: string | RegExp): R;
    }
  }
}

export {};
