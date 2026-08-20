"use client";

import { MapContainer, TileLayer } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Field } from "@/lib/api";

type FieldMapProps = {
  fields: Field[];
};

// Default map center: rough global view, no fields rendered yet.
const DEFAULT_CENTER: [number, number] = [20, 0];
const DEFAULT_ZOOM = 2;

export default function FieldMap({ fields }: FieldMapProps) {
  // `fields` is accepted now so callers can pass existing data down,
  // but it is intentionally unused until polygon rendering is added.
  void fields;

  return (
    <div className="h-96 w-full overflow-hidden rounded-lg border border-gray-200">
      <MapContainer
        center={DEFAULT_CENTER}
        zoom={DEFAULT_ZOOM}
        scrollWheelZoom={false}
        className="h-full w-full"
      >
        <TileLayer
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        />
      </MapContainer>
    </div>
  );
}