import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import OfficerLogin from './pages/OfficerLogin';
import Dashboard from './pages/Dashboard';
import ApplicationForm from './pages/ApplicationForm';
import ApplicationDetail from './pages/ApplicationDetail';
import TrackStatus from './pages/TrackStatus';
import { isOfficerLoggedIn } from './auth';

/**
 * Pramaan - main application component with routing.
 *
 *   /                 Home (choose Officer or College)
 *   /officer-login    Officer sign in (demo)
 *   /dashboard        Officer dashboard            (officer only)
 *   /application/:id  Verification report          (officer only)
 *   /apply            New application              (college)
 *   /track            Track application status     (college)
 */

/** Sends visitors to the officer login if they are not signed in. */
function RequireOfficer({ children }) {
  const location = useLocation();
  if (!isOfficerLoggedIn()) {
    return <Navigate to="/officer-login" state={{ from: location.pathname }} replace />;
  }
  return children;
}

// Pages that use their own full-screen layout (no top navbar)
const FULLSCREEN_PATHS = ['/', '/officer-login'];

function App() {
  const location = useLocation();
  const fullscreen = FULLSCREEN_PATHS.includes(location.pathname);

  return (
    <div className="min-h-screen bg-gray-50">
      {!fullscreen && <Navbar />}
      {fullscreen ? (
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/officer-login" element={<OfficerLogin />} />
        </Routes>
      ) : (
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <Routes>
            <Route path="/dashboard" element={<RequireOfficer><Dashboard /></RequireOfficer>} />
            <Route path="/application/:id" element={<RequireOfficer><ApplicationDetail /></RequireOfficer>} />
            <Route path="/apply" element={<ApplicationForm />} />
            <Route path="/track" element={<TrackStatus />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      )}
    </div>
  );
}

export default App;
