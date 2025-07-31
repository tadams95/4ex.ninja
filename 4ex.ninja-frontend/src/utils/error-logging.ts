/**
 * Client-side error logging service for 4ex.ninja
 * Handles error collection, batching, and reporting for monitoring
 */

export interface LogLevel {
  ERROR: 'error';
  WARN: 'warn';
  INFO: 'info';
  DEBUG: 'debug';
}

export interface ErrorLog {
  id: string;
  timestamp: string;
  level: keyof LogLevel;
  message: string;
  error?: {
    name: string;
    message: string;
    stack?: string;
  };
  context?: {
    userId?: string;
    sessionId: string;
    userAgent: string;
    url: string;
    viewport?: {
      width: number;
      height: number;
    };
    component?: string;
    action?: string;
  };
  metadata?: Record<string, unknown>;
}

export interface ErrorLoggerConfig {
  maxBatchSize: number;
  flushInterval: number; // ms
  maxRetries: number;
  enableConsoleLogging: boolean;
  enableLocalStorage: boolean;
  endpoint?: string;
}

export class ErrorLoggingService {
  private static instance: ErrorLoggingService;
  private config: ErrorLoggerConfig;
  private logQueue: ErrorLog[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private sessionId: string;

  private constructor(config?: Partial<ErrorLoggerConfig>) {
    this.config = {
      maxBatchSize: 10,
      flushInterval: 30000, // 30 seconds
      maxRetries: 3,
      enableConsoleLogging: process.env.NODE_ENV === 'development',
      enableLocalStorage: true,
      ...config,
    };

    this.sessionId = this.generateSessionId();
    this.setupGlobalErrorHandlers();
    this.scheduleFlush();
  }

  static getInstance(config?: Partial<ErrorLoggerConfig>): ErrorLoggingService {
    if (!ErrorLoggingService.instance) {
      ErrorLoggingService.instance = new ErrorLoggingService(config);
    }
    return ErrorLoggingService.instance;
  }

  /**
   * Log an error with context
   */
  logError(
    error: Error | string,
    context?: Partial<ErrorLog['context']>,
    metadata?: Record<string, unknown>
  ): void {
    const logEntry = this.createLogEntry('ERROR', error, context, metadata);
    this.addToQueue(logEntry);
  }

  /**
   * Log a warning
   */
  logWarning(
    message: string,
    context?: Partial<ErrorLog['context']>,
    metadata?: Record<string, unknown>
  ): void {
    const logEntry = this.createLogEntry('WARN', message, context, metadata);
    this.addToQueue(logEntry);
  }

  /**
   * Log info message
   */
  logInfo(
    message: string,
    context?: Partial<ErrorLog['context']>,
    metadata?: Record<string, unknown>
  ): void {
    const logEntry = this.createLogEntry('INFO', message, context, metadata);
    this.addToQueue(logEntry);
  }

  /**
   * Log debug message
   */
  logDebug(
    message: string,
    context?: Partial<ErrorLog['context']>,
    metadata?: Record<string, unknown>
  ): void {
    if (process.env.NODE_ENV === 'development') {
      const logEntry = this.createLogEntry('DEBUG', message, context, metadata);
      this.addToQueue(logEntry);
    }
  }

  /**
   * Log API error with specific context
   */
  logApiError(
    error: Error | string,
    endpoint: string,
    method: string,
    statusCode?: number,
    requestData?: unknown
  ): void {
    this.logError(
      error,
      {
        action: `API_${method.toUpperCase()}`,
        component: 'ApiClient',
      },
      {
        endpoint,
        method,
        statusCode,
        requestData: this.sanitizeRequestData(requestData),
      }
    );
  }

  /**
   * Log component error with React context
   */
  logComponentError(
    error: Error | string,
    componentName: string,
    props?: Record<string, unknown>,
    state?: Record<string, unknown>
  ): void {
    this.logError(
      error,
      {
        component: componentName,
        action: 'COMPONENT_ERROR',
      },
      {
        props: this.sanitizeData(props),
        state: this.sanitizeData(state),
      }
    );
  }

  /**
   * Force flush all queued logs
   */
  async flush(): Promise<void> {
    if (this.logQueue.length === 0) return;

    const logsToSend = [...this.logQueue];
    this.logQueue = [];

    await this.sendLogs(logsToSend);
  }

  /**
   * Get recent logs for debugging
   */
  getRecentLogs(count: number = 50): ErrorLog[] {
    try {
      const stored = localStorage.getItem('errorLogs');
      if (!stored) return [];

      const logs: ErrorLog[] = JSON.parse(stored);
      return logs.slice(-count);
    } catch {
      return [];
    }
  }

  /**
   * Clear stored logs
   */
  clearLogs(): void {
    try {
      localStorage.removeItem('errorLogs');
      this.logQueue = [];
    } catch {
      // Ignore localStorage errors
    }
  }

  /**
   * Create standardized log entry
   */
  private createLogEntry(
    level: keyof LogLevel,
    errorOrMessage: Error | string,
    context?: Partial<ErrorLog['context']>,
    metadata?: Record<string, unknown>
  ): ErrorLog {
    const timestamp = new Date().toISOString();
    const id = `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    let message: string;
    let error: ErrorLog['error'] | undefined;

    if (errorOrMessage instanceof Error) {
      message = errorOrMessage.message;
      error = {
        name: errorOrMessage.name,
        message: errorOrMessage.message,
        stack: errorOrMessage.stack,
      };
    } else {
      message = errorOrMessage;
    }

    return {
      id,
      timestamp,
      level,
      message,
      error,
      context: {
        sessionId: this.sessionId,
        userAgent: navigator.userAgent,
        url: window.location.href,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight,
        },
        userId: this.getCurrentUserId(),
        ...context,
      },
      metadata: metadata ? (this.sanitizeData(metadata) as Record<string, unknown>) : undefined,
    };
  }

  /**
   * Add log to queue and trigger flush if needed
   */
  private addToQueue(logEntry: ErrorLog): void {
    this.logQueue.push(logEntry);

    // Console logging in development
    if (this.config.enableConsoleLogging) {
      this.logToConsole(logEntry);
    }

    // Store in localStorage for persistence
    if (this.config.enableLocalStorage) {
      this.storeInLocalStorage(logEntry);
    }

    // Flush if queue is full
    if (this.logQueue.length >= this.config.maxBatchSize) {
      this.flush();
    }
  }

  /**
   * Send logs to monitoring service
   */
  private async sendLogs(logs: ErrorLog[]): Promise<void> {
    if (!this.config.endpoint) {
      // If no endpoint configured, just store locally
      return;
    }

    try {
      const response = await fetch(this.config.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs }),
      });

      if (!response.ok) {
        throw new Error(`Failed to send logs: ${response.status}`);
      }
    } catch (error) {
      // If sending fails, put logs back in queue for retry
      this.logQueue.unshift(...logs);

      // Avoid infinite recursion by not logging this error
      if (this.config.enableConsoleLogging) {
        console.warn('Failed to send error logs:', error);
      }
    }
  }

  /**
   * Schedule periodic flush
   */
  private scheduleFlush(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  /**
   * Setup global error handlers
   */
  private setupGlobalErrorHandlers(): void {
    // Unhandled errors
    window.addEventListener('error', event => {
      this.logError(
        event.error || event.message,
        {
          component: 'GlobalErrorHandler',
          action: 'UNHANDLED_ERROR',
        },
        {
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        }
      );
    });

    // Unhandled promise rejections
    window.addEventListener('unhandledrejection', event => {
      this.logError(event.reason, {
        component: 'GlobalErrorHandler',
        action: 'UNHANDLED_REJECTION',
      });
    });

    // Cleanup on page unload
    window.addEventListener('beforeunload', () => {
      this.flush();
    });
  }

  /**
   * Log to browser console
   */
  private logToConsole(logEntry: ErrorLog): void {
    const { level, message, error, context, metadata } = logEntry;

    const logData = {
      message,
      context,
      metadata,
      error,
    };

    switch (level) {
      case 'ERROR':
        console.error(`[${logEntry.timestamp}] ERROR:`, logData);
        break;
      case 'WARN':
        console.warn(`[${logEntry.timestamp}] WARN:`, logData);
        break;
      case 'INFO':
        console.info(`[${logEntry.timestamp}] INFO:`, logData);
        break;
      case 'DEBUG':
        console.debug(`[${logEntry.timestamp}] DEBUG:`, logData);
        break;
    }
  }

  /**
   * Store log in localStorage
   */
  private storeInLocalStorage(logEntry: ErrorLog): void {
    try {
      const existingLogs = JSON.parse(localStorage.getItem('errorLogs') || '[]');
      existingLogs.push(logEntry);

      // Keep only recent logs to prevent storage bloat
      if (existingLogs.length > 100) {
        existingLogs.splice(0, existingLogs.length - 100);
      }

      localStorage.setItem('errorLogs', JSON.stringify(existingLogs));
    } catch {
      // Ignore localStorage errors
    }
  }

  /**
   * Sanitize data to remove sensitive information
   */
  private sanitizeData(data: unknown): unknown {
    if (!data || typeof data !== 'object') return data;

    const sensitiveKeys = ['password', 'token', 'auth', 'secret', 'key', 'credential'];

    if (Array.isArray(data)) {
      return data.map(item => this.sanitizeData(item));
    }

    const sanitized: Record<string, unknown> = {};

    for (const [key, value] of Object.entries(data as Record<string, unknown>)) {
      const isLowercaseKey = key.toLowerCase();
      const isSensitive = sensitiveKeys.some(sensitive => isLowercaseKey.includes(sensitive));

      if (isSensitive) {
        sanitized[key] = '[REDACTED]';
      } else if (typeof value === 'object' && value !== null) {
        sanitized[key] = this.sanitizeData(value);
      } else {
        sanitized[key] = value;
      }
    }

    return sanitized;
  }

  /**
   * Sanitize request data specifically
   */
  private sanitizeRequestData(data: unknown): unknown {
    return this.sanitizeData(data);
  }

  /**
   * Generate session ID
   */
  private generateSessionId(): string {
    const existing = sessionStorage.getItem('errorLoggingSessionId');
    if (existing) return existing;

    const sessionId = `sess_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    sessionStorage.setItem('errorLoggingSessionId', sessionId);
    return sessionId;
  }

  /**
   * Get current user ID (placeholder for auth integration)
   */
  private getCurrentUserId(): string | undefined {
    // This would integrate with your auth system
    // For now, return undefined
    return undefined;
  }
}

/**
 * Singleton instance for easy access
 */
export const errorLogger = ErrorLoggingService.getInstance();

/**
 * React hook for error logging
 */
export function useErrorLogger() {
  return {
    logError: errorLogger.logError.bind(errorLogger),
    logWarning: errorLogger.logWarning.bind(errorLogger),
    logInfo: errorLogger.logInfo.bind(errorLogger),
    logDebug: errorLogger.logDebug.bind(errorLogger),
    logApiError: errorLogger.logApiError.bind(errorLogger),
    logComponentError: errorLogger.logComponentError.bind(errorLogger),
  };
}
