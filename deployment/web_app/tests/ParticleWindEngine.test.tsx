import { describe, it, expect, vi } from 'vitest';
import { render } from '@testing-library/react';
import ParticleWindEngine from '../components/ParticleWindEngine';

// Mock canvas context
HTMLCanvasElement.prototype.getContext = vi.fn(() => ({
  clearRect: vi.fn(),
  fillRect: vi.fn(),
  fill: vi.fn(),
  beginPath: vi.fn(),
  moveTo: vi.fn(),
  lineTo: vi.fn(),
  closePath: vi.fn(),
  arc: vi.fn(),
  save: vi.fn(),
  restore: vi.fn(),
  createLinearGradient: vi.fn(() => ({ addColorStop: vi.fn() })),
})) as unknown as typeof HTMLCanvasElement.prototype.getContext;

describe('ParticleWindEngine', () => {
  it('renders a canvas element without crashing', () => {
    const { container } = render(<ParticleWindEngine aqiValue={88} />);
    const canvas = container.querySelector('canvas');
    expect(canvas).toBeTruthy();
    expect(canvas?.getAttribute('aria-hidden')).toBe('true');
  });

  it('renders with hazardous AQI value', () => {
    const { container } = render(<ParticleWindEngine aqiValue={200} />);
    expect(container.querySelector('canvas')).toBeTruthy();
  });
});
