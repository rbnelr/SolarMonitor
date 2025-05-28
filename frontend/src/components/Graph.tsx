import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { fetchData } from "../api";

const Graph: React.FC = () => {
  const [graphData, setGraphData] = useState<{ x: string[]; y: number[] }>({
    x: [],
    y: [],
  });
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadGraphData() {
      try {
        setLoading(true);
        const data = await fetchData();
        const x = data.map((point) => point.timestamp);
        const y = data.map((point) => point.value);
        setGraphData({ x, y });
      } catch (err) {
        setError("Failed to load data.");
      } finally {
        setLoading(false);
      }
    }
    loadGraphData();
  }, []);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>{error}</div>;

  return (
    <div className="plot-container">
      <Plot
        data={[
          {
            x: graphData.x,
            y: graphData.y,
            type: "scatter",
            mode: "lines+markers",
            marker: { color: "blue" },
          },
        ]}
        layout={{
          title: { text: "Energy Usage Over Time" },
          xaxis: { title: { text: "Time" }, type: "date" },
          yaxis: { title: { text: "Energy Usage (kW)" } },
          margin: { t: 40, r: 20, b: 40, l: 60 },
          autosize: true
        }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={true}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default Graph;
