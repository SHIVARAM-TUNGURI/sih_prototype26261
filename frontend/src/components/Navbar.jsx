import { Link, useLocation } from 'react-router-dom';
import { Shield, LayoutDashboard, FilePlus } from 'lucide-react';

/**
 * Top navigation bar for the AICTE Smart Verification system.
 * Shows branding, and navigation links to Dashboard and New Application.
 */
export default function Navbar() {
  const location = useLocation();

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/apply', label: 'New Application', icon: FilePlus },
  ];

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
                AICTE Smart Verification
              </h1>
              <p className="text-xs text-primary-300 leading-none">
                AI-Powered Application Validation
              </p>
            </div>
          </Link>

          {/* Navigation Links */}
          <div className="flex items-center gap-1">
            {navLinks.map(({ to, label, icon: Icon }) => {
              const isActive = location.pathname === to;
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
          </div>
        </div>
      </div>
    </nav>
  );
}
