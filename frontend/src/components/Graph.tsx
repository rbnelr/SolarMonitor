import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { EMPTY_DATA, fetchData } from "../api";
import type { Data } from "../api";

interface GraphProps {
  reloadTrigger: number;
  setIsLoading?: (loading: boolean) => void;
}

const Graph: React.FC<GraphProps> = ({ reloadTrigger, setIsLoading }) => {
  const [graphData, setGraphData] = useState<Data>(EMPTY_DATA);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadGraphData() {
      setIsLoading?.(true);
      setError(null);
      setGraphData(EMPTY_DATA);
      const startTime = Date.now();

      try {
        const data = await fetchData();
        //console.log('Received data:', data);
        setGraphData(data);
      } catch (err) {
        setError("Failed to load data.");
      } finally {
        const remainingTime = 500 - (Date.now() - startTime); // Animate at least one rotation for button
        if (remainingTime > 0) {
          window.setTimeout(() => setIsLoading?.(false), remainingTime);
        } else {
          setIsLoading?.(false);
        }
      }
    }

    loadGraphData();
  }, [reloadTrigger, setIsLoading]);

  return (
    <div className="plot-container">
      {error && <div className="error-message">{error}</div>}
      <Plot
        data={[
          {
            x: graphData.power.map(x => x.timestamp),
            y: graphData.power.map(x => x.value),
            type: "scatter",
            mode: "lines",
            marker: { color: "#003000" },
            line: { width: 2.5, shape: "spline", smoothing: 0.75, simplify: true },
            name: "apower",
            showlegend: true,
          },
          {
            x: graphData.by_minute.map(x => x.timestamp),
            y: graphData.by_minute.map(x => x.value),
            type: "scatter",
            mode: "lines+markers",
            marker: { color: "#5060FF" },
            line: { width: 2.5, shape: "vh", simplify: true },
            name: "by_minute[0]",
            showlegend: true,
          }
        ]}
        layout={{
          xaxis: {
            type: "date",
            showline: true,
            linewidth: 1,
            linecolor: '#d0d0d0',
            mirror: true,
            tickfont: { size: 15 }
          },
          yaxis: {
            title: { text: 'Power (W)' },
            showline: true,
            linewidth: 1,
            linecolor: '#d0d0d0',
            mirror: true,
            tickfont: { size: 15 }
          },
          margin: { t: 20, r: 65, b: 55, l: 65 },
          autosize: true,
          plot_bgcolor: '#f8f8f8',
          paper_bgcolor: "white",
          showlegend: true,
          legend: {
            x: 0,
            y: 1,
            xanchor: "left",
            bgcolor: "transparent"
          }
        }}
        style={{ width: "100%", height: "100%" }}
        useResizeHandler={true}
        config={{ responsive: true }}
      />
    </div>
  );
};

export default Graph;
