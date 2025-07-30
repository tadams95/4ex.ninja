import { Metadata } from 'next';
import { Exo } from 'next/font/google';
import Footer from './components/Footer';
import Header from './components/Header';
import Providers from './components/Providers';
import './globals.css';

const exo = Exo({
  subsets: ['latin'],
  weight: ['400', '700'], // Available weights for Exo
});

export const metadata: Metadata = {
  title: '4ex.ninja',
  description: 'Get premium forex signals with our subscription service',
};

interface RootLayoutProps {
  children: React.ReactNode;
}

export default function RootLayout({ children }: RootLayoutProps) {
  return (
    <html lang="en">
      <body className={exo.className}>
        <Providers>
          <div className="flex flex-col min-h-screen bg-black">
            <Header />
            <main className="flex-grow">{children}</main>
            <Footer />
          </div>
        </Providers>
      </body>
    </html>
  );
}
