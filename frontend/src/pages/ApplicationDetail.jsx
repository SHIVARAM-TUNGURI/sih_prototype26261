import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Shield, ClipboardCheck, AlertTriangle, CheckCircle,
  XCircle, Clock, FileText, Eye, Hash, Loader2, ChevronDown, ChevronUp
} from 'lucide-react';
import { getApplicationReport, verifyDocumentHash, getAuditLog, submitDecision } from '../api';

const TABS = ['Overview', 'Documents', 'Cross-Verification', 'Compliance', 'Audit Log'];

/* ── small helpers ─────────────────────────────────────────────── */
const routeStyle = (r) => ({
  'fast-track':     'bg-green-100 text-green-800 border-green-300',
  'standard':       'bg-amber-100 text-amber-800 border-amber-300',
  'senior-review':  'bg-red-100   text-red-800   border-red-300',
}[r] || 'bg-gray-100 text-gray-600 border-gray-300');

const severityDot = (s) => ({
  high:     'bg-red-500',
  critical: 'bg-red-600',
  medium:   'bg-amber-400',
  major:    'bg-amber-500',
  low:      'bg-blue-400',
  minor:    'bg-blue-300',
}[s?.toLowerCase()] || 'bg-gray-400');

const tamperColor = (score) => {
  if (score == null) return 'text-gray-400';
  if (score > 0.4)   return 'text-red-600';
  if (score > 0.2)   return 'text-amber-500';
  return 'text-green-600';
};

const tamperLabel = (score) => {
  if (score == null) return 'N/A';
  if (score > 0.4)   return `${(score * 100).toFixed(0)}% – HIGH RISK`;
  if (score > 0.2)   return `${(score * 100).toFixed(0)}% – MODERATE`;
  return `${(score * 100).toFixed(0)}% – CLEAN`;
};

/* ─────────────────────────────────────────────────────────────── */

export default function ApplicationDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [report, setReport] = useState(null);
  const [auditLog, setAuditLog] = useState([]);
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Modal states
  const [heatmapDoc, setHeatmapDoc] = useState(null);
  const [decisionAction, setDecisionAction] = useState(null); // 'approve'|'reject'|'raise_deficiency'

  // Hash verify state per document
  const [hashResults, setHashResults] = useState({});
  const [hashLoading, setHashLoading] = useState({});

  // Expanded rule/finding rows
  const [expandedRule, setExpandedRule] = useState(null);

  const fetchReport = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [rep, log] = await Promise.all([
        getApplicationReport(id),
        getAuditLog(id),
      ]);
      setReport(rep);
      setAuditLog(log);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Failed to load report');
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => { fetchReport(); }, [fetchReport]);

  const handleVerifyHash = async (docId) => {
    setHashLoading(h => ({ ...h, [docId]: true }));
    try {
      const result = await verifyDocumentHash(docId);
      setHashResults(r => ({ ...r, [docId]: result }));
    } catch (e) {
      setHashResults(r => ({ ...r, [docId]: { status: 'error', error: e.message } }));
    } finally {
      setHashLoading(h => ({ ...h, [docId]: false }));
    }
  };

  const handleDecisionSubmit = async (action, officerId, remarks) => {
    await submitDecision(id, { action, officer_id: officerId, remarks });
    setDecisionAction(null);
    fetchReport();
  };

  /* ── Loading / error states ─────────────────────────────────── */
  if (loading) return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="flex items-center justify-center h-64">
        <Loader2 size={32} className="animate-spin text-blue-500" />
        <span className="ml-3 text-gray-500">Loading application report…</span>
      </div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />
      <div className="max-w-4xl mx-auto px-4 py-12 text-center">
        <AlertTriangle size={40} className="text-red-400 mx-auto mb-3" />
        <p className="text-red-600 font-medium">{error}</p>
        <button onClick={() => navigate('/')} className="mt-4 text-blue-600 hover:underline text-sm">← Back to Dashboard</button>
      </div>
    </div>
  );

  const { application, documents, findings, rule_results, score_breakdown } = report;

  const statusColor = {
    approved:   'bg-green-100 text-green-700',
    rejected:   'bg-red-100 text-red-700',
    deficiency: 'bg-amber-100 text-amber-700',
    processed:  'bg-blue-100 text-blue-700',
    processing: 'bg-indigo-100 text-indigo-700',
    submitted:  'bg-gray-100 text-gray-600',
  }[application.status] || 'bg-gray-100 text-gray-600';

  return (
    <div className="min-h-screen bg-gray-50">
      <Navbar />

      {/* ── Header ── */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <button onClick={() => navigate('/')} className="flex items-center gap-1 text-sm text-gray-500 hover:text-blue-600 mb-3">
            <ArrowLeft size={16} /> Back to Dashboard
          </button>
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-xl font-bold text-gray-900">{application.institution_name}</h1>
              <p className="text-sm text-gray-500">{application.application_type} · App #{application.id}</p>
            </div>
            <div className="flex items-center gap-3 flex-wrap">
              <span className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${statusColor}`}>
                {application.status}
              </span>
              {application.route && (
                <span className={`px-3 py-1 rounded-full border text-xs font-semibold capitalize ${routeStyle(application.route)}`}>
                  {application.route}
                </span>
              )}
            </div>
          </div>

          {/* Score cards */}
          {score_breakdown && (
            <div className="grid grid-cols-3 gap-4 mt-4">
              <ScoreCard label="Trust Score" value={score_breakdown.trust_score} icon={<Shield size={20}/>}
                thresholds={{ good: 80, warn: 50 }} suffix="/100" />
              <ScoreCard label="Compliance Score" value={score_breakdown.compliance_score} icon={<ClipboardCheck size={20}/>}
                thresholds={{ good: 80, warn: 50 }} suffix="/100" />
              <div className={`rounded-xl p-4 border ${routeStyle(score_breakdown.route)}`}>
                <p className="text-xs font-semibold uppercase tracking-wide mb-1 opacity-70">Review Route</p>
                <p className="text-lg font-bold capitalize">{score_breakdown.route?.replace('-', ' ') || '—'}</p>
                <p className="text-xs mt-1 opacity-60">
                  {score_breakdown.route === 'fast-track' ? 'Score ≥ 80 — expedited review' :
                   score_breakdown.route === 'standard' ? 'Score 50–79 — standard review' :
                   'Score < 50 — senior review / physical inspection'}
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex gap-0 overflow-x-auto">
            {TABS.map((tab, i) => (
              <button
                key={tab}
                onClick={() => setActiveTab(i)}
                className={`px-5 py-3 text-sm font-medium border-b-2 whitespace-nowrap transition-colors
                  ${activeTab === i
                    ? 'border-blue-600 text-blue-700'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'}`}
              >
                {tab}
                {tab === 'Cross-Verification' && findings.length > 0 &&
                  <span className="ml-2 bg-red-100 text-red-600 text-xs font-bold px-1.5 py-0.5 rounded-full">{findings.length}</span>}
                {tab === 'Compliance' && rule_results.filter(r => r.status !== 'compliant').length > 0 &&
                  <span className="ml-2 bg-amber-100 text-amber-700 text-xs font-bold px-1.5 py-0.5 rounded-full">
                    {rule_results.filter(r => r.status !== 'compliant').length}
                  </span>}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tab Content ── */}
      <div className="max-w-6xl mx-auto px-4 py-6">

        {/* ── Overview ── */}
        {activeTab === 0 && (
          <div className="bg-white rounded-xl border border-gray-200 p-6 shadow-sm">
            <h2 className="text-base font-semibold text-gray-800 mb-4">Application Details</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-x-8 gap-y-3">
              {[
                ['Institution', application.institution_name],
                ['Trust / Society', application.trust_name],
                ['Address', application.address],
                ['PIN Code', application.pin_code],
                ['Land Area', `${application.land_area_acres} acres`],
                ['Proposed Courses', application.proposed_courses],
                ['Total Intake', application.total_intake],
                ['Faculty Count', application.faculty_count],
                ['Application Date', application.application_date],
                ['Submitted', new Date(application.created_at).toLocaleString()],
              ].map(([label, value]) => (
                <div key={label} className="flex gap-2">
                  <dt className="text-sm text-gray-500 w-36 shrink-0">{label}</dt>
                  <dd className="text-sm text-gray-800 font-medium">{value || '—'}</dd>
                </div>
              ))}
            </dl>
          </div>
        )}

        {/* ── Documents ── */}
        {activeTab === 1 && (
          <div className="space-y-4">
            {documents.length === 0 && (
              <div className="bg-white rounded-xl border border-gray-200 p-8 text-center text-gray-400">
                No documents uploaded yet.
              </div>
            )}
            {documents.map(doc => {
              const hashRes = hashResults[doc.id];
              return (
                <div key={doc.id} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
                  <div className="flex flex-wrap items-start justify-between gap-3 mb-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <FileText size={16} className="text-blue-500" />
                        <span className="font-medium text-gray-800">{doc.original_filename}</span>
                        {doc.doc_type && (
                          <span className="bg-blue-50 text-blue-700 text-xs font-semibold px-2 py-0.5 rounded-full capitalize">
                            {doc.doc_type.replace('_', ' ')}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-1 font-mono">{doc.file_hash?.substring(0, 16)}…</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {/* Tamper score */}
                      {doc.tamper_score != null && (
                        <span className={`text-sm font-semibold ${tamperColor(doc.tamper_score)}`}>
                          ⚠ {tamperLabel(doc.tamper_score)}
                        </span>
                      )}
                      {/* Heatmap button */}
                      {doc.heatmap_path && (
                        <button
                          onClick={() => setHeatmapDoc(doc)}
                          className="flex items-center gap-1 text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-1.5 rounded-lg hover:bg-purple-100"
                        >
                          <Eye size={13} /> View Heatmap
                        </button>
                      )}
                      {/* Hash verify */}
                      <button
                        onClick={() => handleVerifyHash(doc.id)}
                        disabled={hashLoading[doc.id]}
                        className="flex items-center gap-1 text-xs bg-gray-50 text-gray-700 border border-gray-200 px-2.5 py-1.5 rounded-lg hover:bg-gray-100 disabled:opacity-60"
                      >
                        {hashLoading[doc.id] ? <Loader2 size={13} className="animate-spin"/> : <Hash size={13}/>}
                        Verify Integrity
                      </button>
                    </div>
                  </div>

                  {/* Hash verify result */}
                  {hashRes && (
                    <div className={`text-xs p-2 rounded-lg mb-3 font-medium flex items-center gap-2
                      ${hashRes.status === 'verified' ? 'bg-green-50 text-green-700' :
                        hashRes.status === 'altered'  ? 'bg-red-50 text-red-700' :
                        'bg-gray-50 text-gray-600'}`}>
                      {hashRes.status === 'verified' ? <CheckCircle size={14}/> :
                       hashRes.status === 'altered'  ? <XCircle size={14}/> :
                       <AlertTriangle size={14}/>}
                      {hashRes.status === 'verified' ? 'Integrity verified — file unchanged since upload' :
                       hashRes.status === 'altered'  ? 'INTEGRITY ALERT — file has been altered after upload' :
                       `Error: ${hashRes.error}`}
                    </div>
                  )}

                  {/* Extracted fields */}
                  {doc.fields_json && Object.keys(doc.fields_json).length > 0 && (
                    <div>
                      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Extracted Fields</p>
                      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                        {Object.entries(doc.fields_json).map(([field, val]) => {
                          const value = typeof val === 'object' ? val?.value : val;
                          const conf = typeof val === 'object' ? val?.confidence : null;
                          if (field === 'faculty_members') return null;
                          return (
                            <div key={field} className="bg-gray-50 rounded-lg p-2.5">
                              <p className="text-xs text-gray-400 capitalize">{field.replace(/_/g, ' ')}</p>
                              <p className="text-sm font-medium text-gray-800 truncate">{String(value ?? '—')}</p>
                              {conf != null && (
                                <div className="mt-1 h-1 bg-gray-200 rounded-full overflow-hidden">
                                  <div className="h-1 bg-blue-400 rounded-full" style={{ width: `${(conf * 100).toFixed(0)}%` }} />
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                      {/* Faculty table */}
                      {doc.fields_json.faculty_members && (
                        <div className="mt-3">
                          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">Faculty Members</p>
                          <div className="overflow-x-auto rounded-lg border border-gray-100">
                            <table className="min-w-full text-xs">
                              <thead className="bg-gray-50">
                                <tr>{['ID','Name','Qualification','Designation'].map(h => (
                                  <th key={h} className="px-3 py-2 text-left font-semibold text-gray-500">{h}</th>
                                ))}</tr>
                              </thead>
                              <tbody className="divide-y divide-gray-100">
                                {(doc.fields_json.faculty_members?.value || []).map((m, i) => (
                                  <tr key={i} className="hover:bg-gray-50">
                                    <td className="px-3 py-2 font-mono text-gray-500">{m.faculty_id}</td>
                                    <td className="px-3 py-2 text-gray-800">{m.name}</td>
                                    <td className="px-3 py-2 text-gray-600">{m.qualification}</td>
                                    <td className="px-3 py-2 text-gray-600">{m.designation}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* ── Cross-Verification ── */}
        {activeTab === 2 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-800">Cross-Verification Findings</h2>
              <p className="text-xs text-gray-500 mt-0.5">Compares data across documents and mock government registry</p>
            </div>
            {findings.length === 0 ? (
              <div className="p-8 text-center">
                <CheckCircle size={32} className="text-green-400 mx-auto mb-2" />
                <p className="text-green-700 font-medium">No issues found — all cross-checks passed</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100">
                {findings.map((f) => (
                  <div key={f.id} className="p-4 flex gap-3">
                    <div className={`mt-1.5 w-2.5 h-2.5 rounded-full shrink-0 ${severityDot(f.severity)}`} />
                    <div className="flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <StatusBadge status={f.category} />
                        <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full
                          ${f.severity === 'high' ? 'bg-red-100 text-red-700' :
                            f.severity === 'medium' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                          {f.severity?.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-800 mt-1">{f.description}</p>
                      {f.evidence && (
                        <details className="mt-2">
                          <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600">Show evidence</summary>
                          <pre className="text-xs bg-gray-50 rounded p-2 mt-1 overflow-x-auto text-gray-600">
                            {JSON.stringify(f.evidence, null, 2)}
                          </pre>
                        </details>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Compliance ── */}
        {activeTab === 3 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
            <div className="p-4 border-b border-gray-100">
              <h2 className="font-semibold text-gray-800">Regulatory Compliance — Rule Evaluation</h2>
              <p className="text-xs text-gray-500 mt-0.5">AICTE Approval Process Handbook (sample clauses — thresholds are representative placeholders)</p>
            </div>
            <div className="divide-y divide-gray-100">
              {rule_results.map((r) => (
                <div key={r.id} className="p-4">
                  <div
                    className="flex items-start justify-between cursor-pointer"
                    onClick={() => setExpandedRule(expandedRule === r.id ? null : r.id)}
                  >
                    <div className="flex items-start gap-3 flex-1">
                      <div className={`mt-1 shrink-0 ${severityDot(r.severity)} w-2.5 h-2.5 rounded-full`} />
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="text-xs font-mono font-bold text-gray-500">{r.rule_id}</span>
                          <StatusBadge status={r.status} />
                          <span className={`text-xs font-semibold px-1.5 py-0.5 rounded-full
                            ${r.severity === 'critical' ? 'bg-red-100 text-red-700' :
                              r.severity === 'major' ? 'bg-amber-100 text-amber-700' : 'bg-blue-100 text-blue-700'}`}>
                            {r.severity?.toUpperCase()}
                          </span>
                        </div>
                        <p className="text-sm text-gray-800 mt-1">{r.rule_description}</p>
                        {r.clause_reference && (
                          <p className="text-xs text-blue-600 mt-0.5">📄 {r.clause_reference}</p>
                        )}
                      </div>
                    </div>
                    {expandedRule === r.id ? <ChevronUp size={16} className="text-gray-400 shrink-0 mt-1"/> : <ChevronDown size={16} className="text-gray-400 shrink-0 mt-1"/>}
                  </div>
                  {expandedRule === r.id && (
                    <div className="mt-3 ml-6 space-y-2">
                      {r.clause_text && (
                        <div className="bg-blue-50 border-l-4 border-blue-300 p-3 rounded-r-lg">
                          <p className="text-xs font-semibold text-blue-700 mb-1">Clause Text</p>
                          <p className="text-xs text-blue-800 leading-relaxed">{r.clause_text}</p>
                        </div>
                      )}
                      {r.evidence && (
                        <div>
                          <p className="text-xs font-semibold text-gray-500 mb-1">Evidence</p>
                          <pre className="text-xs bg-gray-50 rounded p-2 overflow-x-auto text-gray-600 border border-gray-100">
                            {JSON.stringify(r.evidence, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Audit Log ── */}
        {activeTab === 4 && (
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Audit Trail</h2>
            {auditLog.length === 0 ? (
              <p className="text-gray-400 text-sm text-center py-6">No actions recorded yet.</p>
            ) : (
              <ol className="relative border-l-2 border-gray-200 ml-4 space-y-6">
                {auditLog.map((entry) => (
                  <li key={entry.id} className="ml-5">
                    <div className="absolute -left-2.5 w-5 h-5 rounded-full border-2 border-blue-300 bg-white flex items-center justify-center">
                      <Clock size={10} className="text-blue-500" />
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3 border border-gray-100">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full capitalize
                          ${entry.action === 'approve' ? 'bg-green-100 text-green-700' :
                            entry.action === 'reject' ? 'bg-red-100 text-red-700' :
                            entry.action === 'raise_deficiency' ? 'bg-amber-100 text-amber-700' :
                            'bg-blue-100 text-blue-700'}`}>
                          {entry.action?.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-gray-500">by <strong>{entry.actor}</strong></span>
                      </div>
                      {entry.details && entry.details.length < 200 && (
                        <p className="text-xs text-gray-600">{entry.details}</p>
                      )}
                      {entry.details && entry.details.length >= 200 && (
                        <details><summary className="text-xs text-gray-400 cursor-pointer">View details</summary>
                          <pre className="text-xs text-gray-600 mt-1 whitespace-pre-wrap">{entry.details}</pre>
                        </details>
                      )}
                      <p className="text-xs text-gray-400 mt-1">{new Date(entry.timestamp).toLocaleString()}</p>
                    </div>
                  </li>
                ))}
              </ol>
            )}
          </div>
        )}
      </div>

      {/* ── Officer Action Bar (only show if processed) ── */}
      {['processed', 'submitted'].includes(application.status) && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 shadow-lg z-10">
          <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
            <p className="text-sm text-gray-600 font-medium">Officer Decision</p>
            <div className="flex gap-3">
              <button
                onClick={() => setDecisionAction('raise_deficiency')}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-amber-50 text-amber-700 border border-amber-300 hover:bg-amber-100"
              >
                ⚠ Raise Deficiency
              </button>
              <button
                onClick={() => setDecisionAction('reject')}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-red-50 text-red-700 border border-red-300 hover:bg-red-100"
              >
                ✕ Reject
              </button>
              <button
                onClick={() => setDecisionAction('approve')}
                className="px-4 py-2 text-sm font-semibold rounded-lg bg-green-600 text-white hover:bg-green-700"
              >
                ✓ Approve
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Modals ── */}
      {heatmapDoc && (
        <HeatmapModal
          documentId={heatmapDoc.id}
          filename={heatmapDoc.original_filename}
          onClose={() => setHeatmapDoc(null)}
        />
      )}
      {decisionAction && (
        <DecisionModal
          action={decisionAction}
          findings={findings}
          onSubmit={handleDecisionSubmit}
          onClose={() => setDecisionAction(null)}
        />
      )}
    </div>
  );
}
