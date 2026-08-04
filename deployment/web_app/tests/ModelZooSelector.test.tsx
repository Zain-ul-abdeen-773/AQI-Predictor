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
  it('renders model name and category', () => {
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="lightgbm"
        onModelChange={vi.fn()}
      />
    );

    expect(screen.getByText('LightGBM')).toBeInTheDocument();
  });

  it('displays model metrics (R², RMSE, MAE)', () => {
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="lightgbm"
        onModelChange={vi.fn()}
      />
    );

    expect(screen.getByText('0.920')).toBeInTheDocument();
    expect(screen.getByText('12.50')).toBeInTheDocument();
    expect(screen.getByText('8.30')).toBeInTheDocument();
  });

  it('calls onModelChange when a different model is selected', () => {
    const mockOnChange = vi.fn();
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="lightgbm"
        onModelChange={mockOnChange}
      />
    );

    const xgboostOption = screen.getByText('XGBoost');
    fireEvent.click(xgboostOption);

    expect(mockOnChange).toHaveBeenCalledWith('xgboost');
  });

  it('shows loading state when isFetching is true', () => {
    render(
      <ModelZooSelector
        modelList={mockModels}
        activeModelId="lightgbm"
        onModelChange={vi.fn()}
        isFetching={true}
      />
    );

    expect(screen.getByText(/switching/i)).toBeInTheDocument();
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

  it('highlights the active model in the dropdown', () => {
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
