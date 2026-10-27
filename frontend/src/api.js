import axios from 'axios';

/**
 * API client for the AICTE Smart Verification backend (FastAPI).
 * Base URL defaults to http://localhost:8000.
 * Set VITE_API_BASE_URL in .env to override.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Applications ────────────────────────────────────────────────────────────

/** Create a new application with institution form data. */
export async function createApplication(data) {
  const res = await api.post('/applications', data);
  return res.data;
}

/** List all applications (officer queue). Optional filters: status, route. */
export async function getApplications(params = {}) {
  const res = await api.get('/applications', { params });
  return res.data;
}

/** Get single application details. */
export async function getApplication(appId) {
  const res = await api.get(`/applications/${appId}`);
  return res.data;
}

/** Get the full verification report (scores, docs, findings, rules). */
export async function getApplicationReport(appId) {
  const res = await api.get(`/applications/${appId}/report`);
  return res.data;
}

/** Get the audit log for an application. */
export async function getAuditLog(appId) {
  const res = await api.get(`/applications/${appId}/audit-log`);
  return res.data;
}

// ─── Documents ───────────────────────────────────────────────────────────────

/** Upload documents (multipart/form-data). */
export async function uploadDocuments(appId, files) {
  const formData = new FormData();
  for (const file of files) formData.append('files', file);
  const res = await api.post(`/applications/${appId}/documents`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

/**
 * Get the ELA tamper heatmap image URL for a document.
 * Returns a URL that can be used directly in an <img> src.
 */
export function getHeatmapUrl(docId) {
  return `${API_BASE_URL}/documents/${docId}/heatmap`;
}

/** Verify SHA-256 integrity hash of a document. */
export async function verifyDocumentHash(docId) {
  const res = await api.get(`/documents/${docId}/verify-hash`);
  return res.data;
}

// ─── Processing & Decisions ──────────────────────────────────────────────────

/** Trigger the full AI processing pipeline for an application. */
export async function processApplication(appId) {
  const res = await api.post(`/applications/${appId}/process`);
  return res.data;
}

/**
 * Submit an officer decision.
 * @param {string|number} appId
 * @param {{ action: string, officer_id: string, remarks?: string }} decision
 */
export async function submitDecision(appId, decision) {
  const res = await api.post(`/applications/${appId}/decision`, decision);
  return res.data;
}

export default api;
