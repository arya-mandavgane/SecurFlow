import React, { useEffect, useState } from 'react';
import {
  FileCheck2,
  Clock,
  CheckCircle2,
  Download,
  Search,
  RefreshCw,
  X,
  ShieldCheck,
  FileText
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { ReleaseRequest, ReleaseRequestStatus } from '../../types';

export const ReleaseEvaluationPage: React.FC = () => {
  const [requests, setRequests] = useState<ReleaseRequest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  // Selected request for evaluation modal
  const [selectedReq, setSelectedReq] = useState<ReleaseRequest | null>(null);
  const [evalRemarks, setEvalRemarks] = useState<string>('');
  const [orderNumber, setOrderNumber] = useState<string>('');
  const [checklist, setChecklist] = useState({
    cycle_completed: true,
    no_pending_compliance: true,
    lockin_satisfied: true,
  });
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [decisionSuccess, setDecisionSuccess] = useState<string | null>(null);

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);

      const res = await apiClient.get(`/releases/?${params.toString()}`);
      if (res.data?.results) {
        setRequests(res.data.results);
      } else if (Array.isArray(res.data)) {
        setRequests(res.data);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRequests();
  }, [statusFilter]);

  const handleOpenEval = (req: ReleaseRequest) => {
    setSelectedReq(req);
    setEvalRemarks(req.official_remarks || '');
    setOrderNumber(req.refund_order_number || '');
    setDecisionSuccess(null);
  };

  const handleExecuteDecision = async (action: ReleaseRequestStatus) => {
    if (!selectedReq) return;
    if (!evalRemarks.trim()) {
      alert('Official remarks are required before taking a release decision.');
      return;
    }

    setIsSubmitting(true);
    try {
      const payload: Record<string, any> = {
        action,
        official_remarks: evalRemarks.trim(),
        checklist,
      };
      if (orderNumber) payload.refund_order_number = orderNumber;

      const res = await apiClient.post(`/releases/${selectedReq.id}/decision/`, payload);
      if (res.data?.success) {
        setDecisionSuccess(`Request successfully updated to: ${res.data.data.status_display}`);
        setSelectedReq(res.data.data);
        fetchRequests();
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err?.response?.data?.detail || 'Failed to record decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const pendingCount = requests.filter((r) => ['REQUESTED', 'UNDER_REVIEW'].includes(r.status)).length;
  const approvedCount = requests.filter((r) => ['APPROVED', 'RELEASED'].includes(r.status)).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0d3b66]/10 text-[#0d3b66]">
              Regional Evaluation Bureau
            </span>
            <span className="text-xs text-slate-500 font-mono">Lien Discharge Panel</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Lien Release & Refund Approvals</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Review institutional security deposit release claims, verify compliance checklists, and issue formal AICTE Release Orders.
          </p>
        </div>

        <button
          onClick={fetchRequests}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-amber-800 uppercase">Pending Official Evaluation</p>
            <p className="text-2xl font-bold text-amber-950 mt-0.5">{pendingCount}</p>
            <p className="text-[11px] text-amber-700 mt-0.5">Awaiting regional review & decision</p>
          </div>
          <Clock className="w-8 h-8 text-amber-600" />
        </div>

        <div className="bg-emerald-50 border border-emerald-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-emerald-800 uppercase">Approved & Released</p>
            <p className="text-2xl font-bold text-emerald-950 mt-0.5">{approvedCount}</p>
            <p className="text-[11px] text-emerald-700 mt-0.5">Formal release order generated</p>
          </div>
          <FileCheck2 className="w-8 h-8 text-emerald-600" />
        </div>

        <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-blue-800 uppercase">Total Release Claims</p>
            <p className="text-2xl font-bold text-blue-950 mt-0.5">{requests.length}</p>
            <p className="text-[11px] text-blue-700 mt-0.5">Recorded across all institutions</p>
          </div>
          <FileText className="w-8 h-8 text-blue-600" />
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row gap-3 items-center justify-between">
        <div className="relative flex-1 w-full">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search FDR number, Institute name, AICTE ID, Release order..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchRequests()}
            className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#0d3b66]"
          />
        </div>

        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white"
        >
          <option value="">All Release Statuses</option>
          <option value="REQUESTED">Requested (New)</option>
          <option value="UNDER_REVIEW">Under Review</option>
          <option value="MORE_INFO_NEEDED">More Info Needed</option>
          <option value="APPROVED">Approved</option>
          <option value="RELEASED">Released / Discharged</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-500">Loading release requests...</div>
        ) : requests.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-500">No release requests found matching query.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase">
                  <th className="py-3 px-4">Request Ref</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Deposit Details</th>
                  <th className="py-3 px-4 text-right">Amount (INR)</th>
                  <th className="py-3 px-4">Reason / Justification</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {requests.map((req) => (
                  <tr key={req.id} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span className="font-bold text-[#0d3b66]">REL-REQ-{req.id.toString().padStart(4, '0')}</span>
                      <span className="text-[10px] text-slate-400 block font-mono">
                        {new Date(req.created_at).toLocaleDateString('en-IN')}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 truncate max-w-[180px]">{req.institution_name}</div>
                      <div className="text-[11px] text-slate-500 font-mono">{req.institution_aicte_id}</div>
                    </td>
                    <td className="py-3 px-4">
                      <div className="font-bold text-slate-800">#{req.fdr_number}</div>
                      <div className="text-[11px] text-slate-500">{req.bank_name}</div>
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-slate-900 whitespace-nowrap">
                      ₹{Number(req.amount).toLocaleString('en-IN')}
                    </td>
                    <td className="py-3 px-4">
                      <p className="line-clamp-2 text-slate-600 text-[11px] max-w-[220px]" title={req.reason}>
                        {req.reason}
                      </p>
                    </td>
                    <td className="py-3 px-4 whitespace-nowrap">
                      <span
                        className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                          req.status === 'APPROVED' || req.status === 'RELEASED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : req.status === 'MORE_INFO_NEEDED'
                            ? 'bg-purple-100 text-purple-800'
                            : req.status === 'REJECTED'
                            ? 'bg-red-100 text-red-800'
                            : req.status === 'UNDER_REVIEW'
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {req.status_display}
                      </span>
                      {req.refund_order_number && (
                        <span className="text-[10px] text-slate-500 block font-mono truncate max-w-[140px]">
                          {req.refund_order_number}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <div className="flex items-center justify-center space-x-1.5">
                        <button
                          onClick={() => handleOpenEval(req)}
                          className="px-2.5 py-1 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded text-xs font-semibold shadow-xs transition"
                        >
                          Evaluate
                        </button>
                        {req.download_order_url && (
                          <a
                            href={req.download_order_url}
                            download
                            className="p-1 text-slate-600 hover:text-emerald-700 bg-slate-100 hover:bg-slate-200 rounded transition"
                            title="Download Release Order PDF"
                          >
                            <Download className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Official Release Evaluation Modal */}
      {selectedReq && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-slate-200">
            {/* Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="w-5 h-5 text-[#0d3b66]" />
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    Official Release Evaluation: REL-REQ-{selectedReq.id.toString().padStart(4, '0')}
                  </h2>
                  <p className="text-xs text-slate-500 font-mono">
                    {selectedReq.institution_name} ({selectedReq.institution_aicte_id})
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedReq(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
              {decisionSuccess && (
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg font-semibold flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{decisionSuccess}</span>
                </div>
              )}

              {/* Deposit Parameter Box */}
              <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-2 gap-3">
                <div>
                  <span className="text-slate-400 font-medium">FDR Number:</span>
                  <p className="font-bold text-slate-900 text-sm">#{selectedReq.fdr_number}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Principal Amount:</span>
                  <p className="font-bold text-slate-900 text-sm">
                    ₹{Number(selectedReq.amount).toLocaleString('en-IN')}
                  </p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Bank & Branch:</span>
                  <p className="font-semibold text-slate-800">{selectedReq.bank_name}</p>
                </div>
                <div>
                  <span className="text-slate-400 font-medium">Current Status:</span>
                  <p className="font-semibold text-[#0d3b66]">{selectedReq.status_display}</p>
                </div>
              </div>

              {/* Institution Justification */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Institutional Justification for Release:
                </label>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-slate-700 whitespace-pre-wrap">
                  {selectedReq.reason}
                </div>
              </div>

              {/* Compliance Checklist */}
              <div className="bg-blue-50/50 border border-blue-200 p-4 rounded-xl space-y-2">
                <h3 className="font-bold text-slate-800 uppercase tracking-wider text-[11px]">
                  Mandatory AICTE Compliance Verification Checklist:
                </h3>
                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.lockin_satisfied}
                    onChange={(e) => setChecklist({ ...checklist, lockin_satisfied: e.target.checked })}
                    className="rounded text-[#0d3b66] focus:ring-0"
                  />
                  <span className="text-slate-800">
                    Minimum statutory lock-in period (e.g. 5-8 years as per APH) has elapsed.
                  </span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.cycle_completed}
                    onChange={(e) => setChecklist({ ...checklist, cycle_completed: e.target.checked })}
                    className="rounded text-[#0d3b66] focus:ring-0"
                  />
                  <span className="text-slate-800">
                    Academic approval cycle completed and student batch obligations fulfilled.
                  </span>
                </label>

                <label className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={checklist.no_pending_compliance}
                    onChange={(e) => setChecklist({ ...checklist, no_pending_compliance: e.target.checked })}
                    className="rounded text-[#0d3b66] focus:ring-0"
                  />
                  <span className="text-slate-800">
                    No vigilance, legal dispute, or financial non-compliance pending against institution.
                  </span>
                </label>
              </div>

              {/* Official Remarks */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Official Regional Bureau Remarks <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={3}
                  required
                  value={evalRemarks}
                  onChange={(e) => setEvalRemarks(e.target.value)}
                  placeholder="Record formal reasons for approval, rejection, or specific information needed from institution..."
                  className="w-full p-2.5 border border-slate-300 rounded-lg focus:outline-none focus:ring-1 focus:ring-[#0d3b66]"
                />
              </div>

              {/* Release Order Number (if approved or releasing) */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Release Order / Refund Reference Number (Optional - auto-generated if left blank)
                </label>
                <input
                  type="text"
                  value={orderNumber}
                  onChange={(e) => setOrderNumber(e.target.value)}
                  placeholder="e.g. AICTE/RO/REL/2026/00042"
                  className="w-full p-2 border border-slate-300 rounded font-mono"
                />
              </div>

              {/* Download link if available */}
              {selectedReq.download_order_url && (
                <div className="pt-2 flex items-center justify-between bg-emerald-50 p-3 rounded-lg border border-emerald-200">
                  <span className="text-emerald-900 font-semibold">
                    Official Release Order PDF is generated & active.
                  </span>
                  <a
                    href={selectedReq.download_order_url}
                    download
                    className="inline-flex items-center space-x-1 px-3 py-1 bg-emerald-700 text-white rounded font-bold hover:bg-emerald-800 transition"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download PDF Letter</span>
                  </a>
                </div>
              )}

              {/* Action Buttons */}
              <div className="pt-3 border-t border-slate-200 flex flex-wrap items-center justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setSelectedReq(null)}
                  className="px-3.5 py-2 border border-slate-300 rounded text-slate-700 hover:bg-slate-100"
                >
                  Close
                </button>

                <button
                  type="button"
                  onClick={() => handleExecuteDecision('UNDER_REVIEW')}
                  disabled={isSubmitting}
                  className="px-3 py-2 bg-slate-700 text-white rounded font-semibold hover:bg-slate-800 disabled:opacity-50"
                >
                  Under Review
                </button>

                <button
                  type="button"
                  onClick={() => handleExecuteDecision('MORE_INFO_NEEDED')}
                  disabled={isSubmitting}
                  className="px-3 py-2 bg-purple-600 text-white rounded font-semibold hover:bg-purple-700 disabled:opacity-50"
                >
                  Request Info
                </button>

                <button
                  type="button"
                  onClick={() => handleExecuteDecision('REJECTED')}
                  disabled={isSubmitting}
                  className="px-3 py-2 bg-rose-600 text-white rounded font-semibold hover:bg-rose-700 disabled:opacity-50"
                >
                  Reject Claim
                </button>

                <button
                  type="button"
                  onClick={() => handleExecuteDecision('APPROVED')}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-emerald-600 text-white rounded font-bold hover:bg-emerald-700 shadow-xs disabled:opacity-50"
                >
                  Approve Order
                </button>

                <button
                  type="button"
                  onClick={() => handleExecuteDecision('RELEASED')}
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-blue-700 text-white rounded font-bold hover:bg-blue-800 shadow-xs disabled:opacity-50"
                >
                  Discharge & Release
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
