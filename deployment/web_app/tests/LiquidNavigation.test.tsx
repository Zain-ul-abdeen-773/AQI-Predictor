import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import LiquidNavigation from '../components/LiquidNavigation';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { style, className } = props as Record<string, unknown>;
      return <div style={style as React.CSSProperties} className={className as string}>{children}</div>;
    },
    span: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <span className={props.className as string}>{children}</span>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

vi.mock('next/link', () => ({
  default: ({ children, href }: { children: React.ReactNode; href: string }) => (
    <a href={href}>{children}</a>
  ),
}));

vi.mock('next/navigation', () => ({
  usePathname: () => '/',
}));

vi.mock('lucide-react', () => ({
  Wind: () => <svg data-testid="wind-icon" />,
}));

describe('LiquidNavigation', () => {
  it('renders without crashing', () => {
    const { container } = render(<LiquidNavigation />);
    expect(container).toBeTruthy();
  });

  it('displays navigation links', () => {
    render(<LiquidNavigation />);
    expect(screen.getByText('Overview')).toBeInTheDocument();
    expect(screen.getByText('Model Comparison')).toBeInTheDocument();
    expect(screen.getByText('Explainability')).toBeInTheDocument();
  });
});
