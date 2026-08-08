import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import ActualVsPredictedGraph from '../components/ActualVsPredictedGraph';

vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { style, className, onClick } = props as Record<string, unknown>;
      return <div style={style as React.CSSProperties} className={className as string} onClick={onClick as React.MouseEventHandler}>{children}</div>;
    },
    span: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <span className={props.className as string}>{children}</span>
    ),
    section: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <section className={props.className as string}>{children}</section>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

describe('ActualVsPredictedGraph', () => {
  it('renders without crashing', () => {
    const { container } = render(<ActualVsPredictedGraph />);
    expect(container).toBeTruthy();
  });

  it('displays the section heading', () => {
    render(<ActualVsPredictedGraph />);
    expect(screen.getByText('Out-of-Sample Trajectory Audit')).toBeInTheDocument();
  });
});
