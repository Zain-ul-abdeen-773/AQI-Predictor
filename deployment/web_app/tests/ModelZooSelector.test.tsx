import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ModelZooSelector, { ModelZooEntry } from '../components/ModelZooSelector';

// Mock framer-motion to avoid animation issues in tests
vi.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => {
      const { style, className, onMouseMove, onMouseLeave, onClick } = props as Record<string, unknown>;
      return (
        <div
          style={style as React.CSSProperties}
          className={className as string}
          onMouseMove={onMouseMove as React.MouseEventHandler}
          onMouseLeave={onMouseLeave as React.MouseEventHandler}
          onClick={onClick as React.MouseEventHandler}
        >
          {children}
        </div>
      );
    },
    span: ({ children, ...props }: React.PropsWithChildren<Record<string, unknown>>) => (
      <span className={props.className as string}>{children}</span>
    ),
  },
  AnimatePresence: ({ children }: React.PropsWithChildren) => <>{children}</>,
}));

const mockModels: ModelZooEntry[] = [
  {
    id: 'lightgbm',
    name: 'LightGBM',
    category: 'Gradient Boosting',
    r2: 0.92,
    rmse: 12.5,
    mae: 8.3,
    is_default: true,
    description: 'Gradient boosting with Optuna HPO',
  },
  {
    id: 'xgboost',
    name: 'XGBoost',
    category: 'Gradient Boosting',
    r2: 0.89,
    rmse: 14.2,
    mae: 9.7,
    is_default: false,
    description: 'Extreme gradient boosting',
  },
  {
    id: 'bilstm',
    name: 'Bi-LSTM + Attention',
    category: 'Deep Learning',
    r2: 0.88,
    rmse: 15.1,
    mae: 10.2,
    is_default: false,
    description: 'Bidirectional LSTM with multi-head attention',
  },
];

describe('ModelZooSelector', () => {
  it('renders without crashing', () => {
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="lightgbm"
        onModelChange={vi.fn()}
      />
    );

    expect(screen.getByText('LightGBM')).toBeInTheDocument();
  });

  it('handles empty model list gracefully', () => {
    const { container } = render(
      <ModelZooSelector
        modelList={[]}
        activeModelId=""
        onModelChange={vi.fn()}
      />
    );

    expect(container).toBeTruthy();
  });

  it('renders the active model', () => {
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="xgboost"
        onModelChange={vi.fn()}
      />
    );

    expect(screen.getByText('XGBoost')).toBeInTheDocument();
  });
});
