// Data in struct of arrays format since plotly expects it this way
// Should also be more efficient than array of objects due to how json encodes it
export interface Data {
  solar: { timestamps: number[]; values: number[] };
  solar_by_minute: { timestamps: number[]; values: number[] };
  meter_power: { timestamps: number[]; values: number[] };
  meter_reading: { timestamps: number[]; values: number[] };
  load: { timestamps: number[]; values: number[] };
  savings: { timestamps: number[]; values: number[] };
  latest_meter_energy: number;
}
//export const EMPTY_DATA: Data = {
//  power: { timestamps: [], values: [] },
//  by_minute: { timestamps: [], values: [] },
//  meter: { timestamps: [], values: [] },
//};

export async function fetchData(start?: number, end?: number): Promise<Data> {
  let url = new URL('http://localhost:8000/data');

  if (start !== undefined) url.searchParams.append('start', start.toString());
  if (end !== undefined) url.searchParams.append('end', end.toString());

  console.log('fetch(%s)', url.toString());
  const response = await fetch(url.toString());

  if (!response.ok) {
    throw new Error('Failed to fetch data');
  }
  return await response.json(); // Convert json response to Data object with native arrays
}
