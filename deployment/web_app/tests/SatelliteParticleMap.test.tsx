import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import SatelliteParticleMap from '../components/SatelliteParticleMap';

describe('SatelliteParticleMap', () => {
  beforeEach(() => {
    vi.spyOn(global, 'fetch').mockRejectedValue(new Error('offline'));
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders without crashing', () => {
    const { container } = render(<SatelliteParticleMap />);
    expect(container).toBeTruthy();
  });

  it('displays the heading and falls back to generated grid', async () => {
    render(<SatelliteParticleMap />);
    expect(screen.getByText('Sargodha Atmospheric Particle Vector Grid')).toBeInTheDocument();
    await waitFor(() => {
      const nodes = screen.getAllByText(/°N/);
      expect(nodes.length).toBeGreaterThan(0);
    });
  });
});
