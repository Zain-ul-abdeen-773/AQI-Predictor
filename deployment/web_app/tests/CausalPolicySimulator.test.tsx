import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import CausalPolicySimulator from '../components/CausalPolicySimulator';

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

describe('CausalPolicySimulator', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('offline'));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<CausalPolicySimulator />);
    expect(container).toBeTruthy();
  });

  it('displays the simulate button', () => {
    render(<CausalPolicySimulator />);
    expect(screen.getByText('Run Intervention Simulation')).toBeInTheDocument();
  });

  it('calls fetch when simulate is clicked', () => {
    render(<CausalPolicySimulator apiBaseUrl="http://test" />);
    fireEvent.click(screen.getByText('Run Intervention Simulation'));
    expect(global.fetch).toHaveBeenCalledWith('http://test/simulate', expect.anything());
  });
});
