import { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Polyline, CircleMarker, Popup, LayerGroup, useMap } from 'react-leaflet';
import { useAppStore } from '@/store';
import type { Corridor, HabitatPatch } from '@/types';

// ── Corridor colour by priority ───────────────────────────────────────────────
const CORRIDOR_COLOR: Record<string, string> = {
  critical: '#ef4444',
  high:     '#f59e0b',
  medium:   '#22c55e',
  low:      '#3b82f6',
};

// ── WKT LINESTRING → LatLng pairs ─────────────────────────────────────────────
function parseWkt(wkt: string | null): [number, number][] {
  if (!wkt) return [];
  const inner = wkt.replace(/MULTILINESTRING\(\(/, '').replace(/LINESTRING\(/, '').replace(/\)\)$/, '').replace(/\)$/, '');
  return inner.split(',').map(pair => {
    const [lon, lat] = pair.trim().split(' ').map(Number);
    return [lat, lon] as [number, number];
  }).filter(([lat, lon]) => !isNaN(lat) && !isNaN(lon));
}

// ── Auto-fit bounds ───────────────────────────────────────────────────────────
function FitBounds({ corridors }: { corridors: Corridor[] }) {
  const map = useMap();
  useEffect(() => {
    const allPts: [number, number][] = [];
    for (const c of corridors) {
      if (c.geometry_wkt) allPts.push(...parseWkt(c.geometry_wkt));
      if (c.start_lat && c.start_lon) allPts.push([c.start_lat, c.start_lon]);
      if (c.end_lat && c.end_lon)   allPts.push([c.end_lat, c.end_lon]);
    }
    if (allPts.length > 1) {
      map.fitBounds(allPts, { padding: [32, 32] });
    }
  }, [corridors, map]);
  return null;
}

// ── Main Map Component ────────────────────────────────────────────────────────

interface Props {
  corridors?: Corridor[];
  patches?: HabitatPatch[];
  selectedId?: number;
  onCorridorClick?: (id: number) => void;
  height?: string;
  showPatches?: boolean;
  highlightWkt?: string | null;  // proposed road/infrastructure
}

export default function KarnatakaMap({
  corridors = [],
  patches = [],
  selectedId,
  onCorridorClick,
  height = '100%',
  showPatches = true,
  highlightWkt = null,
}: Props) {
  const layers = useAppStore(s => s.layers);

  // Karnataka centre
  const center: [number, number] = [14.0, 75.7];

  return (
    <MapContainer
      center={center}
      zoom={7}
      style={{ height, width: '100%' }}
      preferCanvas
    >
      {/* Dark tile layer */}
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com">CARTO</a>'
        maxZoom={18}
      />

      <FitBounds corridors={corridors} />

      {/* Corridor lines */}
      {layers.corridors && (
        <LayerGroup>
          {corridors.map(c => {
            const pts = parseWkt(c.geometry_wkt);
            if (!pts.length) return null;
            const isSelected = c.id === selectedId;
            return (
              <Polyline
                key={c.id}
                positions={pts}
                pathOptions={{
                  color: CORRIDOR_COLOR[c.priority] ?? '#22c55e',
                  weight: isSelected ? 5 : 3,
                  opacity: isSelected ? 1 : 0.75,
                  dashArray: isSelected ? undefined : '8,4',
                }}
                eventHandlers={{ click: () => onCorridorClick?.(c.id) }}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold text-forest-300 mb-1">{c.name}</div>
                    <div>Score: <span className="text-forest-400 font-medium">{c.connectivity_score}/100</span></div>
                    <div>Priority: <span className="capitalize">{c.priority}</span></div>
                    <div>Length: {c.length_km} km</div>
                  </div>
                </Popup>
              </Polyline>
            );
          })}
        </LayerGroup>
      )}

      {/* Habitat patches */}
      {layers.patches && showPatches && (
        <LayerGroup>
          {patches.map(p => {
            const score = p.suitability_score;
            const color = score >= 0.7 ? '#22c55e' : score >= 0.45 ? '#f59e0b' : '#ef4444';
            return (
              <CircleMarker
                key={p.id}
                center={[p.centroid_lat, p.centroid_lon]}
                radius={Math.max(4, Math.min(10, p.area_ha / 80))}
                pathOptions={{ color, fillColor: color, fillOpacity: 0.6, weight: 1 }}
              >
                <Popup>
                  <div className="text-sm">
                    <div className="font-semibold text-forest-300 mb-1">{p.name}</div>
                    <div>Suitability: <span className="text-forest-400">{(score * 100).toFixed(0)}%</span></div>
                    <div>Area: {p.area_ha} ha</div>
                    <div>Cover: {p.land_cover_class?.replace(/_/g, ' ')}</div>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </LayerGroup>
      )}

      {/* Proposed infrastructure overlay */}
      {highlightWkt && (
        <Polyline
          positions={parseWkt(highlightWkt)}
          pathOptions={{ color: '#ef4444', weight: 4, dashArray: '6,3', opacity: 0.9 }}
        />
      )}
    </MapContainer>
  );
}
