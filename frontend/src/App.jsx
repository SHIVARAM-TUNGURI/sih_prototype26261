import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Dashboard from './pages/Dashboard';
import ApplicationForm from './pages/ApplicationForm';
import ApplicationDetail from './pages/ApplicationDetail';
import TrackStatus from './pages/TrackStatus';

/**
 * Main application component with routing.
 * Defines the three primary views: Dashboard, Application Form, and Application Detail.
 */
function App() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/apply" element={<ApplicationForm />} />
          <Route path="/track" element={<TrackStatus />} />
          <Route path="/application/:id" element={<ApplicationDetail />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
