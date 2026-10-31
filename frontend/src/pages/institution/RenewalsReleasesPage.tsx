import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';
import { RefreshCw, CheckCircle2 } from 'lucide-react';

export const RenewalsReleasesPage: React.FC = () => {
  const [fdrs, setFdrs] = useState<FDR[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'renewals' | 'releases'>('renewals');

  // Request modal state
  const [selectedFdr, setSelectedFdr] = useState<FDR | null>(null);
  const [requestReason, setRequestReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    fetchFDRs();
  }, []);

  const fetchFDRs = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/fdrs/');
      setFdrs(res.data.results || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const eligibleForRenewal = fdrs.filter((f) => ['ACTIVE', 'EXPIRING_SOON', 'EXPIRED'].includes(f.status));
  const eligibleForRelease = fdrs.filter((f) => ['ACTIVE', 'VERIFIED'].includes(f.status));

  const handleOpenModal = (fdr: FDR) => {
    setSelectedFdr(fdr);
    setRequestReason('');
    setSuccessMsg(null);
  };

  const handleSubmitRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFdr) return;
    setIsSubmitting(true);

    try {
      // Record remark / request on the FDR
      const actionName = activeTab === 'renewals' ? 'Renewal / Replacement' : 'Lien Release & Refund';
      await apiClient.patch(`/fdrs/${selectedFdr.id}/`, {
        remarks: `[${actionName} Initiated]: ${requestReason}`,
      });

      setSuccessMsg(`Your ${actionName} request for FDR #${selectedFdr.fdr_number} has been logged and queued for AICTE Regional Office evaluation.`);
      setTimeout(() => {
        setSelectedFdr(null);
        setSuccessMsg(null);
        fetchFDRs();
      }, 2500);
    } catch (err) {
      alert('Failed to submit request.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-[#001e3d]">FDR Renewals & Lien Release Gateway</h1>
        <p className="text-xs text-slate-500 mt-1">Manage deposit renewals and request AICTE lien release upon obligation completion</p>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200">
        <button
          onClick={() => setActiveTab('renewals')}
          className={`py-3 px-6 text-xs font-bold border-b-2 flex items-center space-x-2 transition ${
            activeTab === 'renewals'
              ? 'border-[#001e3d] text-[#001e3d]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>FDR Renewal & Replacement ({eligibleForRenewal.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('releases')}
          className={`py-3 px-6 text-xs font-bold border-b-2 flex items-center space-x-2 transition ${
            activeTab === 'releases'
              ? 'border-[#001e3d] text-[#001e3d]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>Lien Release / Refund Requests ({eligibleForRelease.length})</span>
        </button>
      </div>

      {/* Content List */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-sm font-bold text-slate-900">
            {activeTab === 'renewals' ? 'FDRs Approaching Maturity or Requiring Renewal' : 'Verified Deposits Eligible for Lien Release'}
          </h2>
          <span className="text-xs text-slate-500">Subject to AICTE Handbooks 2024-27</span>
        </div>

        {loading ? (
          <div className="py-8 text-center text-xs text-slate-400">Loading records...</div>
        ) : (
          <div className="space-y-3">
            {(activeTab === 'renewals' ? eligibleForRenewal : eligibleForRelease).map((fdr) => (
              <div key={fdr.id} className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="font-mono font-bold text-slate-900">{fdr.fdr_number}</span>
                    <span className="text-slate-400">&bull;</span>
                    <span className="font-semibold text-slate-800">{fdr.bank_name}</span>
                  </div>
                  <div className="text-slate-500">
                    Amount: <span className="font-semibold text-slate-800">₹{Number(fdr.amount).toLocaleString('en-IN')}</span> | Maturity: {fdr.maturity_date}
                  </div>
                  <div className="text-[11px] text-slate-400 font-mono">Cycle: {fdr.purpose_approval_cycle}</div>
                </div>

                <button
                  onClick={() => handleOpenModal(fdr)}
                  className={`px-4 py-2 rounded-lg font-bold text-xs shadow-sm transition whitespace-nowrap ${
                    activeTab === 'renewals'
                      ? 'bg-[#001e3d] hover:bg-[#0d3b66] text-white'
                      : 'bg-emerald-600 hover:bg-emerald-700 text-white'
                  }`}
                >
                  {activeTab === 'renewals' ? 'Initiate Renewal' : 'Request Lien Release'}
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Request Modal */}
      {selectedFdr && (
        <div className="fixed inset-0 bg-slate-900/60 z-50 flex items-center justify-center p-4 backdrop-blur-sm">
          <div className="bg-white rounded-xl max-w-lg w-full p-6 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b pb-3">
              <h3 className="text-base font-bold text-slate-900">
                {activeTab === 'renewals' ? 'Initiate FDR Renewal Request' : 'Request Lien Release & Refund'}
              </h3>
              <button onClick={() => setSelectedFdr(null)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>

            {successMsg ? (
              <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs text-center space-y-2">
                <CheckCircle2 className="w-8 h-8 text-emerald-600 mx-auto" />
                <div className="font-bold">{successMsg}</div>
              </div>
            ) : (
              <form onSubmit={handleSubmitRequest} className="space-y-4 text-xs">
                <div className="p-3 bg-slate-50 rounded-lg space-y-1">
                  <div className="font-mono font-bold text-slate-900">{selectedFdr.fdr_number} ({selectedFdr.bank_name})</div>
                  <div className="text-slate-600">Deposit Amount: ₹{Number(selectedFdr.amount).toLocaleString('en-IN')}</div>
                  <div className="text-slate-600">Maturity Date: {selectedFdr.maturity_date}</div>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">
                    {activeTab === 'renewals' ? 'Reason for Renewal / Replacement Details *' : 'Reason for Lien Release Request *'}
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={requestReason}
                    onChange={(e) => setRequestReason(e.target.value)}
                    placeholder={
                      activeTab === 'renewals'
                        ? 'e.g. Deposit maturing in 30 days. Renewal instructions issued to bank.'
                        : 'e.g. Fulfilled 5-year lock-in period after successful completion of accreditation cycle.'
                    }
                    className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
                  />
                </div>

                <div className="flex justify-end space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSelectedFdr(null)}
                    className="px-4 py-2 border rounded-lg font-medium text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="px-5 py-2 bg-[#001e3d] hover:bg-[#0d3b66] text-white rounded-lg font-bold transition disabled:opacity-50"
                  >
                    {isSubmitting ? 'Submitting...' : 'Confirm & Dispatch to AICTE'}
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
