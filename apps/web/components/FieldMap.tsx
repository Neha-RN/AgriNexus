"use client";

import { useEffect, useMemo } from "react";
import { GeoJSON, MapContainer, TileLayer, useMap } from "react-leaflet";
import type { Feature, FeatureCollection } from "geojson";
import * as L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Field } from "@/lib/api";

type FieldMapProps = {
  fields: Field[];
};

const DEFAULT_CENTER: [number, number] = [20, 0];
const DEFAULT_ZOOM = 2;

function fieldsToFeatureCollection(fields: Field[]): FeatureCollection {
  return {
    type: "FeatureCollection",
    features: fields
      .filter((field) => field.geometry !== null)
      .map((field) => ({
        type: "Feature",
        properties: {
          id: field.id,
          name: field.name,
          crop_type: field.crop_type,
          area_hectares: field.area_hectares,
        },
        geometry: field.geometry as GeoJSON.Geometry,
      })),
  };
}

function FitFieldBounds({
  featureCollection,
}: {
  featureCollection: FeatureCollection;
}) {
  const map = useMap();

  useEffect(() => {
    if (featureCollection.features.length === 0) {
      return;
    }

    const layer = L.geoJSON(featureCollection);
    const bounds = layer.getBounds();

    if (bounds.isValid()) {
      map.fitBounds(bounds, {
        padding: [20, 20],
      });
    }
  }, [map, featureCollection]);

  return null;
}

function FieldLayers({
  featureCollection,
}: {
  featureCollection: FeatureCollection;
}) {
  const map = useMap();

  const fieldStyle = {
    weight: 3,
    opacity: 1,
    fillOpacity: 0.45,
  };

  const handleEachField = (
    feature: Feature,
    layer: L.Layer,
  ) => {
    const properties = feature.properties;

    const name = properties?.name ?? "Field";
    const cropType = properties?.crop_type ?? "Unknown crop";
    const area = properties?.area_hectares ?? "Unknown";

    layer.bindPopup(`
      <strong>${name}</strong><br/>
      Crop: ${cropType}<br/>
      Area: ${area} ha
    `);

    layer.on({
      click: () => {
        const bounds = L.geoJSON(feature).getBounds();

        if (bounds.isValid()) {
          map.fitBounds(bounds, {
            padding: [40, 40],
            maxZoom: 16,
          });
        }
      },

      mouseover: (event) => {
        const target = event.target;

        target.setStyle({
          weight: 4,
          fillOpacity: 0.65,
        });

        target.bringToFront();
      },

      mouseout: (event) => {
        event.target.setStyle(fieldStyle);
      },
    });
  };

  return (
    <GeoJSON
      data={featureCollection}
      style={fieldStyle}
      onEachFeature={handleEachField}
    />
  );
}

export default function FieldMap({ fields }: FieldMapProps) {
  const featureCollection = useMemo(
    () => fieldsToFeatureCollection(fields),
    [fields],
  );

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

        <FieldLayers featureCollection={featureCollection} />

        <FitFieldBounds featureCollection={featureCollection} />
      </MapContainer>
    </div>
  );
}