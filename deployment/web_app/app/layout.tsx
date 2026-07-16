import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';
import Navigation from '../components/Navigation';

const inter = Inter({
  subsets: ['latin'],
  weight: ['100', '200', '300', '400', '500', '600', '700', '800'],
  variable: '--font-inter',
});

export const metadata: Metadata = {
  title: 'Pearls AQI | Sargodha Atmospheric Obsidian Intelligence',
  description:
    'Spatial Hyper-Minimalist Awwwards-winning Air Quality Index prediction engine for Sargodha, Pakistan powered by 8-Model Zoo and SHAP explainability.',
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
        <Navigation />
        <main className="max-w-7xl mx-auto px-4 md:px-6 pb-20 relative z-10">
          {children}
        </main>
      </body>
    </html>
  );
}
