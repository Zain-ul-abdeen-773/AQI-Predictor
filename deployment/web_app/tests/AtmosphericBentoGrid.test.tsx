import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import AtmosphericBentoGrid from '../components/AtmosphericBentoGrid';

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
  useSpring: () => 0,
}));

describe('AtmosphericBentoGrid', () => {
  it('renders without crashing with empty predictions', () => {
    const { container } = render(<AtmosphericBentoGrid hourlyPredictions={[]} />);
    expect(container).toBeTruthy();
  });

  it('displays the 72-hour heading', () => {
    render(<AtmosphericBentoGrid hourlyPredictions={[]} />);
    expect(screen.getByText(/72-Hour Diurnal Progression/)).toBeInTheDocument();
  });
});
