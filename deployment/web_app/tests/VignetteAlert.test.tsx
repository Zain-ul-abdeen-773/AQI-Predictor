import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import VignetteAlert from '../components/VignetteAlert';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { style, className } = props as Record<string, unknown>;
      return <div style={style as React.CSSProperties} className={className as string}>{children}</div>;
    },
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

vi.mock('lucide-react', () => ({
  AlertTriangle: () => <svg data-testid="alert-icon" />,
}));

describe('VignetteAlert', () => {
  it('renders nothing when AQI is below threshold', () => {
    const { container } = render(<VignetteAlert currentAqi={50} />);
    expect(container.querySelector('.fixed')).toBeNull();
  });

  it('renders alert when AQI exceeds 150', () => {
    render(<VignetteAlert currentAqi={180} />);
    expect(screen.getByText(/REGIONAL ADVISORY/)).toBeInTheDocument();
    expect(screen.getByText('AQI 180')).toBeInTheDocument();
  });

  it('renders alert when isTriggered is true regardless of AQI', () => {
    render(<VignetteAlert currentAqi={30} isTriggered={true} />);
    expect(screen.getByText(/REGIONAL ADVISORY/)).toBeInTheDocument();
  });
});
