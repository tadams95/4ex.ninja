import "./globals.css";
import { Monda } from "next/font/google";
import { Exo } from "next/font/google";
import Header from "./components/Header";
import Footer from "./components/Footer";

const monda = Monda({
  subsets: ["latin"],
  weight: ["400", "700"], // Available weights for Monda
});

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
        <div className="flex flex-col min-h-screen bg-black">
          <Header />
          <main className="flex-grow">{children}</main>
          <Footer />
        </div>
      </body>
    </html>
  );
}
