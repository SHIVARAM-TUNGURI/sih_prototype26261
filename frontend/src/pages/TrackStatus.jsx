import { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { Search, Loader2, CheckCircle, Clock, AlertCircle, XCircle, FileText } from 'lucide-react';
import { getApplicationStatus } from '../api';

/**
 * Applicant-facing "Track Application Status" page.
 * Shows only the stage of the application and any message from the officer.
 * It never shows trust/compliance scores, findings, or routing.
 */

const STAGES = ['Submitted', 'Under Review', 'Decision'];

// Which stage index is "current" for each status code
const STAGE_INDEX = {
  under_review: 1,
  query_raised: 2,
  approved: 2,
  rejected: 2,
};

const STATUS_STYLE = {
  under_review: { box: 'bg-blue-50 border-blue-200 text-blue-800', Icon: Clock, iconColor: 'text-blue-600' },
  query_raised: { box: 'bg-amber-50 border-amber-200 text-amber-800', Icon: AlertCircle, iconColor: 'text-amber-600' },
  approved: { box: 'bg-green-50 border-green-200 text-green-800', Icon: CheckCircle, iconColor: 'text-green-600' },
  rejected: { box: 'bg-red-50 border-red-200 text-red-800', Icon: XCircle, iconColor: 'text-red-600' },
};

function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso.endsWith('Z') ? iso : iso + 'Z');
  if (Number.isNaN(d.getTime())) return '—';
  return d.toLocaleString(undefined, { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export default function TrackStatus() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [refNo, setRefNo] = useState(searchParams.get('id') || '');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const lookup = async (idValue) => {
    const cleaned = String(idValue).replace('#', '').trim();
    if (!/^\d+$/.test(cleaned)) {
      setError('Please enter a valid reference number (digits only, e.g. 9).');
      setResult(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await getApplicationStatus(cleaned);
      setResult(data);
      setSearchParams({ id: cleaned });
    } catch (e) {
      setResult(null);
      if (e.response?.status === 404) {
        setError('No application found with that reference number. Please check the number and try again.');
      } else {
        setError('Could not fetch the status right now. Please try again in a moment.');
      }
    } finally {
      setLoading(false);
    }
  };

  // Auto-load when arriving with ?id=9 (e.g. from the confirmation screen)
  useEffect(() => {
    const idFromUrl = searchParams.get('id');
    if (idFromUrl) lookup(idFromUrl);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    lookup(refNo);
  };

  const style = result ? STATUS_STYLE[result.status_code] || STATUS_STYLE.under_review : null;
  const currentStage = result ? STAGE_INDEX[result.status_code] ?? 1 : 0;

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Track Application Status</h1>
        <p className="text-gray-500 mt-1">Enter the reference number you received when you submitted your application.</p>
      </div>

      {/* Lookup form */}
      <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 mb-6">
        <label htmlFor="refNo" className="block text-sm font-medium text-gray-700 mb-2">Reference number</label>
        <div className="flex gap-3">
          <input
            id="refNo"
            type="text"
            inputMode="numeric"
            value={refNo}
            onChange={(e) => setRefNo(e.target.value)}
            placeholder="e.g. 9"
            className="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading}
            className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-semibold text-sm hover:bg-blue-700 disabled:opacity-60"
          >
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Search size={16} />}
            {loading ? 'Checking…' : 'Track'}
          </button>
        </div>
        {error && (
          <p className="mt-3 text-sm text-red-600 flex items-center gap-2">
            <AlertCircle size={16} className="flex-shrink-0" /> {error}
          </p>
        )}
      </form>

      {/* Result */}
      {result && style && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-start justify-between flex-wrap gap-2 mb-6">
            <div>
              <p className="text-xs text-gray-400 uppercase tracking-wide">Application #{result.application_id}</p>
              <h2 className="text-lg font-semibold text-gray-900">{result.institution_name}</h2>
              <p className="text-sm text-gray-500 flex items-center gap-1 mt-0.5">
                <FileText size={14} /> {result.application_type}
              </p>
            </div>
            <div className="text-right text-xs text-gray-500">
              <p>Submitted: {formatDate(result.submitted_on)}</p>
              <p>Last updated: {formatDate(result.last_updated)}</p>
            </div>
          </div>

          {/* Progress */}
          <div className="flex items-center mb-6">
            {STAGES.map((label, i) => {
              const done = i < currentStage;
              const current = i === currentStage;
              return (
                <div key={label} className="flex items-center flex-1 last:flex-none">
                  <div className="flex items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold
                        ${done ? 'bg-green-500 text-white' : current ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}
                    >
                      {done ? <CheckCircle size={16} /> : i + 1}
                    </div>
                    <span className={`ml-2 text-sm font-medium ${current ? 'text-blue-700' : 'text-gray-500'}`}>{label}</span>
                  </div>
                  {i < STAGES.length - 1 && (
                    <div className={`flex-1 h-0.5 mx-3 ${i < currentStage ? 'bg-green-400' : 'bg-gray-200'}`} />
                  )}
                </div>
              );
            })}
          </div>

          {/* Status box */}
          <div className={`border rounded-lg p-4 ${style.box}`}>
            <div className="flex items-center gap-2 mb-1">
              <style.Icon size={20} className={style.iconColor} />
              <p className="font-semibold">{result.status_label}</p>
            </div>
            <p className="text-sm">{result.message}</p>
          </div>

          {/* Officer message */}
          {result.officer_message && (
            <div className="mt-4 border border-gray-200 rounded-lg p-4 bg-gray-50">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Message from AICTE</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.officer_message}</p>
            </div>
          )}
        </div>
      )}

      <div className="text-center mt-6">
        <Link to="/apply" className="text-sm text-blue-600 hover:text-blue-800">← Back to Application Portal</Link>
      </div>
    </div>
  );
}
