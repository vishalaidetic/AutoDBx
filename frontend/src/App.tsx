import { Route, BrowserRouter as Router, Routes } from "react-router-dom";
// import { Toaster } from 'react-hot-toast'; // Import Toaster
import AutodbxPage from "./components/AutodbxPage";
import AWSDataViewer from "./components/AWSDataViewer";
import DataVisualizationPage from "./components/DataVisualizationPage";
import HomePage from "./components/HomePage";
import Navigation from "./components/Navigation";
import TableDataPage from "./components/TableDataPage";

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
          <Route path="/operations" element={<AutodbxPage />} />
          <Route path="/aws-view" element={<AWSDataViewer />} />
          <Route path="*" element={<HomePage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
