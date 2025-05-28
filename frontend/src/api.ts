
export interface DataSet {
  timestamps: number[];  // Unix milliseconds
  values: number[];
}
export interface DataSets {
  energyUsage: DataSet;
  solarPower: DataSet;
}


export async function fetchData(): Promise<DataSets> {
  const response = await fetch("http://127.0.0.1:8000/data");
  if (!response.ok) {
    throw new Error("Failed to fetch data from the backend.");
  }
  return response.json();
}
