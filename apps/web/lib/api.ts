export type HealthResponse = {
  status: string;
};

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL;

export async function getHealth(): Promise<HealthResponse> {
  if (!API_BASE_URL) {
    throw new Error("NEXT_PUBLIC_API_BASE_URL is not defined");
  }

  const response = await fetch(`${API_BASE_URL}/health`);

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  const data: HealthResponse = await response.json();
  return data;
}