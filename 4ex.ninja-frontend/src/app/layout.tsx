import '@coinbase/onchainkit/styles.css';
import { Metadata } from 'next';
import { ChunkLoadErrorBoundary, GlobalErrorBoundary } from '../components/error';
import HydrationErrorBoundary from '../components/error/HydrationErrorBoundary';
import PerformanceDashboard from '../components/PerformanceDashboard';
import Footer from './components/Footer';
import Header from './components/Header';
import Providers from './components/Providers';
import './globals.css';

export const metadata: Metadata = {
  title: '4ex.ninja',
  description: 'Get premium forex signals with our subscription service',
  // Resource hints for performance
  other: {
    'dns-prefetch': 'https://fonts.googleapis.com',
    preconnect: 'https://fonts.gstatic.com',
  },
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en" className="dark">
      <head>
        {/* Resource hints for critical assets */}
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />

        {/* Google Fonts - Exo */}
        <link
          href="https://fonts.googleapis.com/css2?family=Exo:ital,wght@0,100..900;1,100..900&display=swap"
          rel="stylesheet"
        />

        {/* Preconnect to OnchainKit and wallet services */}
        <link rel="preconnect" href="https://api.coinbase.com" />
        <link rel="preconnect" href="https://mainnet.base.org" />

        {/* Preload critical assets */}
        <link rel="preload" href="/next.svg" as="image" type="image/svg+xml" />
        <link rel="preload" href="/vercel.svg" as="image" type="image/svg+xml" />

        {/* Preload critical JavaScript modules */}
        <link rel="modulepreload" href="/_next/static/chunks/framework.js" />
        <link rel="modulepreload" href="/_next/static/chunks/main.js" />

        {/* Optimize favicon loading */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />

        {/* Register service worker for offline functionality */}
        <script
          dangerouslySetInnerHTML={{
            __html: `
              if ('serviceWorker' in navigator) {
                window.addEventListener('load', function() {
                  navigator.serviceWorker.register('/sw.js').then(function(registration) {
                    console.log('SW registered: ', registration);
                  }).catch(function(registrationError) {
                    console.log('SW registration failed: ', registrationError);
                  });
                });
              }
            `,
          }}
        />
      </head>
      <body className="font-exo">
        {/* Progressive enhancement noscript fallback */}
        <noscript>
          <div
            style={{
              backgroundColor: '#1f2937',
              color: '#f9fafb',
              padding: '16px',
              textAlign: 'center',
              borderBottom: '2px solid #374151',
            }}
          >
            <p>
              <strong>JavaScript Required</strong>
            </p>
            <p style={{ fontSize: '14px', marginTop: '8px' }}>
              4ex.ninja requires JavaScript for the best experience. Please enable JavaScript in
              your browser.
            </p>
          </div>
        </noscript>

        <GlobalErrorBoundary>
          <ChunkLoadErrorBoundary>
            <HydrationErrorBoundary>
              <Providers>
                <div className="flex flex-col min-h-screen bg-black">
                  <Header />
                  <main className="flex-grow">{children}</main>
                  <Footer />
                </div>
                {/* Performance Dashboard - only show in development or when explicitly enabled */}
                <PerformanceDashboard
                  isVisible={
                    process.env.NODE_ENV === 'development' ||
                    process.env.NEXT_PUBLIC_SHOW_PERFORMANCE === 'true'
                  }
                  position="bottom-right"
                />
              </Providers>
            </HydrationErrorBoundary>
          </ChunkLoadErrorBoundary>
        </GlobalErrorBoundary>
      </body>
    </html>
  );
}
