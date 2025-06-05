import React, { useState, useCallback, useEffect } from "react";
import Graph from "./components/Graph";
import "./styles.css";

const AUTO_UPDATE_INTERVAL = 5000; // 5 seconds

const App: React.FC = () => {
  const [updateTrigger, setUpdateTrigger] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [autoUpdate, setAutoUpdate] = useState(false);

  const handleUpdate = useCallback(() => {
    setUpdateTrigger(prev => prev + 1);
  }, []);

  useEffect(() => {
    if (autoUpdate) {
      handleUpdate(); // quicker feedback (since intention was to reload)
      const interval = setInterval(handleUpdate, AUTO_UPDATE_INTERVAL);
      return () => clearInterval(interval);
    }
  }, [autoUpdate, handleUpdate]);

  return (
    <div className="app-container">
      <div className='header'>
        <div className="header-title">Energy Use Monitor</div>

        <div className="controls">
          <label className="auto-update-toggle">
            <span className="toggle-label">Auto-update</span>
            <input
              type="checkbox"
              checked={autoUpdate}
              onChange={e => setAutoUpdate(e.target.checked)}
            />
            <span className="toggle-slider"></span>
          </label>

          <button 
            className={`reload-button ${isLoading ? 'spinning' : ''}`} 
            onClick={handleUpdate} disabled={isLoading} aria-label="Reload data"
          >
            <svg viewBox="0 0 24 24" width="28" height="28">
              <path
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
                d="M21 12c0 5-4 9-9 9s-9-4-9-9 4-9 9-9c3.1 0 5.9 1.6 7.5 4.5M21 8V2m0 6h-6"
              />
            </svg>
          </button>
        </div>
      </div>
      <Graph updateTrigger={updateTrigger} setIsLoading={setIsLoading} autoUpdating={autoUpdate} />
    </div>
  );
};

export default App;
