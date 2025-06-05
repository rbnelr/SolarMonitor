import React, { useEffect, useRef, useState } from "react";
import Plotly from "plotly.js/dist/plotly";
import { EMPTY_DATA, fetchData } from "../api";
import type { Data } from "../api";


interface GraphProps {
  updateTrigger: number;
  setIsLoading?: (loading: boolean) => void;
}

const Graph: React.FC<GraphProps> = ({ updateTrigger, setIsLoading }) => {
  const ref = useRef<HTMLDivElement>(null);
  const layout = useRef<Plotly.Layout | null>(null);
  const plotData = useRef<Plotly.Data[] | null>(null);
  //const data = useRef<Data>(EMPTY_DATA);
  const [error, setError] = useState<string | null>(null);

  //const getXRange = () => {
  //  // Even though I provide plotly with number timestamps, it returns strings, so we need to convert them to dates
  //  if (plotRef.current === null) return null;
  //  console.log(plotRef.current);
  //  const range = plotRef.current.props.layout.xaxis!.range!;
  //  return [new Date(range[0]).getTime(), new Date(range[1]).getTime()];
  //};
  //const setXRange = (range: [number, number]) => {
  //  if (plotRef.current !== null) {
  //    //plotRef.current.layout.xaxis!.range = range;
  //    //plotRef.current.relayout({xaxis: {range: range}});
  //  }
  //};

  //const getLatestDataTime = () => {
  //  const t1 = graphData.by_minute.timestamps;
  //  const t2 = graphData.by_minute.timestamps;
  //  return Math.max(t1[t1.length - 1], t2[t2.length - 1]);
  //};

  // Init
  useEffect(() => {
    //if (!ref.current) return;

    layout.current = {
      xaxis: {
        type: "date",
        showline: true,
        linewidth: 1,
        linecolor: '#d0d0d0',
        mirror: true,
        tickfont: { size: 15 },
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
      uirevision: 0,
    } as Plotly.Layout;
    
    plotData.current = [
      {
        x: [],
        y: [],
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
        x: [],
        y: [],
        type: "scatter",
        mode: "lines",
        marker: { color: "#201000A0" },
        line: { width: 2.5, shape: "linear", simplify: true },
        name: "apower",
        showlegend: true,
      },
      {
        x: [],
        y: [],
        type: "scatter",
        mode: "lines",
        marker: { color: "#001020A0" },
        line: { width: 2.5, shape: "linear", simplify: true },
        name: "meter",
        showlegend: true,
      }
    ];

    Plotly.newPlot(ref.current, plotData.current, layout.current, { responsive: true, scrollZoom: true, displayModeBar: false });
  }, []);

  useEffect(() => {
    async function loadGraphData() {
      setIsLoading?.(true);
      setError(null);
      //setGraphData(EMPTY_DATA);
      const startTime = Date.now();
      
      try {
        const data = await fetchData();
        //console.log('Received data:', data);

        // Really unsure how I'm supposed to do this with Plotly.restyle, which if I understand correctly is supposed to be used for changing parts of the data
        plotData.current![0].x = data.by_minute.timestamps;
        plotData.current![0].y = data.by_minute.values;
        plotData.current![1].x = data.power.timestamps;
        plotData.current![1].y = data.power.values;
        plotData.current![2].x = data.meter.timestamps;
        plotData.current![2].y = data.meter.values;

        Plotly.react(ref.current, plotData.current, layout.current)

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
    
    //const xRange = getXRange();
    //if (xRange !== null) {
    //  // Move time axis to show new data if previous data was close to right edge of graph
    //  const newLatest = getLatestDataTime();
    //
    //  const xRangeWidth = xRange[1] - xRange[0];
    //  const oldScreenLoc = (oldLatest - xRange[0]) / xRangeWidth;
    //  const newScreenLoc = (newLatest - xRange[0]) / xRangeWidth;
    //
    //  console.log("oldScreenLoc", oldScreenLoc);
    //  console.log("newScreenLoc", newScreenLoc);
    //
    //  const interestedInAutoMove = oldScreenLoc <= 1.001;
    //  const needToAutoMove = newScreenLoc >= 0.95;
    //  if (interestedInAutoMove && needToAutoMove) {
    //    setXRange([newScreenLoc - xRangeWidth * 0.95, newScreenLoc + xRangeWidth * 0.05]);
    //  }
    //}

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
      <div ref={ref} style={{ width: "100%", height: "100%" }}/>
    </div>
  );
};

export default Graph;
