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
  title: 'Pearls AQI | Atmospheric Obsidian Spatial Intelligence (Sargodha Region)',
  description:
    'Awwwards-winning Spatial Hyper-Minimalist air quality prediction engine for Sargodha, Pakistan powered by an 8-Model AI Zoo and SHAP explainability kernel.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body
        className={`${inter.variable} font-sans bg-[#0A0A0A] text-white min-h-screen antialiased overflow-x-hidden selection:bg-emerald-500 selection:text-black`}
      >
        <LiquidNavigation />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 pb-24 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
