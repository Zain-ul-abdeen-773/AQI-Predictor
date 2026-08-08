import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render } from '@testing-library/react';

// Mock framer-motion
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { style, className, onClick } = props as Record<string, unknown>;
      return (
        <div style={style as React.CSSProperties} className={className as string} onClick={onClick as React.MouseEventHandler}>
          {children}
        </div>
      );
    },
    span: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <span className={props.className as string}>{children}</span>
    ),
    p: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <p className={props.className as string}>{children}</p>
    ),
    button: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { className, onClick, disabled } = props as Record<string, unknown>;
      return (
        <button className={className as string} onClick={onClick as React.MouseEventHandler} disabled={disabled as boolean}>
          {children}
        </button>
      );
    },
    a: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <a className={props.className as string} href={props.href as string}>{children}</a>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
  useSpring: () => ({ set: vi.fn(), on: vi.fn(() => vi.fn()) }),
}));

// Mock all heavy child components to keep the test focused on page rendering
vi.mock('../components/ParticleWindEngine', () => ({
  default: () => <div data-testid="particle-wind-engine" />,
}));
vi.mock('../components/ModelZooSelector', () => ({
  default: () => <div data-testid="model-zoo-selector" />,
  ModelZooEntry: undefined,
}));
vi.mock('../components/AtmosphericBentoGrid', () => ({
  default: () => <div data-testid="atmospheric-bento-grid" />,
}));
vi.mock('../components/VignetteAlert', () => ({
  default: () => <div data-testid="vignette-alert" />,
}));
vi.mock('../components/ActualVsPredictedGraph', () => ({
  default: () => <div data-testid="actual-vs-predicted-graph" />,
}));
vi.mock('../components/CausalPolicySimulator', () => ({
  default: () => <div data-testid="causal-policy-simulator" />,
}));
vi.mock('../components/EdgeInferenceEngine', () => ({
  default: () => <div data-testid="edge-inference-engine" />,
}));
vi.mock('../components/SatelliteParticleMap', () => ({
  default: () => <div data-testid="satellite-particle-map" />,
}));
vi.mock('../components/ShadowCanaryMonitor', () => ({
  default: () => <div data-testid="shadow-canary-monitor" />,
}));

import EditorialHomePage from '../app/page';

describe('EditorialHomePage (page.tsx)', () => {
  beforeEach(() => {
    // Mock global fetch to return empty model list
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve({ models: [] }),
      })
    ) as unknown as typeof fetch;
  });

  it('renders without crashing', () => {
    const { container } = render(<EditorialHomePage />);
    expect(container).toBeTruthy();
  });

  it('renders key child components', () => {
    const { getByTestId } = render(<EditorialHomePage />);
    expect(getByTestId('particle-wind-engine')).toBeInTheDocument();
    expect(getByTestId('model-zoo-selector')).toBeInTheDocument();
    expect(getByTestId('edge-inference-engine')).toBeInTheDocument();
  });
});
