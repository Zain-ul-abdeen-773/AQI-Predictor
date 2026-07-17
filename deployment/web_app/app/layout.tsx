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
  title: 'Pearls AQI — Atmospheric Intelligence Engine (Sargodha)',
  description:
    'High-end editorial air quality prediction platform for the Sargodha region, powered by an 8-Model Machine Learning Zoo with telemetric verification.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body
        className={`${inter.variable} font-sans bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-[#0A0F1A] to-black text-slate-200 min-h-screen antialiased overflow-x-hidden selection:bg-[#0066FF]/30 selection:text-[#0066FF]`}
      >
        <LiquidNavigation />
        <main className="w-full mx-auto px-4 sm:px-6 lg:px-12 pb-24 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
