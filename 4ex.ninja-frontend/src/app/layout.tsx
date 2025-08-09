import { Metadata } from 'next';
import { Exo } from 'next/font/google';
import { ChunkLoadErrorBoundary, GlobalErrorBoundary } from '../components/error';
import HydrationErrorBoundary from '../components/error/HydrationErrorBoundary';
import Footer from './components/Footer';
import Header from './components/Header';
import Providers from './components/Providers';
import './globals.css';

const exo = Exo({
  subsets: ['latin'],
  weight: ['400', '700'], // Available weights for Exo
  display: 'swap', // Optimize font loading with font-display: swap
  preload: true, // Preload the font
  fallback: ['system-ui', 'arial'], // Fallback fonts
});

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
    <html lang="en">
      <head>
        {/* Resource hints for critical assets */}
        <link rel="dns-prefetch" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="" />

        {/* Preload critical assets */}
        <link rel="preload" href="/next.svg" as="image" type="image/svg+xml" />
        <link rel="preload" href="/vercel.svg" as="image" type="image/svg+xml" />

        {/* Optimize favicon loading */}
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/favicon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className={exo.className}>
        <GlobalErrorBoundary>
          <ChunkLoadErrorBoundary>
            <HydrationErrorBoundary>
              <Providers>
                <div className="flex flex-col min-h-screen bg-black">
                  <Header />
                  <main className="flex-grow">{children}</main>
                  <Footer />
                </div>
              </Providers>
            </HydrationErrorBoundary>
          </ChunkLoadErrorBoundary>
        </GlobalErrorBoundary>
      </body>
    </html>
  );
}
