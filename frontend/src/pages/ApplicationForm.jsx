import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Upload, FileText, CheckCircle, AlertCircle, Loader2, X } from 'lucide-react';
import { createApplication, uploadDocuments, processApplication } from '../api';

const REQUIRED_DOCS = [
  { key: 'land_deed', label: 'Land Deed / Conveyance Deed', accept: '.png,.jpg,.jpeg,.pdf' },
  { key: 'trust_certificate', label: 'Trust / Society Registration Certificate', accept: '.png,.jpg,.jpeg,.pdf' },
  { key: 'noc', label: 'No Objection Certificate (NOC)', accept: '.png,.jpg,.jpeg,.pdf' },
  { key: 'faculty_list', label: 'Faculty List', accept: '.png,.jpg,.jpeg,.pdf' },
];

const FIELD_CONFIGS = [
  { name: 'institution_name', label: 'Institution Name', type: 'text', placeholder: 'e.g. Vidya Bharati Institute of Technology' },
  { name: 'trust_name', label: 'Trust / Society Name', type: 'text', placeholder: 'e.g. Vidya Bharati Educational Trust' },
  { name: 'address', label: 'Address', type: 'text', placeholder: 'Full address including city and state' },
  { name: 'pin_code', label: 'PIN Code', type: 'text', placeholder: '6-digit PIN', maxLength: 6 },
  { name: 'land_area_acres', label: 'Land Area (acres)', type: 'number', placeholder: 'e.g. 5.0', step: '0.1', min: '0' },
  { name: 'proposed_courses', label: 'Proposed Courses', type: 'text', placeholder: 'e.g. Computer Science, Electronics, Mechanical' },
  { name: 'total_intake', label: 'Total Intake (students/year)', type: 'number', placeholder: 'e.g. 180', min: '1' },
  { name: 'faculty_count', label: 'Faculty Count', type: 'number', placeholder: 'e.g. 12', min: '1' },
  { name: 'application_date', label: 'Application Date', type: 'date' },
];

const STEPS = ['Application Form', 'Upload Documents', 'Submit & Process'];

export default function ApplicationForm() {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [formData, setFormData] = useState({});
  const [formErrors, setFormErrors] = useState({});
  const [files, setFiles] = useState({});  // { doc_key: File }
  const [dragOver, setDragOver] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [createdAppId, setCreatedAppId] = useState(null);
  const [processResult, setProcessResult] = useState(null);
  const [error, setError] = useState(null);

  /* ── Form validation ── */
  const validateForm = () => {
    const errors = {};
    if (!formData.institution_name?.trim()) errors.institution_name = 'Required';
    if (!formData.trust_name?.trim()) errors.trust_name = 'Required';
    if (!formData.address?.trim()) errors.address = 'Required';
    if (!/^\d{6}$/.test(formData.pin_code || '')) errors.pin_code = 'Must be 6 digits';
    if (!formData.land_area_acres || parseFloat(formData.land_area_acres) <= 0) errors.land_area_acres = 'Must be > 0';
    if (!formData.proposed_courses?.trim()) errors.proposed_courses = 'Required';
    if (!formData.total_intake || parseInt(formData.total_intake) <= 0) errors.total_intake = 'Must be > 0';
    if (!formData.faculty_count || parseInt(formData.faculty_count) <= 0) errors.faculty_count = 'Must be > 0';
    if (!formData.application_date) errors.application_date = 'Required';
    else if (new Date(formData.application_date) > new Date()) errors.application_date = 'Cannot be in the future';
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  /* ── Step 1: submit form → create application ── */
  const handleFormNext = async () => {
    if (!validateForm()) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        ...formData,
        land_area_acres: parseFloat(formData.land_area_acres),
        total_intake: parseInt(formData.total_intake),
        faculty_count: parseInt(formData.faculty_count),
      };
      const app = await createApplication(payload);
      setCreatedAppId(app.id);
      setStep(1);
    } catch (e) {
      setError(e.response?.data?.detail?.message || e.message || 'Failed to create application');
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Step 2: upload documents ── */
  const handleFileDrop = (docKey, e) => {
    e.preventDefault();
    setDragOver(null);
    const file = e.dataTransfer?.files?.[0] || e.target?.files?.[0];
    if (file) setFiles(f => ({ ...f, [docKey]: file }));
  };

  const missingDocs = REQUIRED_DOCS.filter(d => !files[d.key]);

  const handleUploadNext = async () => {
    if (missingDocs.length > 0) {
      setError(`Please upload all required documents. Missing: ${missingDocs.map(d => d.label).join(', ')}`);
      return;
    }
    setSubmitting(true);
    setError(null);
    try {
      const fileList = Object.values(files);
      await uploadDocuments(createdAppId, fileList);
      setStep(2);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Upload failed');
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Step 3: process ── */
  const handleProcess = async () => {
    setSubmitting(true);
    setError(null);
    try {
      const result = await processApplication(createdAppId);
      setProcessResult(result);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || 'Processing failed');
    } finally {
      setSubmitting(false);
    }
  };

  /* ── UI helpers ── */
  const routeColor = (r) => ({
    'fast-track': 'bg-green-100 text-green-800',
    'standard': 'bg-amber-100 text-amber-800',
    'senior-review': 'bg-red-100 text-red-800',
  }[r] || 'bg-gray-100 text-gray-700');

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">New Engineering Institution Approval</h1>
          <p className="text-gray-500 mt-1">AICTE Application Submission Portal</p>
        </div>

        {/* Stepper */}
        <div className="flex items-center mb-8">
          {STEPS.map((s, i) => (
            <div key={i} className="flex items-center flex-1 last:flex-none">
              <div className={`flex items-center justify-center w-8 h-8 rounded-full text-sm font-semibold
                ${i < step ? 'bg-green-500 text-white' : i === step ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}`}>
                {i < step ? <CheckCircle size={16} /> : i + 1}
              </div>
              <span className={`ml-2 text-sm font-medium ${i === step ? 'text-blue-700' : 'text-gray-500'}`}>{s}</span>
              {i < STEPS.length - 1 && <div className={`flex-1 h-0.5 mx-3 ${i < step ? 'bg-green-400' : 'bg-gray-200'}`} />}
            </div>
          ))}
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2">
            <AlertCircle size={18} className="text-red-500 mt-0.5 shrink-0" />
            <p className="text-red-700 text-sm">{error}</p>
            <button onClick={() => setError(null)} className="ml-auto text-red-400 hover:text-red-600"><X size={16}/></button>
          </div>
        )}

        {/* ─── STEP 0: Application Form ─── */}
        {step === 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-5">Application Details</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
              {FIELD_CONFIGS.map(({ name, label, type, placeholder, ...rest }) => (
                <div key={name} className={name === 'address' || name === 'proposed_courses' ? 'sm:col-span-2' : ''}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
                  <input
                    type={type}
                    placeholder={placeholder}
                    value={formData[name] || ''}
                    onChange={e => {
                      setFormData(d => ({ ...d, [name]: e.target.value }));
                      if (formErrors[name]) setFormErrors(er => ({ ...er, [name]: null }));
                    }}
                    className={`w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-blue-500 focus:outline-none
                      ${formErrors[name] ? 'border-red-400 bg-red-50' : 'border-gray-300'}`}
                    {...rest}
                  />
                  {formErrors[name] && <p className="text-red-500 text-xs mt-1">{formErrors[name]}</p>}
                </div>
              ))}
            </div>
            <div className="mt-6 flex justify-end">
              <button
                onClick={handleFormNext}
                disabled={submitting}
                className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? <Loader2 size={16} className="animate-spin" /> : null}
                {submitting ? 'Creating…' : 'Next: Upload Documents →'}
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 1: Upload Documents ─── */}
        {step === 1 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-800 mb-1">Upload Supporting Documents</h2>
            <p className="text-sm text-gray-500 mb-5">Application ID: <span className="font-mono font-semibold text-blue-700">#{createdAppId}</span> — All 4 documents are required.</p>

            <div className="space-y-4">
              {REQUIRED_DOCS.map(({ key, label }) => {
                const file = files[key];
                const isOver = dragOver === key;
                return (
                  <div key={key}>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {label} <span className="text-red-500">*</span>
                    </label>
                    <div
                      onDragOver={e => { e.preventDefault(); setDragOver(key); }}
                      onDragLeave={() => setDragOver(null)}
                      onDrop={e => handleFileDrop(key, e)}
                      onClick={() => document.getElementById(`file-${key}`).click()}
                      className={`relative border-2 border-dashed rounded-lg p-4 cursor-pointer transition-colors
                        ${isOver ? 'border-blue-400 bg-blue-50' : file ? 'border-green-400 bg-green-50' : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'}`}
                    >
                      <input
                        id={`file-${key}`}
                        type="file"
                        className="hidden"
                        accept=".png,.jpg,.jpeg,.pdf"
                        onChange={e => handleFileDrop(key, e)}
                      />
                      <div className="flex items-center gap-3">
                        {file
                          ? <CheckCircle size={20} className="text-green-500 shrink-0" />
                          : <Upload size={20} className="text-gray-400 shrink-0" />}
                        <div className="flex-1 min-w-0">
                          {file
                            ? <p className="text-sm font-medium text-green-700 truncate">{file.name}</p>
                            : <p className="text-sm text-gray-500">Click or drag file here</p>}
                          {file && <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>}
                        </div>
                        {file && (
                          <button
                            onClick={e => { e.stopPropagation(); setFiles(f => { const n = {...f}; delete n[key]; return n; }); }}
                            className="text-gray-400 hover:text-red-500"
                          >
                            <X size={16} />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 flex justify-between">
              <button onClick={() => setStep(0)} className="text-gray-500 hover:text-gray-700 text-sm">← Back</button>
              <button
                onClick={handleUploadNext}
                disabled={submitting}
                className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-60"
              >
                {submitting ? <Loader2 size={16} className="animate-spin" /> : null}
                {submitting ? 'Uploading…' : `Upload & Continue (${Object.keys(files).length}/4) →`}
              </button>
            </div>
          </div>
        )}

        {/* ─── STEP 2: Submit & Process ─── */}
        {step === 2 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 text-center">
            {!processResult ? (
              <>
                <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FileText size={28} className="text-blue-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-2">Ready to Process</h2>
                <p className="text-gray-500 mb-2">Application <span className="font-mono font-bold text-blue-700">#{createdAppId}</span> and all documents uploaded successfully.</p>
                <p className="text-sm text-gray-400 mb-6">Click below to run the full AI pipeline: OCR, tamper detection, cross-verification, and compliance check.</p>
                <button
                  onClick={handleProcess}
                  disabled={submitting}
                  className="inline-flex items-center gap-2 bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold text-base hover:bg-blue-700 disabled:opacity-60"
                >
                  {submitting ? <Loader2 size={18} className="animate-spin" /> : null}
                  {submitting ? 'Running AI Pipeline…' : '⚡ Process Application'}
                </button>
              </>
            ) : (
              <>
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle size={28} className="text-green-600" />
                </div>
                <h2 className="text-xl font-semibold text-gray-900 mb-4">Processing Complete</h2>
                <div className="grid grid-cols-3 gap-4 max-w-sm mx-auto mb-6">
                  <div className="bg-blue-50 rounded-lg p-3">
                    <p className="text-xs text-blue-600 font-medium mb-1">Trust Score</p>
                    <p className="text-2xl font-bold text-blue-800">{processResult.trust_score ?? '—'}</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-3">
                    <p className="text-xs text-purple-600 font-medium mb-1">Compliance</p>
                    <p className="text-2xl font-bold text-purple-800">{processResult.compliance_score ?? '—'}</p>
                  </div>
                  <div className={`${routeColor(processResult.route)} rounded-lg p-3`}>
                    <p className="text-xs font-medium mb-1">Route</p>
                    <p className="text-sm font-bold capitalize">{processResult.route?.replace('-', ' ') ?? '—'}</p>
                  </div>
                </div>
                <p className="text-sm text-gray-500 mb-5">{processResult.findings_count} findings · {processResult.rule_results_count} rules checked</p>
                <button
                  onClick={() => navigate(`/application/${createdAppId}`)}
                  className="bg-blue-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-blue-700"
                >
                  View Full Report →
                </button>
              </>
            )}
          </div>
        )}

        {/* Disclaimer */}
        <p className="text-xs text-gray-400 text-center mt-6">
          ⚠ External government APIs (DigiLocker, MCA, land records) are simulated with a mock registry in this prototype.
        </p>
    </div>
  );
}
