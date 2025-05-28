
export interface EnergyDataPoint {
  timestamp: string;
  value: number;
}

export async function fetchData(): Promise<EnergyDataPoint[]> {
  const response = await fetch("http://127.0.0.1:8000/data");
  if (!response.ok) {
    throw new Error("Failed to fetch data from the backend.");
  }
  return response.json();
}
