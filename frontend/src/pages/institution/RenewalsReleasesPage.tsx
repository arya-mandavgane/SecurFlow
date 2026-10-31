import React, { useState, useEffect } from 'react';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';
import {
  RefreshCw,
  CheckCircle2,
  Calendar,
  Clock,
  GitBranch,
  Layers,
  X,
  ShieldAlert
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface LineageNode {
  id: number;
  fdr_number: string;
  bank_name: string;
  branch: string;
  amount: number;
  issue_date: string;
  maturity_date: string;
  status: string;
  status_display: string;
  depth: number;
  is_current: boolean;
  is_root: boolean;
  renewal_type?: string;
  renewal_type_display?: string;
  reason?: string;
}

export const RenewalsReleasesPage: React.FC = () => {
  const [fdrs, setFdrs] = useState<FDR[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'renewals' | 'calendar' | 'releases'>('renewals');

  // Expiry filter
  const [maturityFilter, setMaturityFilter] = useState<'ALL' | '30' | '60' | '90' | 'EXPIRED'>('ALL');

  // Renewal submit modal
  const [selectedParentFdr, setSelectedParentFdr] = useState<FDR | null>(null);
  const [renewalType, setRenewalType] = useState<'RENEWAL' | 'REPLACEMENT'>('RENEWAL');
  const [newFdrNumber, setNewFdrNumber] = useState<string>('');
  const [bankName, setBankName] = useState<string>('');
  const [branch, setBranch] = useState<string>('');
  const [amount, setAmount] = useState<string>('');
  const [interestRate, setInterestRate] = useState<string>('');
  const [issueDate, setIssueDate] = useState<string>('');
  const [maturityDate, setMaturityDate] = useState<string>('');
  const [reason, setReason] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [renewalSuccess, setRenewalSuccess] = useState<string | null>(null);

  // Lineage chain modal
  const [lineageChain, setLineageChain] = useState<LineageNode[] | null>(null);
  const [lineageLoading, setLineageLoading] = useState<boolean>(false);
  const [activeLineageFdrNum, setActiveLineageFdrNum] = useState<string>('');

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

  const handleOpenRenewalModal = (fdr: FDR) => {
    setSelectedParentFdr(fdr);
    setRenewalType('RENEWAL');
    setNewFdrNumber(`${fdr.fdr_number}-R1`);
    setBankName(fdr.bank_name);
    setBranch(fdr.branch);
    setAmount(String(fdr.amount));
    setInterestRate(fdr.interest_rate ? String(fdr.interest_rate) : '7.00');
    setIssueDate(new Date().toISOString().split('T')[0]);
    // Default maturity 1 year from now
    const d = new Date();
    d.setFullYear(d.getFullYear() + 1);
    setMaturityDate(d.toISOString().split('T')[0]);
    setReason('Mandatory continuous security deposit compliance renewal under AICTE APH regulations');
    setRenewalSuccess(null);
  };

  const handleSubmitRenewal = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParentFdr) return;
    setIsSubmitting(true);
    setRenewalSuccess(null);

    try {
      const payload = {
        original_fdr_id: selectedParentFdr.id,
        renewal_type: renewalType,
        reason,
        fdr_number: newFdrNumber,
        bank_name: bankName,
        branch,
        amount: parseFloat(amount),
        interest_rate: interestRate ? parseFloat(interestRate) : null,
        issue_date: issueDate,
        maturity_date: maturityDate,
        lien_marked_aicte: true,
      };

      const res = await apiClient.post('/renewals/submit/', payload);
      if (res.data?.success) {
        setRenewalSuccess(
          `Renewal deposit #${newFdrNumber} submitted successfully! It is linked to parent FDR #${selectedParentFdr.fdr_number}.`
        );
        setTimeout(() => {
          setSelectedParentFdr(null);
          setRenewalSuccess(null);
          fetchFDRs();
        }, 2000);
      }
    } catch (err: any) {
      alert(err?.response?.data?.error?.message || err?.response?.data?.message || 'Failed to submit renewal.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleViewLineage = async (fdr: FDR) => {
    setActiveLineageFdrNum(fdr.fdr_number);
    setLineageLoading(true);
    setLineageChain(null);
    try {
      const res = await apiClient.get(`/renewals/${fdr.id}/chain/`);
      if (res.data?.success) {
        setLineageChain(res.data.data.lineage);
      }
    } catch (err: any) {
      alert('Failed to load renewal chain: ' + (err?.response?.data?.error?.message || err.message));
    } finally {
      setLineageLoading(false);
    }
  };

  const today = new Date();
  const getDaysLeft = (matDate: string) => {
    const diff = new Date(matDate).getTime() - today.getTime();
    return Math.ceil(diff / (1000 * 60 * 60 * 24));
  };

  // Filter FDRs for renewals and calendar
  const eligibleForRenewal = fdrs.filter((f) =>
    ['ACTIVE', 'EXPIRING_SOON', 'EXPIRED', 'VERIFIED'].includes(f.status)
  );

  const filteredByMaturity = eligibleForRenewal.filter((f) => {
    const days = getDaysLeft(f.maturity_date);
    if (maturityFilter === '30') return days <= 30 && days > 0;
    if (maturityFilter === '60') return days <= 60 && days > 0;
    if (maturityFilter === '90') return days <= 90 && days > 0;
    if (maturityFilter === 'EXPIRED') return days <= 0 || f.status === 'EXPIRED';
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0d3b66]/10 text-[#0d3b66]">
              Continuous Compliance
            </span>
            <span className="text-xs text-slate-500 font-mono">Renewal Chain & Expiry Watch</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">FDR Renewals & Maturity Tracking</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Monitor upcoming deposit maturities, submit linked renewals, and audit full multi-year lineage chains.
          </p>
        </div>

        <button
          onClick={fetchFDRs}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 bg-white px-4 rounded-t-xl">
        <button
          onClick={() => setActiveTab('renewals')}
          className={`py-3.5 px-6 text-xs font-bold border-b-2 flex items-center space-x-2 transition ${
            activeTab === 'renewals'
              ? 'border-[#0d3b66] text-[#0d3b66]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Renewals & Replacement ({eligibleForRenewal.length})</span>
        </button>

        <button
          onClick={() => setActiveTab('calendar')}
          className={`py-3.5 px-6 text-xs font-bold border-b-2 flex items-center space-x-2 transition ${
            activeTab === 'calendar'
              ? 'border-[#0d3b66] text-[#0d3b66]'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          }`}
        >
          <Calendar className="w-3.5 h-3.5" />
          <span>Maturity Radar (30/60/90 Days)</span>
        </button>
      </div>

      {/* Tab 1: Renewals List */}
      {activeTab === 'renewals' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-amber-800 uppercase">Expiring in ≤ 60 Days</p>
                <p className="text-2xl font-bold text-amber-950 mt-0.5">
                  {eligibleForRenewal.filter((f) => getDaysLeft(f.maturity_date) <= 60 && getDaysLeft(f.maturity_date) > 0).length}
                </p>
                <p className="text-[11px] text-amber-700 mt-0.5">Action required to avoid compliance gap</p>
              </div>
              <Clock className="w-8 h-8 text-amber-600" />
            </div>

            <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-red-800 uppercase">Expired Deposits</p>
                <p className="text-2xl font-bold text-red-950 mt-0.5">
                  {eligibleForRenewal.filter((f) => getDaysLeft(f.maturity_date) <= 0 || f.status === 'EXPIRED').length}
                </p>
                <p className="text-[11px] text-red-700 mt-0.5">Replacement deposit mandatory immediately</p>
              </div>
              <ShieldAlert className="w-8 h-8 text-red-600" />
            </div>

            <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex items-center justify-between">
              <div>
                <p className="text-xs font-semibold text-blue-800 uppercase">Active Portfolio</p>
                <p className="text-2xl font-bold text-blue-950 mt-0.5">{eligibleForRenewal.length}</p>
                <p className="text-[11px] text-blue-700 mt-0.5">Deposits under surveillance</p>
              </div>
              <Layers className="w-8 h-8 text-blue-600" />
            </div>
          </div>

          {/* FDR List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            {loading ? (
              <div className="p-12 text-center text-xs text-slate-500">Loading FDRs...</div>
            ) : eligibleForRenewal.length === 0 ? (
              <div className="p-12 text-center text-xs text-slate-500">No active or expiring FDRs found.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse text-xs">
                  <thead>
                    <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase">
                      <th className="py-3 px-4">FDR Identifier</th>
                      <th className="py-3 px-4">Bank & Branch</th>
                      <th className="py-3 px-4 text-right">Amount (INR)</th>
                      <th className="py-3 px-4">Maturity Date</th>
                      <th className="py-3 px-4">Status & Urgency</th>
                      <th className="py-3 px-4 text-center">Renewal Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {eligibleForRenewal.map((fdr) => {
                      const daysLeft = getDaysLeft(fdr.maturity_date);
                      return (
                        <tr key={fdr.id} className="hover:bg-slate-50 transition">
                          <td className="py-3 px-4">
                            <Link to={`/fdrs/${fdr.id}`} className="font-bold text-[#0d3b66] hover:underline">
                              {fdr.fdr_number}
                            </Link>
                            {fdr.parent_fdr_number && (
                              <span className="text-[10px] text-slate-400 block font-mono">
                                Prior: #{fdr.parent_fdr_number}
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-800">{fdr.bank_name}</div>
                            <div className="text-[11px] text-slate-500">{fdr.branch}</div>
                          </td>
                          <td className="py-3 px-4 text-right font-bold text-slate-900">
                            ₹{Number(fdr.amount).toLocaleString('en-IN')}
                          </td>
                          <td className="py-3 px-4">
                            <div className="font-medium text-slate-800">{fdr.maturity_date}</div>
                            <span
                              className={`text-[10px] font-semibold ${
                                daysLeft <= 0
                                  ? 'text-red-600'
                                  : daysLeft <= 30
                                  ? 'text-red-500'
                                  : daysLeft <= 90
                                  ? 'text-amber-600'
                                  : 'text-slate-500'
                              }`}
                            >
                              {daysLeft <= 0 ? 'Overdue' : `${daysLeft} days remaining`}
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                fdr.status === 'EXPIRED'
                                  ? 'bg-red-100 text-red-800'
                                  : fdr.status === 'EXPIRING_SOON'
                                  ? 'bg-amber-100 text-amber-800'
                                  : 'bg-emerald-100 text-emerald-800'
                              }`}
                            >
                              {fdr.status_display}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center justify-center space-x-2">
                              <button
                                onClick={() => handleOpenRenewalModal(fdr)}
                                className="px-3 py-1.5 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded text-xs font-semibold shadow-xs transition"
                              >
                                Submit Renewal
                              </button>
                              <button
                                onClick={() => handleViewLineage(fdr)}
                                className="p-1.5 text-slate-600 hover:text-[#0d3b66] bg-slate-100 hover:bg-slate-200 rounded transition"
                                title="View Multi-Year Renewal Chain"
                              >
                                <GitBranch className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Maturity Calendar / Radar */}
      {activeTab === 'calendar' && (
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 border-b border-slate-100 pb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900">Maturity Radar & Forecast Timeline</h2>
              <p className="text-xs text-slate-500">
                Categorized time horizons for upcoming maturities scheduled across the calendar year.
              </p>
            </div>

            {/* Quick Filter Buttons */}
            <div className="flex flex-wrap items-center gap-1.5 text-xs">
              {(['ALL', '30', '60', '90', 'EXPIRED'] as const).map((filter) => (
                <button
                  key={filter}
                  onClick={() => setMaturityFilter(filter)}
                  className={`px-3 py-1.5 rounded-lg font-semibold transition ${
                    maturityFilter === filter
                      ? 'bg-[#0d3b66] text-white shadow-xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {filter === 'ALL'
                    ? 'All Upcoming'
                    : filter === 'EXPIRED'
                    ? 'Already Expired'
                    : `≤ ${filter} Days`}
                </button>
              ))}
            </div>
          </div>

          {/* Cards for Filtered Items */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredByMaturity.map((fdr) => {
              const days = getDaysLeft(fdr.maturity_date);
              const isUrgent = days <= 30;
              return (
                <div
                  key={fdr.id}
                  className={`p-4 rounded-xl border transition flex flex-col justify-between space-y-3 ${
                    isUrgent
                      ? 'border-red-300 bg-red-50/40'
                      : days <= 90
                      ? 'border-amber-300 bg-amber-50/30'
                      : 'border-slate-200 bg-white'
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-[#0d3b66]">{fdr.fdr_number}</span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                          days <= 0
                            ? 'bg-red-200 text-red-900'
                            : days <= 30
                            ? 'bg-red-100 text-red-800'
                            : days <= 90
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-blue-100 text-blue-800'
                        }`}
                      >
                        {days <= 0 ? 'EXPIRED' : `${days} DAYS LEFT`}
                      </span>
                    </div>

                    <p className="text-sm font-bold text-slate-900">
                      ₹{Number(fdr.amount).toLocaleString('en-IN')}
                    </p>
                    <p className="text-xs text-slate-600">
                      {fdr.bank_name} • {fdr.branch}
                    </p>
                    <p className="text-[11px] text-slate-500 font-mono">
                      Matures: {fdr.maturity_date}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-slate-200/60 flex items-center justify-between">
                    <button
                      onClick={() => handleViewLineage(fdr)}
                      className="text-xs text-slate-600 hover:text-slate-900 flex items-center space-x-1"
                    >
                      <GitBranch className="w-3.5 h-3.5" />
                      <span>Lineage</span>
                    </button>
                    <button
                      onClick={() => handleOpenRenewalModal(fdr)}
                      className="px-2.5 py-1 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded text-xs font-semibold transition"
                    >
                      Renew Deposit
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Renewal Submission Modal */}
      {selectedParentFdr && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-slate-200">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h2 className="text-base font-bold text-slate-900">Submit Renewal / Replacement FDR</h2>
                <p className="text-xs text-slate-500 font-mono">
                  Linking to Parent FDR #{selectedParentFdr.fdr_number} (₹{Number(selectedParentFdr.amount).toLocaleString('en-IN')})
                </p>
              </div>
              <button
                onClick={() => setSelectedParentFdr(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmitRenewal} className="p-6 overflow-y-auto space-y-4 flex-1 text-xs">
              {renewalSuccess && (
                <div className="bg-emerald-50 border border-emerald-200 text-emerald-800 p-3 rounded-lg font-semibold flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>{renewalSuccess}</span>
                </div>
              )}

              {/* Renewal Type Radio */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Renewal Classification</label>
                <div className="grid grid-cols-2 gap-2">
                  <label
                    className={`p-2.5 rounded-lg border cursor-pointer flex items-center space-x-2 ${
                      renewalType === 'RENEWAL' ? 'border-[#0d3b66] bg-blue-50/50' : 'border-slate-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="renewal_type"
                      checked={renewalType === 'RENEWAL'}
                      onChange={() => setRenewalType('RENEWAL')}
                    />
                    <div>
                      <p className="font-bold text-slate-900">Direct Renewal</p>
                      <p className="text-[10px] text-slate-500">Same bank rollover</p>
                    </div>
                  </label>

                  <label
                    className={`p-2.5 rounded-lg border cursor-pointer flex items-center space-x-2 ${
                      renewalType === 'REPLACEMENT' ? 'border-[#0d3b66] bg-blue-50/50' : 'border-slate-200'
                    }`}
                  >
                    <input
                      type="radio"
                      name="renewal_type"
                      checked={renewalType === 'REPLACEMENT'}
                      onChange={() => setRenewalType('REPLACEMENT')}
                    />
                    <div>
                      <p className="font-bold text-slate-900">Replacement FDR</p>
                      <p className="text-[10px] text-slate-500">New bank / new receipt</p>
                    </div>
                  </label>
                </div>
              </div>

              {/* New FDR Number */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">New FDR Certificate Number *</label>
                <input
                  type="text"
                  required
                  value={newFdrNumber}
                  onChange={(e) => setNewFdrNumber(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded focus:ring-1 focus:ring-[#0d3b66]"
                />
              </div>

              {/* Bank & Branch */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Issuing Bank *</label>
                  <input
                    type="text"
                    required
                    value={bankName}
                    onChange={(e) => setBankName(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Bank Branch *</label>
                  <input
                    type="text"
                    required
                    value={branch}
                    onChange={(e) => setBranch(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
              </div>

              {/* Amount & Interest */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Deposit Amount (INR) *</label>
                  <input
                    type="number"
                    step="0.01"
                    required
                    value={amount}
                    onChange={(e) => setAmount(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Interest Rate (%)</label>
                  <input
                    type="number"
                    step="0.01"
                    value={interestRate}
                    onChange={(e) => setInterestRate(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
              </div>

              {/* Dates */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Renewal / Issue Date *</label>
                  <input
                    type="date"
                    required
                    value={issueDate}
                    onChange={(e) => setIssueDate(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">New Maturity Date *</label>
                  <input
                    type="date"
                    required
                    value={maturityDate}
                    onChange={(e) => setMaturityDate(e.target.value)}
                    className="w-full p-2 border border-slate-300 rounded"
                  />
                </div>
              </div>

              {/* Reason */}
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Renewal Justification / Notes</label>
                <textarea
                  rows={2}
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  className="w-full p-2 border border-slate-300 rounded"
                />
              </div>

              <div className="pt-3 border-t border-slate-200 flex items-center justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setSelectedParentFdr(null)}
                  className="px-4 py-2 border border-slate-300 rounded text-slate-700 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded font-bold shadow-xs disabled:opacity-50"
                >
                  {isSubmitting ? 'Linking Renewal...' : 'Submit Renewal Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Visual Renewal Lineage Chain Modal */}
      {lineageChain && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[85vh] overflow-hidden flex flex-col shadow-2xl border border-slate-200">
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-2">
                <GitBranch className="w-5 h-5 text-[#0d3b66]" />
                <div>
                  <h2 className="text-base font-bold text-slate-900">Multi-Year Deposit Lineage Chain</h2>
                  <p className="text-xs text-slate-500 font-mono">Traced for #{activeLineageFdrNum}</p>
                </div>
              </div>
              <button
                onClick={() => setLineageChain(null)}
                className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 flex-1">
              {lineageLoading ? (
                <div className="py-8 text-center text-xs text-slate-500">Tracing ancestry tree...</div>
              ) : (
                <div className="relative border-l-2 border-[#0d3b66]/30 ml-4 pl-6 space-y-6">
                  {lineageChain.map((node) => (
                    <div key={node.id} className="relative">
                      {/* Node Bullet */}
                      <div
                        className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-2 bg-white ${
                          node.is_current
                            ? 'border-[#0d3b66] ring-4 ring-[#0d3b66]/20'
                            : 'border-slate-400'
                        }`}
                      />

                      <div
                        className={`p-4 rounded-xl border text-xs transition ${
                          node.is_current
                            ? 'bg-blue-50/60 border-[#0d3b66]'
                            : 'bg-white border-slate-200'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-2">
                            <span className="font-bold text-sm text-[#0d3b66]">
                              {node.fdr_number}
                            </span>
                            {node.is_root && (
                              <span className="text-[10px] bg-slate-100 text-slate-700 px-1.5 py-0.2 rounded font-mono">
                                Original Deposit
                              </span>
                            )}
                            {node.is_current && (
                              <span className="text-[10px] bg-[#0d3b66] text-white px-1.5 py-0.2 rounded font-semibold">
                                Viewing
                              </span>
                            )}
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                            {node.status_display}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 mt-2 text-slate-600 text-[11px]">
                          <div>
                            <span className="text-slate-400">Bank:</span> {node.bank_name} ({node.branch})
                          </div>
                          <div>
                            <span className="text-slate-400">Principal:</span> ₹
                            {node.amount.toLocaleString('en-IN')}
                          </div>
                          <div>
                            <span className="text-slate-400">Issued:</span> {node.issue_date}
                          </div>
                          <div>
                            <span className="text-slate-400">Matures:</span> {node.maturity_date}
                          </div>
                        </div>

                        {node.renewal_type_display && (
                          <div className="mt-2 pt-2 border-t border-slate-100 text-[11px] text-slate-500">
                            <strong>{node.renewal_type_display}:</strong> {node.reason || 'Annual renewal'}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
