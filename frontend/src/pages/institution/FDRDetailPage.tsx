import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';
import {
  FileText,
  Download,
  AlertCircle,
  Upload,
  Copy,
  Check,
  ArrowLeft
} from 'lucide-react';

export const FDRDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [fdr, setFdr] = useState<FDR | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Clarification Response Modal State
  const [showClarificationModal, setShowClarificationModal] = useState<boolean>(false);
  const [clarificationRemarks, setClarificationRemarks] = useState<string>('');
  const [clarificationFile, setClarificationFile] = useState<File | null>(null);
  const [isSubmittingClarification, setIsSubmittingClarification] = useState<boolean>(false);

  // Document Upload Modal State
  const [showUploadModal, setShowUploadModal] = useState<boolean>(false);
  const [additionalFile, setAdditionalFile] = useState<File | null>(null);
  const [additionalFileType, setAdditionalFileType] = useState<string>('BANK_LETTER');
  const [isUploading, setIsUploading] = useState<boolean>(false);

  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  useEffect(() => {
    fetchFDRDetail();
  }, [id]);

  const fetchFDRDetail = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get(`/fdrs/${id}/`);
      setFdr(res.data);
    } catch (err) {
      setErrorMsg('Failed to load FDR details. The record might not exist or you lack permission.');
    } finally {
      setLoading(false);
    }
  };

  const handleCopyHash = (hash: string) => {
    navigator.clipboard.writeText(hash);
    setCopiedHash(hash);
    setTimeout(() => setCopiedHash(null), 2000);
  };

  const handleClarificationSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fdr) return;
    setIsSubmittingClarification(true);

    try {
      // 1. Upload new document if attached
      if (clarificationFile) {
        const docData = new FormData();
        docData.append('file', clarificationFile);
        docData.append('file_type', 'RENEWAL_ADVICE');
        await apiClient.post(`/fdrs/${fdr.id}/documents/`, docData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      // 2. Update remarks and transition to UNDER_REVIEW
      await apiClient.patch(`/fdrs/${fdr.id}/`, {
        remarks: clarificationRemarks ? `[Institution Response]: ${clarificationRemarks}` : fdr.remarks,
      });

      setShowClarificationModal(false);
      setClarificationRemarks('');
      setClarificationFile(null);
      fetchFDRDetail();
    } catch (err) {
      alert('Failed to submit clarification response.');
    } finally {
      setIsSubmittingClarification(false);
    }
  };

  const handleUploadAdditional = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fdr || !additionalFile) return;
    setIsUploading(true);

    try {
      const docData = new FormData();
      docData.append('file', additionalFile);
      docData.append('file_type', additionalFileType);

      await apiClient.post(`/fdrs/${fdr.id}/documents/`, docData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setShowUploadModal(false);
      setAdditionalFile(null);
      fetchFDRDetail();
    } catch (err) {
      alert('Failed to upload document.');
    } finally {
      setIsUploading(false);
    }
  };

  if (loading) {
    return <div className="p-12 text-center text-sm text-slate-500">Loading FDR details...</div>;
  }

  if (errorMsg || !fdr) {
    return (
      <div className="p-8 bg-red-50 border border-red-200 rounded-xl text-center space-y-3">
        <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
        <div className="text-sm font-bold text-red-900">{errorMsg || 'FDR Not Found'}</div>
        <Link to="/fdrs" className="text-xs font-semibold text-[#001e3d] underline">
          &larr; Return to FDR list
        </Link>
      </div>
    );
  }

  const latestVerification = fdr.verification_records?.[0];

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Back Link & Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="space-y-1">
          <Link to="/fdrs" className="text-xs font-semibold text-slate-500 hover:text-slate-800 flex items-center space-x-1">
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to All FDRs</span>
          </Link>
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-[#001e3d] font-mono">{fdr.fdr_number}</h1>
            <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-blue-100 text-[#001e3d] border border-blue-200">
              {fdr.status_display}
            </span>
          </div>
          <div className="text-xs text-slate-500">
            {fdr.bank_name} &bull; Pledged in favour of AICTE &bull; Cycle: {fdr.purpose_approval_cycle}
          </div>
        </div>

        {fdr.status === 'NEEDS_CLARIFICATION' && (
          <button
            onClick={() => setShowClarificationModal(true)}
            className="bg-amber-600 hover:bg-amber-700 text-white px-4 py-2.5 rounded-lg text-xs font-bold shadow animate-pulse flex items-center space-x-1.5"
          >
            <AlertCircle className="w-4 h-4" />
            <span>Respond to Clarification</span>
          </button>
        )}
      </div>

      {/* Official Clarification Banner if Applicable */}
      {fdr.status === 'NEEDS_CLARIFICATION' && latestVerification && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-xl p-5 shadow-sm space-y-2">
          <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm">
            <AlertCircle className="w-5 h-5 text-amber-600" />
            <span>AICTE Official Clarification Requested</span>
          </div>
          <div className="text-xs text-amber-950 bg-white/80 p-3 rounded-lg border border-amber-200 leading-relaxed">
            <span className="font-semibold block text-slate-700 mb-1">Official Remarks:</span>
            {latestVerification.remarks}
          </div>
          {latestVerification.mismatches?.length > 0 && (
            <div className="text-xs text-amber-900 pt-1">
              <span className="font-semibold">Flagged Mismatches:</span>
              <ul className="list-disc pl-5 mt-1 space-y-0.5 text-slate-700">
                {latestVerification.mismatches.map((m, idx) => (
                  <li key={idx}>
                    <span className="font-medium capitalize">{m.field || 'Field'}:</span> {m.issue || `Expected ${m.expected || ''}, found ${m.found || ''}`}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Lifecycle Progress Bar */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-4">Lifecycle Verification Stages</h2>
        <div className="grid grid-cols-4 gap-2 text-center text-xs">
          <div className="space-y-1.5">
            <div className="w-8 h-8 mx-auto rounded-full bg-emerald-500 text-white flex items-center justify-center font-bold">✓</div>
            <div className="font-semibold text-slate-900">1. Submitted</div>
            <div className="text-[10px] text-slate-400">{fdr.created_at?.slice(0, 10)}</div>
          </div>

          <div className="space-y-1.5">
            <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center font-bold ${
              ['UNDER_REVIEW', 'VERIFIED', 'ACTIVE', 'NEEDS_CLARIFICATION'].includes(fdr.status)
                ? 'bg-blue-600 text-white'
                : 'bg-slate-100 text-slate-400'
            }`}>2</div>
            <div className="font-semibold text-slate-900">2. Review</div>
            <div className="text-[10px] text-slate-400">OCR & Document Cross-check</div>
          </div>

          <div className="space-y-1.5">
            <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center font-bold ${
              ['VERIFIED', 'ACTIVE'].includes(fdr.status)
                ? 'bg-emerald-600 text-white'
                : fdr.status === 'NEEDS_CLARIFICATION'
                ? 'bg-amber-500 text-white animate-pulse'
                : 'bg-slate-100 text-slate-400'
            }`}>3</div>
            <div className="font-semibold text-slate-900">3. Decision</div>
            <div className="text-[10px] text-slate-400">Approval / Clarification</div>
          </div>

          <div className="space-y-1.5">
            <div className={`w-8 h-8 mx-auto rounded-full flex items-center justify-center font-bold ${
              fdr.status === 'ACTIVE' ? 'bg-emerald-600 text-white' : 'bg-slate-100 text-slate-400'
            }`}>4</div>
            <div className="font-semibold text-slate-900">4. Active Lien</div>
            <div className="text-[10px] text-slate-400">Tracked to Maturity</div>
          </div>
        </div>
      </div>

      {/* Grid: Details & Documents */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Deposit Parameters */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <h2 className="text-sm font-bold text-slate-900 border-b border-slate-100 pb-2">Fixed Deposit Parameters</h2>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-slate-400 block text-[11px]">Bank Name</span>
              <span className="font-semibold text-slate-800">{fdr.bank_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Branch Location</span>
              <span className="font-semibold text-slate-800">{fdr.branch || 'Main Branch'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Deposit Amount</span>
              <span className="font-bold text-slate-900 text-sm">₹{Number(fdr.amount).toLocaleString('en-IN')}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Interest Rate</span>
              <span className="font-semibold text-slate-800">{fdr.interest_rate ? `${fdr.interest_rate}% p.a.` : 'N/A'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Issue Date</span>
              <span className="font-semibold text-slate-800">{fdr.issue_date}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Maturity Date</span>
              <span className="font-semibold text-slate-800">{fdr.maturity_date}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Lien Status</span>
              <span className="font-semibold text-emerald-700">{fdr.lien_marked_aicte ? 'Pledged to AICTE' : 'Not Pledged'}</span>
            </div>
            <div>
              <span className="text-slate-400 block text-[11px]">Approval Purpose</span>
              <span className="font-semibold text-slate-800">{fdr.purpose_approval_cycle}</span>
            </div>
          </div>
        </div>

        {/* Documents Repository */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-2">
            <h2 className="text-sm font-bold text-slate-900">Uploaded Documents ({fdr.documents?.length || 0})</h2>
            <button
              onClick={() => setShowUploadModal(true)}
              className="text-xs font-semibold text-[#001e3d] hover:underline flex items-center space-x-1"
            >
              <Upload className="w-3.5 h-3.5" />
              <span>Attach File</span>
            </button>
          </div>

          <div className="space-y-3">
            {(!fdr.documents || fdr.documents.length === 0) ? (
              <p className="text-xs text-slate-400 italic py-4 text-center">No documents uploaded yet.</p>
            ) : (
              fdr.documents.map((doc) => (
                <div key={doc.id} className="p-3 bg-slate-50 border border-slate-200 rounded-lg space-y-2 text-xs">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2 font-medium text-slate-800">
                      <FileText className="w-4 h-4 text-blue-700" />
                      <span className="truncate max-w-[200px]">{doc.file_name}</span>
                    </div>
                    <span className="text-[10px] bg-slate-200 text-slate-700 px-2 py-0.5 rounded font-medium">
                      {doc.file_type_display}
                    </span>
                  </div>

                  {/* Cryptographic SHA-256 Checksum */}
                  <div className="flex items-center justify-between text-[10px] text-slate-500 bg-white px-2 py-1 rounded border border-slate-200 font-mono">
                    <span className="truncate max-w-[240px]">SHA-256: {doc.checksum}</span>
                    <button
                      onClick={() => handleCopyHash(doc.checksum)}
                      className="text-slate-400 hover:text-slate-700 ml-1"
                      title="Copy Checksum"
                    >
                      {copiedHash === doc.checksum ? <Check className="w-3 h-3 text-emerald-600" /> : <Copy className="w-3 h-3" />}
                    </button>
                  </div>

                  <div className="flex items-center justify-between pt-1">
                    <span className="text-[10px] text-slate-400">{(doc.file_size / 1024).toFixed(1)} KB</span>
                    <a
                      href={doc.download_url}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center space-x-1 text-xs font-semibold text-[#0d3b66] hover:underline"
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </a>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Clarification Response Modal */}
      {showClarificationModal && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Respond to AICTE Clarification</h3>
              <button onClick={() => setShowClarificationModal(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            <form onSubmit={handleClarificationSubmit} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Your Explanation / Clarification Remarks *</label>
                <textarea
                  rows={4}
                  required
                  value={clarificationRemarks}
                  onChange={(e) => setClarificationRemarks(e.target.value)}
                  placeholder="Provide clarification addressing the official remarks..."
                  className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Re-upload Corrected Document (Optional)</label>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => e.target.files && setClarificationFile(e.target.files[0])}
                  className="w-full p-2 border rounded-lg text-slate-600 text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowClarificationModal(false)}
                  className="px-4 py-2 border rounded-lg font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingClarification}
                  className="px-5 py-2 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg font-bold transition disabled:opacity-50"
                >
                  {isSubmittingClarification ? 'Submitting...' : 'Submit Clarification'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Additional Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-xl max-w-md w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">Upload Additional Document</h3>
              <button onClick={() => setShowUploadModal(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            <form onSubmit={handleUploadAdditional} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Document Type</label>
                <select
                  value={additionalFileType}
                  onChange={(e) => setAdditionalFileType(e.target.value)}
                  className="w-full p-2.5 border rounded-lg focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
                >
                  <option value="BANK_LETTER">Bank Lien / Pledge Advice Letter</option>
                  <option value="RENEWAL_ADVICE">Renewal Certificate</option>
                  <option value="RELEASE_NOC">Release NOC</option>
                  <option value="OTHER">Other Compliance Document</option>
                </select>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Select File (PDF, JPG, PNG)</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => e.target.files && setAdditionalFile(e.target.files[0])}
                  className="w-full p-2 border rounded-lg text-slate-600 text-xs"
                />
              </div>

              <div className="flex justify-end space-x-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="px-4 py-2 border rounded-lg font-medium text-slate-600 hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="px-5 py-2 bg-[#001e3d] hover:bg-[#0d3b66] text-white rounded-lg font-bold transition disabled:opacity-50"
                >
                  {isUploading ? 'Uploading...' : 'Upload File'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
