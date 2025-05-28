import React, { useState, useCallback } from "react";
import Graph from "./components/Graph";
import "./styles.css";

const App: React.FC = () => {
  const [reloadTrigger, setReloadTrigger] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const handleReload = useCallback(() => {
    setReloadTrigger(prev => prev + 1);
  }, []);

  return (
    <div className="app-container">
      <div className='header'>
        <div>Energy Use Monitor</div>
        <button 
          className={`reload-button ${isLoading ? 'spinning' : ''}`} 
          onClick={handleReload} disabled={isLoading} aria-label="Reload data"
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
      <Graph reloadTrigger={reloadTrigger} onLoadingChange={setIsLoading} />
    </div>
  );
};

export default App;
