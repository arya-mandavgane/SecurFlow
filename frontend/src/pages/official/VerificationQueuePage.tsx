import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  AlertTriangle,
  Clock,
  Search,
  CheckCircle2,
  Calendar,
  ArrowRight,
  RefreshCw,
  FileText
} from 'lucide-react';
import { apiClient } from '../../api/client';

interface QueueItem {
  id: number;
  fdr_number: string;
  institution_id: number;
  institution_name: string;
  institution_aicte_id: string;
  state: string;
  bank_name: string;
  branch: string;
  amount: number;
  issue_date: string;
  maturity_date: string;
  days_to_maturity: number;
  status: string;
  status_display: string;
  discrepancy_count: number;
  has_critical_discrepancy: boolean;
  priority: 'HIGH' | 'MEDIUM' | 'LOW';
  priority_score: number;
  has_document: boolean;
  created_at: string;
}

export const VerificationQueuePage: React.FC = () => {
  const [items, setItems] = useState<QueueItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [priorityFilter, setPriorityFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const fetchQueue = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (priorityFilter && priorityFilter !== 'ALL') params.append('priority', priorityFilter);
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);

      const res = await apiClient.get(`/fdrs/verification-queue/?${params.toString()}`);
      if (res.data?.success) {
        setItems(res.data.data);
      }
    } catch {
      // non-fatal
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
  }, [priorityFilter, statusFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchQueue();
  };

  const highPriorityCount = items.filter((i) => i.priority === 'HIGH').length;
  const criticalCount = items.filter((i) => i.has_critical_discrepancy).length;
  const urgentMaturityCount = items.filter((i) => i.days_to_maturity <= 30).length;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
              Scrutiny Pipeline
            </span>
            <span className="text-xs text-slate-500 font-mono">Prioritized Queue</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Official Verification Queue</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Smart-ranked queue prioritizing flagged OCR discrepancies and nearest maturity deadlines.
          </p>
        </div>

        <button
          onClick={fetchQueue}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh Queue</span>
        </button>
      </div>

      {/* Queue Stat Summary Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-red-50 border border-red-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-red-800 uppercase tracking-wider">Critical / High Priority</p>
            <p className="text-2xl font-bold text-red-950 mt-0.5">{highPriorityCount}</p>
            <p className="text-xs text-red-700 mt-0.5">{criticalCount} with severe OCR mismatches</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-red-100 text-red-700 flex items-center justify-center">
            <ShieldAlert className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-amber-800 uppercase tracking-wider">Maturity Urgency (≤30 Days)</p>
            <p className="text-2xl font-bold text-amber-950 mt-0.5">{urgentMaturityCount}</p>
            <p className="text-xs text-amber-700 mt-0.5">Expiring deposits requiring fast action</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-amber-100 text-amber-700 flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-blue-50 border border-blue-200 p-4 rounded-xl flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold text-blue-800 uppercase tracking-wider">Total in Scrutiny</p>
            <p className="text-2xl font-bold text-blue-950 mt-0.5">{items.length}</p>
            <p className="text-xs text-blue-700 mt-0.5">Awaiting official approval decision</p>
          </div>
          <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center">
            <FileText className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-col lg:flex-row gap-3 items-stretch lg:items-center justify-between">
          {/* Search form */}
          <form onSubmit={handleSearchSubmit} className="flex-1 flex gap-2">
            <div className="relative flex-1">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search FDR number, Institute name, AICTE ID, Bank..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0d3b66]"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 bg-[#0d3b66] hover:bg-[#001e3d] text-white text-sm font-medium rounded-lg transition"
            >
              Search
            </button>
          </form>

          {/* Quick Filter Selects */}
          <div className="flex flex-wrap items-center gap-2">
            {/* Priority Selector */}
            <div className="flex items-center space-x-1 border border-slate-200 rounded-lg p-1 bg-slate-50 text-xs">
              <span className="text-slate-500 font-semibold px-2">Priority:</span>
              {(['ALL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((p) => (
                <button
                  key={p}
                  onClick={() => setPriorityFilter(p)}
                  className={`px-2.5 py-1 rounded font-medium transition ${
                    priorityFilter === p
                      ? 'bg-[#0d3b66] text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Status Dropdown */}
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="text-xs border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-1 focus:ring-[#0d3b66]"
            >
              <option value="">All Scrutiny Statuses</option>
              <option value="SUBMITTED">Submitted</option>
              <option value="UNDER_REVIEW">Under Review</option>
              <option value="NEEDS_CLARIFICATION">Needs Clarification</option>
            </select>
          </div>
        </div>
      </div>

      {/* Queue Items Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        {loading ? (
          <div className="p-12 text-center space-y-3">
            <RefreshCw className="w-8 h-8 text-[#0d3b66] animate-spin mx-auto" />
            <p className="text-sm text-slate-500 font-medium">Loading prioritized queue items...</p>
          </div>
        ) : items.length === 0 ? (
          <div className="p-12 text-center space-y-3">
            <CheckCircle2 className="w-12 h-12 text-emerald-500 mx-auto" />
            <h3 className="text-base font-bold text-slate-900">Verification Queue is Clear</h3>
            <p className="text-sm text-slate-500 max-w-md mx-auto">
              No pending FDR submissions match your active filter criteria. Great job maintaining zero compliance backlog!
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">Priority & Status</th>
                  <th className="py-3 px-4">FDR Identifier</th>
                  <th className="py-3 px-4">Institution</th>
                  <th className="py-3 px-4">Bank & Branch</th>
                  <th className="py-3 px-4 text-right">Amount (INR)</th>
                  <th className="py-3 px-4">Maturity Urgency</th>
                  <th className="py-3 px-4">AI-OCR Check</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/80 transition">
                    {/* Priority & Status */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex flex-col space-y-1">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold w-fit ${
                            item.priority === 'HIGH'
                              ? 'bg-red-100 text-red-800 border border-red-200'
                              : item.priority === 'MEDIUM'
                              ? 'bg-amber-100 text-amber-800 border border-amber-200'
                              : 'bg-slate-100 text-slate-700'
                          }`}
                        >
                          {item.priority === 'HIGH' && (
                            <span className="w-1.5 h-1.5 rounded-full bg-red-600 mr-1.5 animate-pulse" />
                          )}
                          {item.priority} PRIORITY
                        </span>
                        <span className="text-[11px] text-slate-500 font-medium">
                          {item.status_display}
                        </span>
                      </div>
                    </td>

                    {/* FDR Number */}
                    <td className="py-3 px-4">
                      <Link
                        to={`/official/verify/${item.id}`}
                        className="font-bold text-[#0d3b66] hover:underline flex items-center space-x-1"
                      >
                        <span>{item.fdr_number}</span>
                      </Link>
                      <span className="text-[10px] text-slate-400">
                        Lodged: {new Date(item.created_at).toLocaleDateString('en-IN')}
                      </span>
                    </td>

                    {/* Institution */}
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 truncate max-w-[200px]" title={item.institution_name}>
                        {item.institution_name}
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono">
                        {item.institution_aicte_id} • {item.state}
                      </div>
                    </td>

                    {/* Bank */}
                    <td className="py-3 px-4">
                      <div className="font-medium text-slate-800">{item.bank_name}</div>
                      <div className="text-[11px] text-slate-500 truncate max-w-[150px]">{item.branch}</div>
                    </td>

                    {/* Amount */}
                    <td className="py-3 px-4 text-right whitespace-nowrap">
                      <span className="font-bold text-slate-900 text-sm">
                        ₹{item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                      </span>
                    </td>

                    {/* Maturity Urgency */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      <div className="flex items-center space-x-1.5">
                        <Calendar className="w-3.5 h-3.5 text-slate-400" />
                        <span className="font-medium text-slate-700">{item.maturity_date}</span>
                      </div>
                      <span
                        className={`text-[10px] font-semibold ${
                          item.days_to_maturity <= 30
                            ? 'text-red-600'
                            : item.days_to_maturity <= 90
                            ? 'text-amber-600'
                            : 'text-slate-500'
                        }`}
                      >
                        {item.days_to_maturity > 0
                          ? `in ${item.days_to_maturity} days`
                          : `${Math.abs(item.days_to_maturity)} days overdue`}
                      </span>
                    </td>

                    {/* AI-OCR Check */}
                    <td className="py-3 px-4 whitespace-nowrap">
                      {item.discrepancy_count > 0 ? (
                        <div className="flex items-center space-x-1 text-red-600 font-semibold">
                          <AlertTriangle className="w-3.5 h-3.5" />
                          <span>{item.discrepancy_count} Issue{item.discrepancy_count > 1 ? 's' : ''}</span>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-1 text-emerald-600 font-medium">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Match OK</span>
                        </div>
                      )}
                    </td>

                    {/* Action */}
                    <td className="py-3 px-4 text-center whitespace-nowrap">
                      <Link
                        to={`/official/verify/${item.id}`}
                        className="inline-flex items-center space-x-1 px-3 py-1.5 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded-lg text-xs font-semibold shadow-xs transition"
                      >
                        <span>Smart Verify</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
