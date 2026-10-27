import { useState, useEffect } from 'react';
import { X, CheckCircle, XCircle, AlertTriangle, Send, Loader2 } from 'lucide-react';

/**
 * Officer decision modal for approve / reject / raise_deficiency actions.
 *
 * @param {string} action - 'approve' | 'reject' | 'raise_deficiency'
 * @param {Array}  findings - Finding objects from the report (used to auto-draft deficiency note)
 * @param {Function} onSubmit - async (action, officerId, remarks) => void
 * @param {Function} onClose - close callback
 */
export default function DecisionModal({ action, findings = [], onSubmit, onClose }) {
  const [officerId, setOfficerId] = useState('');
  const [remarks, setRemarks] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const configs = {
    approve: {
      title: 'Approve Application',
      desc: 'Confirm this application meets all AICTE requirements.',
      Icon: CheckCircle,
      headerCls: 'bg-green-50 border-green-200',
      iconCls: 'text-green-600',
      btnCls: 'bg-green-600 text-white hover:bg-green-700',
      btnLabel: 'Confirm Approval',
    },
    reject: {
      title: 'Reject Application',
      desc: 'Reject this application. This action is recorded in the audit log.',
      Icon: XCircle,
      headerCls: 'bg-red-50 border-red-200',
      iconCls: 'text-red-600',
      btnCls: 'bg-red-600 text-white hover:bg-red-700',
      btnLabel: 'Confirm Rejection',
    },
    raise_deficiency: {
      title: 'Raise Deficiency Notice',
      desc: 'Send a deficiency notice listing issues to the institution.',
      Icon: AlertTriangle,
      headerCls: 'bg-amber-50 border-amber-200',
      iconCls: 'text-amber-600',
      btnCls: 'bg-amber-500 text-white hover:bg-amber-600',
      btnLabel: 'Send Deficiency Notice',
    },
  };

  const cfg = configs[action] || configs.approve;
  const { Icon } = cfg;

  // Auto-generate deficiency note from findings
  useEffect(() => {
    if (action === 'raise_deficiency' && findings.length > 0) {
      const lines = ['DEFICIENCY NOTICE\n', 'The following issues were identified:\n'];
      findings.slice(0, 10).forEach((f, i) => {
        lines.push(`${i + 1}. [${(f.severity || '').toUpperCase()}] ${f.description}`);
      });
      if (findings.length > 10) lines.push(`… and ${findings.length - 10} more issues.`);
      lines.push('\nPlease address all items and resubmit the required documents.');
      setRemarks(lines.join('\n'));
    }
  }, [action, findings]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!officerId.trim()) { setError('Officer ID is required'); return; }
    setSubmitting(true);
    setError(null);
    try {
      await onSubmit(action, officerId.trim(), remarks.trim());
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Submission failed');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/60 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div
        className="bg-white rounded-xl shadow-2xl max-w-lg w-full"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className={`flex items-center gap-3 p-4 rounded-t-xl border-b ${cfg.headerCls}`}>
          <Icon size={22} className={cfg.iconCls} />
          <div>
            <h3 className="font-semibold text-gray-900">{cfg.title}</h3>
            <p className="text-xs text-gray-600">{cfg.desc}</p>
          </div>
          <button onClick={onClose} className="ml-auto p-1 hover:bg-black/10 rounded-lg">
            <X size={16} className="text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 space-y-4">
          {/* Officer ID */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Officer ID <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={officerId}
              onChange={e => { setOfficerId(e.target.value); setError(null); }}
              placeholder="e.g. AICTE/OFF/2026/042"
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
          </div>

          {/* Remarks */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {action === 'raise_deficiency' ? 'Deficiency Notice (auto-generated, editable)' : 'Remarks (optional)'}
            </label>
            <textarea
              value={remarks}
              onChange={e => setRemarks(e.target.value)}
              rows={action === 'raise_deficiency' ? 8 : 3}
              placeholder={action === 'raise_deficiency' ? 'Deficiency details…' : 'Add any remarks…'}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:outline-none resize-y"
            />
          </div>

          {error && <p className="text-red-500 text-xs">{error}</p>}

          <div className="flex items-center justify-end gap-3 pt-1">
            <button
              type="button"
              onClick={onClose}
              disabled={submitting}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !officerId.trim()}
              className={`inline-flex items-center gap-2 px-5 py-2 text-sm font-semibold rounded-lg disabled:opacity-60 ${cfg.btnCls}`}
            >
              {submitting ? <Loader2 size={15} className="animate-spin" /> : <Send size={15} />}
              {submitting ? 'Submitting…' : cfg.btnLabel}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
