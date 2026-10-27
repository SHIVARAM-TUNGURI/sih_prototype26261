import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BarChart3, Clock, Zap, AlertTriangle, RefreshCw,
  ArrowUpDown, ChevronRight, FileSearch,
} from 'lucide-react';
import { getApplications } from '../api';
import ScoreCard from '../components/ScoreCard';
import StatusBadge from '../components/StatusBadge';

/**
 * Officer Dashboard page.
 * Displays application queue with stats cards, sortable table,
 * and color-coded route badges.
 */
export default function Dashboard() {
  const navigate = useNavigate();
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [sortField, setSortField] = useState('trust_score');
  const [sortAsc, setSortAsc] = useState(true);

  /** Fetch applications from the backend. */
  const fetchApplications = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getApplications();
      setApplications(Array.isArray(data) ? data : data.applications || []);
    } catch (err) {
      console.error('Failed to fetch applications:', err);
      setError('Failed to load applications. Is the backend running?');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchApplications();
  }, []);

  // ─── Derived Stats ──────────────────────────────────────────────────────────

  const stats = {
    total: applications.length,
    pending: applications.filter(
      (a) => ['submitted', 'pending_review', 'processed'].includes(a.status)
    ).length,
    fastTrack: applications.filter((a) => a.route === 'fast-track').length,
    flagged: applications.filter(
      (a) => a.route === 'senior-review' || (a.trust_score != null && a.trust_score < 40)
    ).length,
  };

  // ─── Sorting ────────────────────────────────────────────────────────────────

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(field === 'trust_score'); // default ascending for scores
    }
  };

  const sortedApplications = [...applications].sort((a, b) => {
    const aVal = a[sortField] ?? 0;
    const bVal = b[sortField] ?? 0;
    const cmp = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
    return sortAsc ? cmp : -cmp;
  });

  // ─── Route Badge ────────────────────────────────────────────────────────────

  const getRouteBadge = (route) => {
    const routeMap = {
      'fast-track': { label: 'Fast Track', color: 'green' },
      standard: { label: 'Standard', color: 'amber' },
      'senior-review': { label: 'Senior Review', color: 'red' },
    };
    const config = routeMap[route] || { label: route || '—', color: 'gray' };
    return <StatusBadge status={config.label} colorOverride={config.color} />;
  };

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            AICTE Application Verification System
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Officer Dashboard — Review and process institution applications
          </p>
        </div>
        <button
          onClick={fetchApplications}
          className="btn-outline"
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <ScoreCard
          label="Total Applications"
          value={stats.total}
          color="blue"
          icon={BarChart3}
        />
        <ScoreCard
          label="Pending Review"
          value={stats.pending}
          color="amber"
          icon={Clock}
        />
        <ScoreCard
          label="Fast-Track"
          value={stats.fastTrack}
          color="green"
          icon={Zap}
        />
        <ScoreCard
          label="Flagged"
          value={stats.flagged}
          color="red"
          icon={AlertTriangle}
        />
      </div>

      {/* Error State */}
      {error && (
        <div className="bg-danger-50 border border-danger-200 text-danger-700 px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-5 h-5 flex-shrink-0" />
          <p className="text-sm">{error}</p>
        </div>
      )}

      {/* Application Queue Table */}
      <div className="card p-0 overflow-hidden">
        <div className="px-4 py-3 border-b border-gray-200 bg-gray-50">
          <h2 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
            <FileSearch className="w-4 h-4" />
            Application Queue
            <span className="text-gray-400 font-normal">({applications.length})</span>
          </h2>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-16">
            <div className="spinner w-8 h-8" />
            <span className="ml-3 text-sm text-gray-500">Loading applications...</span>
          </div>
        ) : applications.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-16 text-gray-400">
            <FileSearch className="w-12 h-12 mb-3 opacity-50" />
            <p className="text-sm font-medium">No applications found</p>
            <p className="text-xs mt-1">Applications will appear here once submitted</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Institution</th>
                  <th>Status</th>
                  <th
                    className="cursor-pointer select-none hover:bg-primary-800"
                    onClick={() => handleSort('trust_score')}
                  >
                    <span className="flex items-center gap-1">
                      Trust Score
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th
                    className="cursor-pointer select-none hover:bg-primary-800"
                    onClick={() => handleSort('compliance_score')}
                  >
                    <span className="flex items-center gap-1">
                      Compliance
                      <ArrowUpDown className="w-3 h-3" />
                    </span>
                  </th>
                  <th>Route</th>
                  <th>Date</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {sortedApplications.map((app) => (
                  <tr
                    key={app.id}
                    onClick={() => navigate(`/application/${app.id}`)}
                    className="group"
                  >
                    <td className="font-mono text-xs text-gray-500">
                      #{app.id || '—'}
                    </td>
                    <td className="font-medium text-gray-900 max-w-[200px] truncate">
                      {app.institution_name || '—'}
                    </td>
                    <td>
                      <StatusBadge status={app.status} />
                    </td>
                    <td>
                      <span className={`font-semibold ${
                        (app.trust_score ?? 0) >= 70 ? 'text-success-600' :
                        (app.trust_score ?? 0) >= 40 ? 'text-warning-600' :
                        'text-danger-600'
                      }`}>
                        {app.trust_score != null ? `${app.trust_score.toFixed(1)}%` : '—'}
                      </span>
                    </td>
                    <td>
                      <span className={`font-semibold ${
                        (app.compliance_score ?? 0) >= 70 ? 'text-success-600' :
                        (app.compliance_score ?? 0) >= 40 ? 'text-warning-600' :
                        'text-danger-600'
                      }`}>
                        {app.compliance_score != null ? `${app.compliance_score.toFixed(1)}%` : '—'}
                      </span>
                    </td>
                    <td>{getRouteBadge(app.route)}</td>
                    <td className="text-xs text-gray-500">
                      {app.application_date
                        ? new Date(app.application_date).toLocaleDateString()
                        : '—'}
                    </td>
                    <td>
                      <button
                        className="text-primary-600 hover:text-primary-800 transition-colors
                                   flex items-center gap-1 text-xs font-medium"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/application/${app.id}`);
                        }}
                      >
                        Review
                        <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
