import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import EdgeInferenceEngine from '../components/EdgeInferenceEngine';

describe('EdgeInferenceEngine', () => {
  it('renders without crashing', () => {
    const { container } = render(<EdgeInferenceEngine />);
    expect(container).toBeTruthy();
  });

  it('shows enable button initially', () => {
    render(<EdgeInferenceEngine />);
    expect(screen.getByText('Enable Edge Wasm')).toBeInTheDocument();
  });

  it('toggles edge mode on click and calls onEdgePrediction', () => {
    const mockCallback = vi.fn();
    render(<EdgeInferenceEngine onEdgePrediction={mockCallback} />);
    fireEvent.click(screen.getByText('Enable Edge Wasm'));
    expect(screen.getByText('Edge Mode Active')).toBeInTheDocument();
    expect(mockCallback).toHaveBeenCalled();
  });
});
