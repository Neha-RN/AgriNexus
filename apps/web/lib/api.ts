export type HealthResponse = {
  status: string;
};

export type GeoJSONGeometry = {
  type: string;
  coordinates: unknown[];
};

export type Field = {
  id: number;
  country_id: number;
  name: string;
  crop_type: string | null;
  area_hectares: string | null;
  geometry: GeoJSONGeometry | null;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

function getBaseUrl(): string {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not defined");
  }

  return API_BASE_URL;
}

export async function getHealth(): Promise<HealthResponse> {
  const response = await fetch(`${getBaseUrl()}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  const data: HealthResponse = await response.json();
  return data;
}

export async function getFields(): Promise<Field[]> {
  const response = await fetch(`${getBaseUrl()}/api/v1/fields`);

  if (!response.ok) {
    throw new Error(`Fields request failed with status ${response.status}`);
  }

  const data: Field[] = await response.json();
  return data;
}