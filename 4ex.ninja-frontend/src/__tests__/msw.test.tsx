/**
 * @jest-environment jsdom
 */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import React from 'react';

// Simple component that makes an API call
function TestComponent() {
  const [data, setData] = React.useState(null);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    setLoading(true);
    fetch('/api/subscription-status')
      .then(res => res.json())
      .then(data => {
        setData(data);
        setLoading(false);
      });
  }, []);

  if (loading) return <div data-testid="loading">Loading...</div>;
  if (data) return <div data-testid="data">{JSON.stringify(data)}</div>;
  return <div data-testid="no-data">No data</div>;
}

describe('MSW Integration', () => {
  it('should mock API calls successfully', async () => {
    const queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    });

    render(
      <QueryClientProvider client={queryClient}>
        <TestComponent />
      </QueryClientProvider>
    );

    // Should show loading initially
    expect(screen.getByTestId('loading')).toBeInTheDocument();

    // Should show mocked data after API call
    await waitFor(() => {
      expect(screen.getByTestId('data')).toBeInTheDocument();
    });

    const dataElement = screen.getByTestId('data');
    expect(dataElement.textContent).toContain('isSubscribed');
    expect(dataElement.textContent).toContain('subscriptionStatus');
  });
});
