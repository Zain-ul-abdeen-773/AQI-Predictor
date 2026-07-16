import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import LiquidNavigation from '../components/LiquidNavigation';

const inter = Inter({
  subsets: ['latin'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Pearls AQI — Air Quality Prediction for Sargodha',
  description:
    'Machine learning-powered air quality index prediction for the Sargodha region, Pakistan. Featuring 8 regression models and SHAP explainability.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans bg-[#111114] text-white min-h-screen antialiased overflow-x-hidden selection:bg-teal-500 selection:text-black`}
      >
        <LiquidNavigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 pb-20 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
