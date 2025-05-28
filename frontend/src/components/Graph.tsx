import React, { useEffect, useState } from "react";
import Plot from "react-plotly.js";
import { fetchData } from "../api";
import type { DataSets } from "../api";

interface GraphProps {
  reloadTrigger: number;
  onLoadingChange?: (loading: boolean) => void;
}

const Graph: React.FC<GraphProps> = ({ reloadTrigger, onLoadingChange }) => {
  const [graphData, setGraphData] = useState<{
    data: DataSets;
  }>({
    data: {
      energyUsage: { timestamps: [], values: [] },
      solarPower: { timestamps: [], values: [] }
    }
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let buttonAnimationTimer: number;

    async function loadGraphData() {
      try {
        onLoadingChange?.(true);
        
        // Start button animation timer
        buttonAnimationTimer = window.setTimeout(() => {
          onLoadingChange?.(false);
        }, 300);

        const data = await fetchData();
        setGraphData({ data });
      } catch (err) {
        setError("Failed to load data.");
      }
    }

    loadGraphData();

    return () => {
      if (buttonAnimationTimer) {
        clearTimeout(buttonAnimationTimer);
      }
    };
  }, [reloadTrigger, onLoadingChange]);

  if (error) return <div>{error}</div>;

  return (
    <div className="plot-container">
      <Plot
        data={[
          {
            x: graphData.data.energyUsage.timestamps,
            y: graphData.data.energyUsage.values,
            type: "scatter",
            mode: "lines",
            fill: 'tozeroy',
            marker: { color: "blue" },
            line: { width: 4, shape: 'spline', smoothing: 0.75, simplify: true },
            name: "Energy Usage",
            showlegend: true
          },
          {
            x: graphData.data.solarPower.timestamps,
            y: graphData.data.solarPower.values,
            type: "scatter",
            mode: "lines",
            fill: 'tozeroy',
            marker: { color: "#eee600" },
            line: { width: 4, shape: 'spline', smoothing: 0.75, simplify: true },
            name: "Solar Power",
            showlegend: true
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
            ticksuffix: "W",
            showline: true,
            linewidth: 1,
            linecolor: '#d0d0d0',
            mirror: true,
            tickfont: { size: 15 }
          },
          margin: { t: 20, r: 20, b: 55, l: 65 },
          autosize: true,
          plot_bgcolor: '#f8f8f8',
          paper_bgcolor: 'white',
          showlegend: true,
          legend: {
            x: 0,
            y: 1,
            xanchor: 'left',
            bgcolor: 'transparent'
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
