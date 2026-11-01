import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Shield, Lock, AlertCircle, ArrowLeft } from 'lucide-react';
import { loginOfficer, DEMO_OFFICER_ID, DEMO_PASSWORD } from '../auth';

/**
 * Officer login (demo). On success, goes to the dashboard, or back to the
 * page the officer originally tried to open.
 */
export default function OfficerLogin() {
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || '/dashboard';

  const [officerId, setOfficerId] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!officerId.trim() || !password) {
      setError('Please enter your Officer ID and password.');
      return;
    }
    if (loginOfficer(officerId, password)) {
      navigate(redirectTo, { replace: true });
    } else {
      setError('Invalid Officer ID or password.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-primary-900 to-primary-800 flex flex-col items-center justify-center px-4 py-10">
      <div className="w-full max-w-md">
        <div className="text-center text-white mb-6">
          <div className="inline-flex bg-primary-600 p-3 rounded-xl mb-3">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight">
            Pramaan <span className="font-normal text-primary-300">| प्रमाण</span>
          </h1>
          <p className="text-primary-300 text-sm mt-1">Officer Sign In</p>
        </div>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-xl p-6">
          <div className="mb-4">
            <label htmlFor="officerId" className="block text-sm font-medium text-gray-700 mb-1">Officer ID</label>
            <input
              id="officerId"
              type="text"
              autoComplete="username"
              value={officerId}
              onChange={(e) => setOfficerId(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none"
            />
          </div>

          <div className="mb-4">
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-primary-500 focus:border-primary-500 focus:outline-none"
            />
          </div>

          {error && (
            <p className="mb-4 text-sm text-red-600 flex items-center gap-2">
              <AlertCircle size={16} className="flex-shrink-0" /> {error}
            </p>
          )}

          <button
            type="submit"
            className="w-full inline-flex items-center justify-center gap-2 bg-primary-700 text-white px-5 py-3 rounded-lg font-semibold hover:bg-primary-800 transition-colors"
          >
            <Lock size={16} /> Sign In
          </button>

          <div className="mt-4 text-xs text-gray-500 bg-gray-50 border border-gray-200 rounded-lg p-3">
            <p className="font-semibold text-gray-600 mb-1">Demo access (prototype only)</p>
            <p>Officer ID: <span className="font-mono">{DEMO_OFFICER_ID}</span></p>
            <p>Password: <span className="font-mono">{DEMO_PASSWORD}</span></p>
          </div>
        </form>

        <div className="text-center mt-5">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-primary-200 hover:text-white">
            <ArrowLeft size={14} /> Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
