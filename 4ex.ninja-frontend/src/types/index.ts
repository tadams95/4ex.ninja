// Core type definitions for 4ex.ninja frontend

export interface User {
  id?: string;
  email?: string | null;
  name?: string | null;
  image?: string | null;
  isSubscribed?: boolean;
  subscriptionEnds?: string | Date;
  stripeCustomerId?: string;
  createdAt?: string | Date;
  updatedAt?: string | Date;
}

export interface Crossover {
  _id: string;
  pair: string;
  crossoverType: 'BULLISH' | 'BEARISH';
  timeframe: string;
  fastMA: number;
  slowMA: number;
  price: string;
  timestamp: string | Date;
  signal?: 'Buy' | 'Sell';
  close?: number;
  time?: string | Date;
}

export interface ApiResponse<T = any> {
  success?: boolean;
  data?: T;
  error?: string;
  message?: string;
  crossovers?: Crossover[];
  isEmpty?: boolean;
}

export interface NotificationSettings {
  emailNotifications: boolean;
  pushNotifications: boolean;
  smsNotifications?: boolean;
  emailFrequency: 'immediate' | 'hourly' | 'daily' | 'weekly';
  notificationTypes: {
    crossoverAlerts: boolean;
    marketUpdates: boolean;
    accountUpdates: boolean;
    promotional: boolean;
  };
  preferredPairs?: string[];
  minimumSignalStrength?: number;
}

// Session types for NextAuth compatibility
export interface ExtendedUser extends User {
  // Additional properties can be added here
}

export interface Session {
  user: ExtendedUser;
  expires: string;
}

// Common component prop types
export interface BaseComponentProps {
  className?: string;
  children?: React.ReactNode;
}

// API Error types
export interface ApiError {
  code: string;
  message: string;
  status: number;
  details?: any;
}

// Loading states
export interface LoadingState {
  isLoading: boolean;
  error: string | null;
  data: any;
}

// Form validation types
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormState {
  isSubmitting: boolean;
  errors: ValidationError[];
  success: boolean;
}

// Subscription related types
export interface SubscriptionStatus {
  isActive: boolean;
  plan?: string;
  expiresAt?: Date;
  customerId?: string;
}

export interface CheckoutSession {
  sessionId: string;
  url: string;
}
