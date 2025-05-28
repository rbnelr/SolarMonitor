import React from "react";
import Graph from "./components/Graph";
import "./styles.css";

const App: React.FC = () => {
  return (
    <div className="app-container">
      <h1>Energy Use Monitor</h1>
      <Graph />
    </div>
  );
};

export default App;
