import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Shield, LayoutDashboard, FilePlus, Search, LogOut } from 'lucide-react';
import { logoutOfficer } from '../auth';

/**
 * Top navigation bar for Pramaan.
 * Shows officer links on officer pages and college links on college pages.
 */
export default function Navbar() {
  const location = useLocation();
  const navigate = useNavigate();

  const path = location.pathname;
  const isOfficerArea = path.startsWith('/dashboard') || path.startsWith('/application/');

  const navLinks = isOfficerArea
    ? [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }]
    : [
        { to: '/apply', label: 'New Application', icon: FilePlus },
        { to: '/track', label: 'Track Status', icon: Search },
      ];

  const handleLogout = () => {
    logoutOfficer();
    navigate('/');
  };

  return (
    <nav className="bg-primary-900 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / Branding */}
          <Link to="/" className="flex items-center gap-3 hover:opacity-90 transition-opacity">
            <div className="bg-primary-600 p-2 rounded-lg">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight tracking-tight">
                Pramaan <span className="font-normal text-primary-300">| प्रमाण</span>
              </h1>
              <p className="text-xs text-primary-300 leading-none">
                AI-Powered Application Verification
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => {
              const isActive = path === to || (to === '/dashboard' && path.startsWith('/application/'));
              return (
                <Link
                  key={to}
                  to={to}
                  className={`
                    flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium
                    transition-colors duration-200
                    ${isActive
                      ? 'bg-primary-700 text-white'
                      : 'text-primary-200 hover:bg-primary-800 hover:text-white'
                    }
                  `}
                >
                  <Icon className="w-4 h-4" />
                  {label}
                </Link>
              );
            })}

            {isOfficerArea && (
              <button
                onClick={handleLogout}
                className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-primary-200 hover:bg-primary-800 hover:text-white transition-colors duration-200"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
