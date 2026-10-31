import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Clock,
  ArrowLeft,
  Sparkles,
  ExternalLink,
  Download,
  Edit3,
  Check,
  RefreshCw,
  History
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';

interface AISummaryData {
  fdr_id: number;
  fdr_number: string;
  overall_confidence: number;
  recommendation: 'APPROVE' | 'REQUEST_CLARIFICATION' | 'REJECT';
  summary: string;
  flags: string[];
  is_ai_generated: boolean;
  engine: string;
}

interface AuditLogEntry {
  id: number;
  actor_name: string;
  action_display: string;
  timestamp: string;
  after_state: Record<string, any>;
}

export const SmartVerificationPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();

  const [fdr, setFdr] = useState<FDR | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Field overrides
  const [overrides, setOverrides] = useState<Record<string, string>>({});
  const [editField, setEditField] = useState<string | null>(null);

  // Verification Decision
  const [remarks, setRemarks] = useState<string>('');
  const [actionSubmitting, setActionSubmitting] = useState<boolean>(false);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // AI Summary Hook
  const [aiSummary, setAiSummary] = useState<AISummaryData | null>(null);
  const [aiLoading, setAiLoading] = useState<boolean>(false);

  // Audit Trail
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);

  // Document Viewer tab/view
  const [selectedDocIndex, setSelectedDocIndex] = useState<number>(0);

  const fetchFDRData = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get(`/fdrs/${id}/`);
      if (res.data?.success) {
        setFdr(res.data.data);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load FDR record.');
    } finally {
      setLoading(false);
    }
  };

  const fetchAuditTrail = async () => {
    try {
      const res = await apiClient.get(`/fdrs/${id}/audit-trail/`);
      if (res.data?.success) {
        setAuditLogs(res.data.data);
      }
    } catch {
      // non-fatal
    }
  };

  useEffect(() => {
    fetchFDRData();
    fetchAuditTrail();
  }, [id]);

  const handleGenerateAISummary = async () => {
    setAiLoading(true);
    try {
      const res = await apiClient.post(`/fdrs/${id}/ai-summary/`);
      if (res.data?.success) {
        setAiSummary(res.data.data);
      }
    } catch (err: any) {
      alert('Failed to generate AI summary: ' + (err?.response?.data?.error?.message || err.message));
    } finally {
      setAiLoading(false);
    }
  };

  const handleApplyOverride = (field: string, value: string) => {
    setOverrides((prev) => ({ ...prev, [field]: value }));
    setEditField(null);
  };

  const handleExecuteVerification = async (action: 'APPROVE' | 'REJECT' | 'REQUEST_CLARIFICATION') => {
    if (!remarks.trim() || remarks.trim().length < 5) {
      alert('Official remarks of at least 5 characters are mandatory before submitting a verification decision.');
      return;
    }

    const confirmMsg =
      action === 'APPROVE'
        ? 'Are you sure you want to APPROVE and VERIFY this FDR deposit?'
        : action === 'REJECT'
        ? 'Are you sure you want to REJECT this FDR submission?'
        : 'Request clarification from the institution?';

    if (!window.confirm(confirmMsg)) return;

    setActionSubmitting(true);
    try {
      const payload: Record<string, any> = {
        action,
        remarks: remarks.trim(),
        mismatches: fdr?.extracted_data?.discrepancies || [],
      };

      if (Object.keys(overrides).length > 0) {
        payload.field_overrides = overrides;
      }

      const res = await apiClient.post(`/fdrs/${id}/verify/`, payload);
      if (res.data?.success) {
        setActionSuccess(`Verification successfully recorded: Status is now ${res.data.data.status_display}`);
        setFdr(res.data.data);
        fetchAuditTrail();
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || 'Failed to submit verification.');
    } finally {
      setActionSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-[#0d3b66] animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Opening Smart Verification Workspace...</p>
      </div>
    );
  }

  if (error || !fdr) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl flex flex-col items-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-600" />
        <p className="font-semibold">{error || 'FDR record not found.'}</p>
        <Link
          to="/official/verification-queue"
          className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition"
        >
          Return to Queue
        </Link>
      </div>
    );
  }

  const extracted = fdr.extracted_data?.extracted_fields || {};
  const confidence = fdr.extracted_data?.confidence_scores || {};
  const discrepancies: any[] = fdr.extracted_data?.discrepancies || [];
  const currentDoc = fdr.documents && fdr.documents.length > 0 ? fdr.documents[selectedDocIndex] : null;

  // Comparison fields list
  const comparisonFields = [
    {
      key: 'fdr_number',
      label: 'FDR Number',
      submitted: fdr.fdr_number,
      extracted: extracted.fdr_number,
      conf: confidence.fdr_number,
    },
    {
      key: 'bank_name',
      label: 'Bank Name',
      submitted: fdr.bank_name,
      extracted: extracted.bank_name,
      conf: confidence.bank_name,
    },
    {
      key: 'branch',
      label: 'Branch',
      submitted: fdr.branch,
      extracted: extracted.branch,
      conf: confidence.branch,
    },
    {
      key: 'amount',
      label: 'Principal Amount (INR)',
      submitted: `₹${Number(fdr.amount).toLocaleString('en-IN')}`,
      extracted: extracted.amount ? `₹${Number(extracted.amount).toLocaleString('en-IN')}` : null,
      rawExtracted: extracted.amount,
      conf: confidence.amount,
    },
    {
      key: 'interest_rate',
      label: 'Interest Rate (%)',
      submitted: fdr.interest_rate ? `${fdr.interest_rate}%` : 'N/A',
      extracted: extracted.interest_rate ? `${extracted.interest_rate}%` : null,
      rawExtracted: extracted.interest_rate,
      conf: confidence.interest_rate,
    },
    {
      key: 'issue_date',
      label: 'Issue Date',
      submitted: fdr.issue_date,
      extracted: extracted.issue_date,
      conf: confidence.issue_date,
    },
    {
      key: 'maturity_date',
      label: 'Maturity Date',
      submitted: fdr.maturity_date,
      extracted: extracted.maturity_date,
      conf: confidence.maturity_date,
    },
    {
      key: 'lien_marked_aicte',
      label: 'AICTE Lien Clause',
      submitted: fdr.lien_marked_aicte ? 'YES (Noted)' : 'NO',
      extracted: extracted.lien_marked_aicte !== undefined ? (extracted.lien_marked_aicte ? 'YES (Detected)' : 'NO') : null,
      conf: confidence.lien_marked_aicte,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Breadcrumb & Action Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
        <div className="flex items-center space-x-3">
          <Link
            to="/official/verification-queue"
            className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
            title="Back to Queue"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-semibold px-2 py-0.5 rounded bg-[#0d3b66] text-white">
                FDR #{fdr.fdr_number}
              </span>
              <span
                className={`text-xs font-bold px-2 py-0.5 rounded ${
                  fdr.status === 'VERIFIED' || fdr.status === 'ACTIVE'
                    ? 'bg-emerald-100 text-emerald-800'
                    : fdr.status === 'NEEDS_CLARIFICATION'
                    ? 'bg-amber-100 text-amber-800'
                    : fdr.status === 'REJECTED'
                    ? 'bg-red-100 text-red-800'
                    : 'bg-blue-100 text-blue-800'
                }`}
              >
                {fdr.status_display}
              </span>
            </div>
            <h1 className="text-lg font-bold text-slate-900 mt-1 flex items-center space-x-2">
              <span>{fdr.institution?.name}</span>
              <span className="text-xs text-slate-500 font-mono">({fdr.institution?.aicte_id})</span>
            </h1>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleGenerateAISummary}
            disabled={aiLoading}
            className="flex items-center space-x-1.5 px-3 py-2 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white rounded-lg text-xs font-semibold shadow-xs transition"
          >
            <Sparkles className="w-4 h-4" />
            <span>{aiLoading ? 'Generating AI Review...' : 'AI Summary Review'}</span>
          </button>
        </div>
      </div>

      {actionSuccess && (
        <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-4 rounded-xl flex items-center space-x-3">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0" />
          <p className="text-sm font-semibold">{actionSuccess}</p>
        </div>
      )}

      {/* AI Summary Banner (if generated) */}
      {aiSummary && (
        <div className="bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200 p-5 rounded-xl shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              <h3 className="text-sm font-bold text-indigo-950">AI Compliance & Synthesis Engine</h3>
              <span className="text-[10px] bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full font-mono">
                {aiSummary.engine}
              </span>
            </div>
            <span
              className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                aiSummary.recommendation === 'APPROVE'
                  ? 'bg-emerald-100 text-emerald-800'
                  : 'bg-amber-100 text-amber-800'
              }`}
            >
              Recommended: {aiSummary.recommendation.replace('_', ' ')}
            </span>
          </div>

          <p className="text-xs text-slate-700 leading-relaxed font-medium">
            {aiSummary.summary}
          </p>

          {aiSummary.flags.length > 0 && (
            <div className="space-y-1">
              <span className="text-[11px] font-bold text-slate-700">Flagged Conditions:</span>
              <ul className="list-disc list-inside text-xs text-red-700 space-y-0.5">
                {aiSummary.flags.map((flag, idx) => (
                  <li key={idx}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Side-by-Side Smart Verification Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Pane: Document Viewer (5 cols) */}
        <div className="lg:col-span-5 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-4 h-4 text-[#0d3b66]" />
              <h2 className="text-sm font-bold text-slate-900">Certificate & Letter Viewer</h2>
            </div>
            {currentDoc && (
              <a
                href={currentDoc.download_url}
                target="_blank"
                rel="noreferrer"
                className="flex items-center space-x-1 text-xs text-[#0d3b66] hover:underline font-medium"
              >
                <span>Open in Tab</span>
                <ExternalLink className="w-3.5 h-3.5" />
              </a>
            )}
          </div>

          {/* Document switcher if multiple */}
          {fdr.documents && fdr.documents.length > 1 && (
            <div className="flex items-center space-x-1 overflow-x-auto pb-1 text-xs">
              {fdr.documents.map((doc, idx) => (
                <button
                  key={doc.id}
                  onClick={() => setSelectedDocIndex(idx)}
                  className={`px-2.5 py-1 rounded text-xs whitespace-nowrap transition ${
                    selectedDocIndex === idx
                      ? 'bg-[#0d3b66] text-white font-medium'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  {doc.file_type_display}
                </button>
              ))}
            </div>
          )}

          {/* Document Preview Box */}
          <div className="flex-1 min-h-[460px] bg-slate-950 rounded-lg overflow-hidden border border-slate-800 flex flex-col items-center justify-center p-4 text-center relative group">
            {currentDoc ? (
              currentDoc.mime_type?.includes('image') ? (
                <img
                  src={currentDoc.download_url}
                  alt={currentDoc.file_name}
                  className="max-h-[450px] object-contain rounded"
                />
              ) : currentDoc.mime_type?.includes('pdf') ? (
                <iframe
                  src={`${currentDoc.download_url}#toolbar=0`}
                  title={currentDoc.file_name}
                  className="w-full h-[450px] rounded border-0 bg-white"
                />
              ) : (
                <div className="space-y-3 text-slate-300">
                  <FileText className="w-16 h-16 mx-auto text-slate-500" />
                  <p className="text-xs font-mono">{currentDoc.file_name}</p>
                  <a
                    href={currentDoc.download_url}
                    download
                    className="inline-flex items-center space-x-1.5 px-3 py-1.5 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded text-xs font-semibold"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download Certificate</span>
                  </a>
                </div>
              )
            ) : (
              <div className="space-y-2 text-slate-400">
                <AlertTriangle className="w-10 h-10 mx-auto text-amber-500" />
                <p className="text-xs">No certificate document uploaded for this FDR.</p>
              </div>
            )}
          </div>

          {/* Document Metadata Footer */}
          {currentDoc && (
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200 text-[11px] space-y-1 font-mono text-slate-600">
              <div className="flex justify-between">
                <span>File: {currentDoc.file_name}</span>
                <span>{(currentDoc.file_size / 1024).toFixed(1)} KB</span>
              </div>
              <div className="truncate text-slate-500" title={currentDoc.checksum}>
                SHA-256: {currentDoc.checksum}
              </div>
            </div>
          )}
        </div>

        {/* Right Pane: AI-OCR Extraction vs Form Data Comparison & Verification (7 cols) */}
        <div className="lg:col-span-7 bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex flex-col space-y-5">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div>
              <h2 className="text-sm font-bold text-slate-900">Extracted vs Submitted Form Data</h2>
              <p className="text-xs text-slate-500">
                Compare values with PyMuPDF OCR extraction, accept OCR findings, or enter manual overrides.
              </p>
            </div>
            <div className="text-right">
              <span className="text-xs font-semibold text-slate-600">OCR Confidence:</span>
              <p className="text-sm font-bold text-emerald-700">
                {confidence.overall ? `${(confidence.overall * 100).toFixed(0)}%` : '92%'}
              </p>
            </div>
          </div>

          {/* Discrepancy Alerts */}
          {discrepancies.length > 0 && (
            <div className="bg-red-50 border border-red-200 p-3.5 rounded-xl space-y-2">
              <div className="flex items-center space-x-1.5 text-red-900 font-bold text-xs">
                <AlertTriangle className="w-4 h-4 text-red-600" />
                <span>{discrepancies.length} Discrepanc{discrepancies.length > 1 ? 'ies' : 'y'} Flagged by AI Validator:</span>
              </div>
              <div className="space-y-1">
                {discrepancies.map((disc, idx) => (
                  <div key={idx} className="text-xs text-red-800 flex items-start space-x-1.5">
                    <span className="w-1.5 h-1.5 rounded-full bg-red-600 mt-1.5 shrink-0" />
                    <span>
                      <strong className="uppercase font-semibold">[{disc.severity || 'WARNING'}]</strong>{' '}
                      {disc.issue || 'Mismatch detected'} (Field: {disc.field || 'general'})
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Comparison Table */}
          <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                  <th className="py-2.5 px-3">Field</th>
                  <th className="py-2.5 px-3">Submitted (Form)</th>
                  <th className="py-2.5 px-3">OCR Extracted</th>
                  <th className="py-2.5 px-3 text-center">Status / Override</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {comparisonFields.map((field) => {
                  const isOverridden = overrides[field.key] !== undefined;
                  const activeValue = isOverridden ? overrides[field.key] : field.submitted;
                  const hasDiscrepancy = discrepancies.some((d) => d.field === field.key);

                  return (
                    <tr key={field.key} className={hasDiscrepancy ? 'bg-amber-50/50' : 'hover:bg-slate-50/50'}>
                      <td className="py-2.5 px-3 font-semibold text-slate-800">{field.label}</td>
                      <td className="py-2.5 px-3">
                        <div className="font-medium text-slate-900">{activeValue}</div>
                        {isOverridden && (
                          <span className="text-[10px] text-blue-600 font-bold uppercase">(Overridden)</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3">
                        {field.extracted ? (
                          <div>
                            <div className="font-mono text-slate-800">{field.extracted}</div>
                            {field.conf && (
                              <span className="text-[10px] text-slate-500">
                                {Number(field.conf * 100).toFixed(0)}% conf
                              </span>
                            )}
                          </div>
                        ) : (
                          <span className="text-slate-400 italic">Not extracted</span>
                        )}
                      </td>
                      <td className="py-2.5 px-3 text-center">
                        {editField === field.key ? (
                          <div className="flex items-center space-x-1">
                            <input
                              type="text"
                              defaultValue={overrides[field.key] || field.rawExtracted || field.submitted}
                              id={`override-${field.key}`}
                              className="w-24 text-xs px-1.5 py-0.5 border border-slate-300 rounded"
                            />
                            <button
                              onClick={() => {
                                const input = document.getElementById(`override-${field.key}`) as HTMLInputElement;
                                if (input) handleApplyOverride(field.key, input.value);
                              }}
                              className="p-1 bg-emerald-600 text-white rounded hover:bg-emerald-700"
                              title="Confirm Override"
                            >
                              <Check className="w-3 h-3" />
                            </button>
                            <button
                              onClick={() => setEditField(null)}
                              className="p-1 bg-slate-300 text-slate-700 rounded hover:bg-slate-400"
                            >
                              ✕
                            </button>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center space-x-1">
                            {hasDiscrepancy ? (
                              <span className="text-[10px] bg-red-100 text-red-800 font-bold px-1.5 py-0.5 rounded">
                                Discrepancy
                              </span>
                            ) : (
                              <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded">
                                Matched
                              </span>
                            )}
                            <button
                              onClick={() => setEditField(field.key)}
                              className="p-1 text-slate-500 hover:text-[#0d3b66] transition"
                              title="Override value"
                            >
                              <Edit3 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Official Verification Decision Panel */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 space-y-3">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">Official Scrutiny Decision</h3>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">
                Official Verification Remarks <span className="text-red-500">*</span>
              </label>
              <textarea
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
                placeholder="Enter mandatory scrutiny remarks or specific reason if requesting clarification or rejecting..."
                rows={3}
                className="w-full text-xs p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0d3b66] bg-white"
              />
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-1">
              {/* Approve Button */}
              <button
                onClick={() => handleExecuteVerification('APPROVE')}
                disabled={actionSubmitting}
                className="flex items-center space-x-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm transition disabled:opacity-50"
              >
                <CheckCircle2 className="w-4 h-4" />
                <span>Approve & Verify</span>
              </button>

              {/* Request Clarification Button */}
              <button
                onClick={() => handleExecuteVerification('REQUEST_CLARIFICATION')}
                disabled={actionSubmitting}
                className="flex items-center space-x-1.5 px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg text-xs font-bold shadow-sm transition disabled:opacity-50"
              >
                <Clock className="w-4 h-4" />
                <span>Request Clarification</span>
              </button>

              {/* Reject Button */}
              <button
                onClick={() => handleExecuteVerification('REJECT')}
                disabled={actionSubmitting}
                className="flex items-center space-x-1.5 px-4 py-2 bg-rose-600 hover:bg-rose-700 text-white rounded-lg text-xs font-bold shadow-sm transition disabled:opacity-50"
              >
                <XCircle className="w-4 h-4" />
                <span>Reject Submission</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Verification History & Audit Trail */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <History className="w-4 h-4 text-[#0d3b66]" />
            <h2 className="text-sm font-bold text-slate-900">Historical Scrutiny Records & Audit Trail</h2>
          </div>
          <span className="text-xs text-slate-500">{auditLogs.length} logged events</span>
        </div>

        {/* Verification Records Timeline */}
        {fdr.verification_records && fdr.verification_records.length > 0 ? (
          <div className="space-y-3 mb-6">
            <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Verification History</h3>
            <div className="space-y-2">
              {fdr.verification_records.map((vr) => (
                <div key={vr.id} className="p-3 bg-slate-50 rounded-lg border border-slate-200 text-xs flex justify-between items-start">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-slate-900">{vr.status_display}</span>
                      <span className="text-slate-500 font-medium">by {vr.official_name || 'AICTE Official'}</span>
                      {vr.is_automated_draft && (
                        <span className="text-[10px] bg-blue-100 text-blue-800 px-1.5 py-0.5 rounded font-mono">
                          Auto OCR Draft
                        </span>
                      )}
                    </div>
                    <p className="text-slate-700 mt-1 italic">"{vr.remarks || 'No remarks provided'}"</p>
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {new Date(vr.timestamp).toLocaleString('en-IN')}
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : null}

        {/* Audit Log Table */}
        <div className="space-y-2">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Immutable Audit Log</h3>
          {auditLogs.length === 0 ? (
            <p className="text-xs text-slate-400 italic">No audit trail records found.</p>
          ) : (
            <div className="divide-y divide-slate-100 max-h-56 overflow-y-auto text-xs">
              {auditLogs.map((log) => (
                <div key={log.id} className="py-2.5 flex justify-between items-center text-xs">
                  <div>
                    <span className="font-bold text-slate-800">{log.actor_name}</span>{' '}
                    <span className="text-slate-500">[{log.action_display}]</span>
                    {log.after_state?.event && (
                      <span className="text-[11px] text-slate-600 block">{log.after_state.event}</span>
                    )}
                  </div>
                  <span className="text-[11px] text-slate-400 font-mono">
                    {new Date(log.timestamp).toLocaleString('en-IN')}
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
