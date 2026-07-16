import './globals.css';
import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import LiquidNavigation from '../components/LiquidNavigation';

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'Pearls AQI — Luminous Neumorphic Air Quality Intelligence (Sargodha)',
  description:
    'Awwwards-winning Luminous Neumorphic (Soft UI) air quality prediction platform for the Sargodha region, powered by an 8-Model Machine Learning Zoo and volumetric atmospheric simulation.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} font-sans bg-[#F2F4F8] text-[#2D3748] min-h-screen antialiased overflow-x-hidden selection:bg-[#0284C7] selection:text-white`}
      >
        <LiquidNavigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 pb-20 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
