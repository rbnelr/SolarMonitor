import React, { useEffect, useRef, useState } from "react";
import Plot from "react-plotly.js";
import { EMPTY_DATA, fetchData } from "../api";
import type { Data } from "../api";

interface GraphProps {
  updateTrigger: number;
  setIsLoading?: (loading: boolean) => void;
}

const Graph: React.FC<GraphProps> = ({ updateTrigger, setIsLoading }) => {
  const [graphData, setGraphData] = useState<Data>(EMPTY_DATA);
  const [error, setError] = useState<string | null>(null);
  
  //const getLatestDataTime = () => {
  //  const t1 = graphData.by_minute.timestamps;
  //  const t2 = graphData.by_minute.timestamps;
  //  return Math.max(t1[t1.length - 1], t2[t2.length - 1]);
  //};

  useEffect(() => {
    async function loadGraphData() {
      setIsLoading?.(true);
      setError(null);
      //setGraphData(EMPTY_DATA);
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
    
    //const oldLatest = getLatestDataTime();

    loadGraphData();

    /*if (xRange.current !== null) {
      // Move time axis to show new data if previous data was close to right edge of graph
      const newLatest = getLatestDataTime();

      const xRangeWidth = xRange.current[1] - xRange.current[0];
      const oldScreenLoc = (oldLatest - xRange.current[0]) / xRangeWidth;
      const newScreenLoc = (newLatest - xRange.current[0]) / xRangeWidth;

      console.log("xRange", xRange.current);
      console.log("oldScreenLoc", oldScreenLoc);
      console.log("newScreenLoc", newScreenLoc);

      const interestedInAutoMove = oldScreenLoc <= 1.001;
      const needToAutoMove = newScreenLoc >= 0.95;
      if (interestedInAutoMove && needToAutoMove) {
        setXRange(newScreenLoc - xRangeWidth * 0.95, newScreenLoc + xRangeWidth * 0.05);
      }
    }*/

  }, [updateTrigger, setIsLoading]);

  // Performance: (From what I can tell)
  // spline smoothing for traces is quite slow so prefer linear display
  // Seems like passing the data to plotly and react both don't matter, the main bottleneck is the amount of data and plotly layout and rendering
  // panning is fast (browser caches rendered svg?)
  // zooming and window resize are quick enough
  // (just noticed that resizing actually attempts to wait until your mouse stops moving, which can appear as lag but likely is just as fast at redrawing as mousewheel zooming)
  // Actually performance without smoothing is good with test data (data.txt)

  // BUG: zooming breaks time axis? but panning first then zooming works
  return (
    <div className="plot-container">
      {error && <div className="error-message">{error}</div>}
      <Plot
        data={[
          {
            x: graphData.by_minute.timestamps,
            y: graphData.by_minute.values,
            type: "scatter",
            mode: "lines+markers",
            fill: "tozeroy",
            fillcolor: "#F3D70030",
            connectgaps: false,
            marker: { color: "#F3D700" },
            line: { width: 2.5, shape: "vh", simplify: true },
            name: "by_minute",
            showlegend: true,
          },
          {
            x: graphData.power.timestamps,
            y: graphData.power.values,
            type: "scatter",
            mode: "lines",
            marker: { color: "#201000A0" },
            line: { width: 2.5, shape: "linear", simplify: true },
            name: "apower",
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
            tickfont: { size: 15 },

            //rangeslider: { visible: true },
            rangeselector: { // Seemingly don't actually work with panning, but this is easy to implement myself
              buttons: [
                {
                  count: 1,
                  label: "1h",
                  step: "hour",
                  stepmode: "backward"
                },
                {
                  count: 1,
                  label: "1d",
                  step: "day",
                  stepmode: "backward"
                }
              ]
            },
          },
          yaxis: {
            showline: true,
            linewidth: 1,
            linecolor: '#d0d0d0',
            mirror: true,
            // Shows Watts as 100W / 100kW / 100MW etc., note that using " W" breaks as it displays as 100k W etc.
            // However M actually stands for million not mega, so instead of GW (gigawatt) we get BW (billion watt), which is wrong, but probably irrelevant for our use case
            ticksuffix: "W",
            tickfont: { size: 15 },
            fixedrange: true, // TODO: Allow zooming and pan of y axis, how? Toggle x/y being fixed with ctrl key and or toggle button (good for mobile)?
            range: [-100, 1100],
          },
          margin: { t: 20, r: 20, b: 55, l: 65 },
          autosize: true,
          plot_bgcolor: '#f8f8f8',
          paper_bgcolor: "white",
          showlegend: true,
          legend: {
            x: 0,
            y: 1,
            xanchor: "left",
            bgcolor: "transparent"
          },
          dragmode: "pan",
          uirevision: 'true'
        }}
        style={{ width: "100%", height: "100%" }}
        config={{ responsive: true, scrollZoom: true, displayModeBar: false }}
      />
    </div>
  );
};

export default Graph;
