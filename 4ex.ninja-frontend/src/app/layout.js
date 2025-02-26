import "./globals.css";

import { Exo } from "next/font/google";
import Header from "./components/Header";
import Footer from "./components/Footer";
import Providers from "./components/Providers";

const exo = Exo({
  subsets: ["latin"],
  weight: ["400", "700"], // Available weights for Exo
});

export const metadata = {
  title: "4ex.ninja",
  description: "Get premium forex signals with our subscription service",
};

export default function RootLayout({ children }) {
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
