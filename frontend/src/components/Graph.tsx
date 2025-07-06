import React, { useEffect, useRef, useState } from "react";
import Plotly from "plotly.js/dist/plotly";
import { fetchData } from "../api";
import type { Data } from "../api";


interface GraphProps {
  updateTrigger: number;
  autoUpdating: boolean;
  setIsLoading?: (loading: boolean) => void;
  setLatestMeter?: (value: number) => void;
}

const Graph: React.FC<GraphProps> = ({ updateTrigger, setIsLoading, autoUpdating, setLatestMeter }) => {
  const div = useRef<HTMLDivElement>(null);
  const layout = useRef<Plotly.Layout | null>(null);
  const plotData = useRef<Plotly.Data[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Could not find a better way of doing this, and this still does not give me the range while panning happens, only when mouse is released
  const getXRange = () => {
    // Even though I provide plotly with number timestamps, it returns strings, so we need to convert them to dates
    if (div.current === null || (div.current as any)._fullLayout === undefined) return null;
    const range = (div.current as any)._fullLayout.xaxis!.range!;
    return [new Date(range[0]).getTime(), new Date(range[1]).getTime()];
  };
  const getYRange = () => {
    if (div.current === null || (div.current as any)._fullLayout === undefined) return null;
    const range = (div.current as any)._fullLayout.yaxis!.range!;
    return [range[0], range[1]];
  };

  const getLatestDataTime = () => {
    var maxTime = -Infinity;
    for (const trace of plotData.current!) {
      if (trace.x.length > 0) {
        maxTime = Math.max(maxTime, trace.x[trace.x.length - 1]);
      }
    }
    return maxTime;
  };

  const leftMargin = 65;

  // Init
  useEffect(() => {
    //if (!ref.current) return;

    const today = new Date();
    const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate());
    const todayEnd = new Date(today.getFullYear(), today.getMonth(), today.getDate() + 1);

    layout.current = {
      xaxis: {
        type: "date",
        showline: true,
        linewidth: 1,
        linecolor: '#d0d0d0',
        mirror: true,
        tickfont: { size: 15 },
        autorange: false,
        range: [todayStart.getTime(), todayEnd.getTime()],
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
        autorange: false,
        fixedrange: false, // TODO: Allow zooming and pan of y axis, how? Toggle x/y being fixed with ctrl key and or toggle button (good for mobile)?
        zoom: "up",
        range: [-100, 1100],
      },
      margin: { t: 20, r: 20, b: 55, l: leftMargin },
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
        mode: "lines",
        marker: { color: "#1F303EA0" },
        line: { width: 1.0, shape: "linear", simplify: true },
        name: "meter",
        showlegend: true,
      },
      {
        x: [],
        y: [],
        type: "scatter",
        mode: "lines",
        fill: "tozeroy",
        fillcolor: "#1F303E60",
        connectgaps: false,
        marker: { color: "#1F303E" },
        line: { width: 2.0, shape: "linear", simplify: true },
        name: "load",
        showlegend: true,
      },
      {
        x: [],
        y: [],
        type: "scatter",
        mode: "lines",
        fill: "tozeroy",
        fillcolor: "#F3D70040",
        marker: { color: "#F3D700C0" },
        line: { width: 2.0, shape: "linear", simplify: true },
        name: "apower",
        showlegend: true,
      },
      //{
      //  x: [],
      //  y: [],
      //  type: "scatter",
      //  mode: "lines+markers",
      //  connectgaps: false,
      //  marker: { color: "#F3D700" },
      //  line: { width: 1.0, shape: "vh", simplify: true },
      //  name: "by_minute",
      //  showlegend: true,
      //}
    ];

    Plotly.newPlot(div.current, plotData.current, layout.current, { responsive: true, scrollZoom: true, displayModeBar: false });
    
    //div.current!.on('plotly_relayout', function(eventdata : any) {
    //  console.log('plotly_relayout! ', eventdata);
    //});
  }, []);

  useEffect(() => {
    const oldLatest = getLatestDataTime();

    const autopan = () => {
      const enable = autoUpdating; // && Not currently panning by mouse (but that's seemingly not possible to know with plotly) 

      const xRange = getXRange();
      if (xRange !== null) {
        // Move time axis to show new data if previous data was close to right edge of graph
        const newLatest = getLatestDataTime();
      
        const xRangeWidth = xRange[1] - xRange[0];
        const oldScreenLoc = (oldLatest - xRange[0]) / xRangeWidth;
        const newScreenLoc = (newLatest - xRange[0]) / xRangeWidth;
      
        //console.log(`screenLoc ${oldScreenLoc} => ${newScreenLoc}`);
      
        const interestedInAutopan = oldScreenLoc <= 1.001;
        const needToAutopan = newScreenLoc >= 0.95;
        if (enable && interestedInAutopan && needToAutopan) {
          // Applies at next Plotly.react
          layout.current!.xaxis!.range = [Math.round(newLatest - 0.95 * xRangeWidth), Math.round(newLatest + 0.05 * xRangeWidth)];
        }
      }
    }

    async function loadGraphData() {
      setIsLoading?.(true);
      setError(null);
      //setGraphData(EMPTY_DATA);
      const startTime = Date.now();
      
      try {
        let data;

        const timeRange = getXRange();
        if (timeRange !== null) {
          // If autoupdating: always load data up to present
          // TODO: only if panned to the right (ie only if autopan would even happen)?
          data = await fetchData(timeRange[0], autoUpdating ? undefined : timeRange[1]);
        } else {
          data = await fetchData();
        }
        //console.log('Received data:', data);

        // Really unsure how I'm supposed to do this with Plotly.restyle, which if I understand correctly is supposed to be used for changing parts of the data
        
        plotData.current![0].x = data.meter.timestamps;
        plotData.current![0].y = data.meter.values;
        plotData.current![1].x = data.load.timestamps;
        plotData.current![1].y = data.load.values;
        //plotData.current![2].x = data.solar_by_minute.timestamps;
        //plotData.current![2].y = data.solar_by_minute.values;
        plotData.current![2].x = data.solar.timestamps;
        plotData.current![2].y = data.solar.values;
        
        setLatestMeter?.(data.latest_meter_energy);

        autopan();

        Plotly.react(div.current, plotData.current, layout.current);
        
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
  }, [updateTrigger, setIsLoading]);

  // pan/scroll x on main plot, but y while hovering y axis by toggling yaxis.fixedrange
  useEffect(() => {
    if (!div.current) return;

    const handleMouseMove = (e: MouseEvent) => {
      // Get plot dimensions
      const rect = div.current!.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;

      // Check if mouse is over y-axis area
      const isOverYAxis = mouseX < leftMargin;
      const wasOverYAxis = layout.current!.yaxis!.fixedrange! == false;
      
      //console.log('Over y-axis:', isOverYAxis);
      if (isOverYAxis != wasOverYAxis) {
        layout.current!.yaxis!.fixedrange = !isOverYAxis;
        Plotly.relayout(div.current, {
          yaxis: {
            fixedrange: !isOverYAxis,
            // Explicitly set range to range it is already at becaue for some reason if I don't it autofits despite autorange=false
            // Maybe this is intended (specify what behavior you want when toggling on fixedrange?)
            // Seems like this somehow even retains my original range (I would have expected it to be reset to my original range on the next Plotly.react)
            // So with this I get my desired behavior
            range: getYRange()
          }
        });
      }
    };

    div.current.addEventListener('mousemove', handleMouseMove);
    
    // Cleanup
    return () => {
      div.current?.removeEventListener('mousemove', handleMouseMove);
    };
  }, []);

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
      <div ref={div} style={{ width: "100%", height: "100%" }}/>
    </div>
  );
};

export default Graph;
