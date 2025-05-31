export interface Data {
  readings: any[];
}
export const EMPTY_DATA: Data = {
  readings: []
};

export async function fetchData(): Promise<Data> {
  const response = await fetch('http://localhost:8000/data');
  if (!response.ok) {
    throw new Error('Failed to fetch data');
  }
  return await response.json();
}
