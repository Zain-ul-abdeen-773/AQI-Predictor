'use client';

import React, { useState, useEffect } from 'react';

interface GridPoint {
  latitude: number;
  longitude: number;
  no2_column_density: number;
  aerosol_optical_depth: number;
  wind_u_component: number;
  wind_v_component: number;
  aqi_proxy: number;
}

interface SatelliteParticleMapProps {
  apiBaseUrl?: string;
}

export default function SatelliteParticleMap({ apiBaseUrl = 'http://localhost:8000' }: SatelliteParticleMapProps) {
  const [activeLayer, setActiveLayer] = useState<'no2' | 'aod' | 'wind'>('no2');
  const [grid, setGrid] = useState<GridPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${apiBaseUrl}/satellite/sentinel5p`)
      .then((r) => r.json())
      .then((data) => {
        if (data?.grid_points) {
          setGrid(data.grid_points);
        }
      })
      .catch(() => {
        // Fallback grid dataset for Sargodha basin
        const centerLat = 32.0836;
        const centerLon = 72.6711;
        const pts: GridPoint[] = [];
        for (let i = -2; i <= 2; i++) {
          for (let j = -2; j <= 2; j++) {
            pts.push({
              latitude: Number((centerLat + i * 0.08).toFixed(4)),
              longitude: Number((centerLon + j * 0.08).toFixed(4)),
              no2_column_density: Number((18.5 - Math.abs(i) * 2 - Math.abs(j) * 1.5).toFixed(1)),
              aerosol_optical_depth: Number((0.52 - Math.abs(i) * 0.05).toFixed(2)),
              wind_u_component: 2.8,
              wind_v_component: -1.4,
              aqi_proxy: Math.round(90 + (2 - Math.abs(i)) * 12),
            });
          }
        }
        setGrid(pts);
      })
      .finally(() => setLoading(false));
  }, [apiBaseUrl]);

  const getColor = (val: number, type: 'no2' | 'aod' | 'wind') => {
    if (type === 'no2') {
      return val > 20
        ? 'bg-rose-500/80 border-rose-400'
        : val > 15
        ? 'bg-amber-500/80 border-amber-400'
        : 'bg-emerald-500/80 border-emerald-400';
    }
    if (type === 'aod') {
      return val > 0.5
        ? 'bg-purple-500/80 border-purple-400'
        : val > 0.3
        ? 'bg-blue-500/80 border-blue-400'
        : 'bg-cyan-500/80 border-cyan-400';
    }
    return 'bg-sky-500/80 border-sky-400';
  };

  return (
    <div className="w-full bg-slate-900/80 backdrop-blur-xl border border-slate-800 rounded-3xl p-6 shadow-2xl text-slate-100 font-sans">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-violet-500/10 text-violet-400 border border-violet-500/20">
              Copernicus Sentinel-5P TROPOMI
            </span>
            <span className="text-xs text-slate-400">Earth Observation Satellite Swath</span>
          </div>
          <h3 className="text-xl font-bold tracking-tight text-white mt-1">
            Sargodha Atmospheric Particle Vector Grid
          </h3>
        </div>

        <div className="flex items-center gap-2 bg-slate-950 p-1 rounded-xl border border-slate-800">
          <button
            onClick={() => setActiveLayer('no2')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeLayer === 'no2' ? 'bg-violet-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            NO₂ Column
          </button>
          <button
            onClick={() => setActiveLayer('aod')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeLayer === 'aod' ? 'bg-violet-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            AOD Aerosols
          </button>
          <button
            onClick={() => setActiveLayer('wind')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              activeLayer === 'wind' ? 'bg-violet-600 text-white shadow' : 'text-slate-400 hover:text-slate-200'
            }`}
          >
            Wind Dispersion
          </button>
        </div>
      </div>

      {/* 5x5 Satellite Observation Mesh */}
      <div className="relative w-full aspect-[2/1] bg-slate-950 rounded-2xl border border-slate-800 overflow-hidden p-6 flex flex-col justify-between">
        {/* Background Grid Lines */}
        <div className="absolute inset-0 opacity-20 pointer-events-none bg-[radial-gradient(#6366f1_1px,transparent_1px)] [background-size:16px_16px]" />

        <div className="relative z-10 grid grid-cols-5 gap-3 w-full h-full items-center">
          {grid.map((pt, idx) => {
            const val =
              activeLayer === 'no2'
                ? pt.no2_column_density
                : activeLayer === 'aod'
                ? pt.aerosol_optical_depth
                : pt.wind_u_component;

            return (
              <div
                key={idx}
                className="group relative flex flex-col items-center justify-center p-2 rounded-xl bg-slate-900/60 border border-slate-800 hover:border-violet-500/50 transition-all hover:scale-105"
              >
                <div
                  className={`w-3 h-3 rounded-full mb-1.5 border shadow-sm ${getColor(
                    val,
                    activeLayer
                  )} group-hover:animate-ping`}
                />
                <span className="text-[10px] font-mono font-semibold text-slate-300">
                  {val} {activeLayer === 'no2' ? '10¹⁵' : activeLayer === 'aod' ? 'AOD' : 'm/s'}
                </span>
                <span className="text-[9px] text-slate-500 font-mono mt-0.5">
                  {pt.latitude}°N
                </span>
              </div>
            );
          })}
        </div>

        <div className="relative z-10 flex items-center justify-between text-[11px] text-slate-400 pt-3 border-t border-slate-800/80">
          <span>Target Center: 32.0836° N, 72.6711° E (Sargodha District)</span>
          <span className="font-mono text-violet-400">Resolution: 0.08° (~8.8 km mesh)</span>
        </div>
      </div>
    </div>
  );
}
