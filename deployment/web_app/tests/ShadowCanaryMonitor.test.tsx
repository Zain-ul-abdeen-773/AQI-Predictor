import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import ShadowCanaryMonitor from '../components/ShadowCanaryMonitor';

describe('ShadowCanaryMonitor', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('offline'));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<ShadowCanaryMonitor />);
    expect(container).toBeTruthy();
  });

  it('displays the champion model and challenger table', () => {
    render(<ShadowCanaryMonitor />);
    expect(screen.getByText('Champion vs. Challenger Shadow Router')).toBeInTheDocument();
    expect(screen.getByText('BILSTM_ATTENTION')).toBeInTheDocument();
    expect(screen.getByText('lightgbm')).toBeInTheDocument();
  });
});
