import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
// import { Toaster } from 'react-hot-toast'; // Import Toaster
import Navigation from "./components/Navigation";
import HomePage from "./components/HomePage";
import DataVisualizationPage from "./components/DataVisualizationPage";
import TableDataPage from "./components/TableDataPage";
import AutodbxPage from "./components/AutodbxPage";

function App() {
  return (
    <Router>
      <div className="min-h-screen">
        <Navigation /> 
        {/* Add Toaster for notifications */}

        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/visualization" element={<DataVisualizationPage />} />
          <Route
            path="/data-view/:catalogName/:schemaName/:tableName"
            element={<TableDataPage />}
          />
          <Route path="/databricks-operations" element={<AutodbxPage />} /> {/* New route for DatabricksOperations */}
          <Route path="*" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
