"use client";

import { useMemo } from "react";
import { ScatterplotLayer, PolygonLayer } from "@deck.gl/layers";

interface WeatherStation {
  position: [number, number];
  temp: number;
  humidity: number;
  windSpeed: number;
  windDir?: number;
}

const stations: WeatherStation[] = [
  { position: [78.5, 17.5], temp: 32, humidity: 68, windSpeed: 12, windDir: 180 },
  { position: [79.0, 18.0], temp: 30, humidity: 72, windSpeed: 8, windDir: 200 },
  { position: [78.0, 17.0], temp: 34, humidity: 55, windSpeed: 15, windDir: 160 },
  { position: [79.5, 17.5], temp: 31, humidity: 65, windSpeed: 10, windDir: 190 },
  { position: [78.0, 18.0], temp: 28, humidity: 78, windSpeed: 6, windDir: 220 },
  { position: [79.2, 16.8], temp: 33, humidity: 58, windSpeed: 14, windDir: 170 },
  { position: [77.8, 18.5], temp: 27, humidity: 82, windSpeed: 5, windDir: 210 },
];

const rainRadarZones = [
  {
    polygon: [[78.2, 17.2], [78.8, 17.2], [78.8, 17.8], [78.2, 17.8]],
    intensity: 0.7,
  },
  {
    polygon: [[79.0, 18.0], [79.5, 18.0], [79.5, 18.5], [79.0, 18.5]],
    intensity: 0.3,
  },
  {
    polygon: [[77.8, 17.5], [78.2, 17.5], [78.2, 18.0], [77.8, 18.0]],
    intensity: 0.5,
  },
];

function getTempColor(temp: number): [number, number, number, number] {
  if (temp >= 35) return [220, 38, 38, 200];
  if (temp >= 32) return [234, 88, 12, 200];
  if (temp >= 29) return [251, 146, 60, 200];
  if (temp >= 26) return [251, 191, 36, 200];
  return [59, 130, 246, 200];
}

interface WeatherOverlayProps {
  showTemperature?: boolean;
  showStations?: boolean;
  showRainRadar?: boolean;
}

export function WeatherOverlay({
  showTemperature = true,
  showStations = true,
  showRainRadar = true,
}: WeatherOverlayProps) {
  const layers = useMemo(() => {
    const result: any[] = [];

    if (showRainRadar) {
      result.push(
        new PolygonLayer({
          id: "weather-rain-radar",
          data: rainRadarZones,
          getPolygon: (d: { polygon: [number, number][]; intensity: number }) => d.polygon,
          getFillColor: (d: { polygon: [number, number][]; intensity: number }) =>
            [59, 130, 246, Math.round(d.intensity * 100)] as [number, number, number, number],
          getLineColor: [59, 130, 246, 80] as [number, number, number, number],
          getLineWidth: 1,
          stroked: true,
        })
      );
    }

    if (showStations) {
      result.push(
        new ScatterplotLayer({
          id: "weather-stations",
          data: stations,
          getPosition: (d: WeatherStation) => d.position,
          getFillColor: (d: WeatherStation) =>
            showTemperature ? getTempColor(d.temp) : [59, 130, 246, 200] as [number, number, number, number],
          getRadius: 12,
          radiusMinPixels: 6,
          radiusMaxPixels: 18,
          pickable: true,
          autoHighlight: true,
          highlightColor: [255, 255, 255, 150],
          stroked: true,
          getLineColor: [255, 255, 255, 120] as [number, number, number, number],
          getLineWidth: 1.5,
        })
      );
    }

    if (showTemperature && showStations) {
      result.push(
        new ScatterplotLayer({
          id: "weather-temp-labels",
          data: stations,
          getPosition: (d: WeatherStation) => d.position,
          getFillColor: [0, 0, 0, 0] as [number, number, number, number],
          getRadius: 1,
          pickable: false,
        })
      );
    }

    return result;
  }, [showTemperature, showStations, showRainRadar]);

  return <>{layers}</>;
}

export type { WeatherStation };
