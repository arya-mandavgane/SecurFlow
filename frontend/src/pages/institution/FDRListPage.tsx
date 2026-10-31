import React, { useState, useEffect } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';
import { Search, PlusCircle, Filter, FileText, ExternalLink } from 'lucide-react';

export const FDRListPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [fdrs, setFdrs] = useState<FDR[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>(searchParams.get('status') || 'ALL');

  useEffect(() => {
    fetchFDRs();
  }, [statusFilter]);

  const fetchFDRs = async () => {
    try {
      setLoading(true);
      let url = '/fdrs/';
      const params: string[] = [];

      if (statusFilter && statusFilter !== 'ALL') {
        params.push(`status=${statusFilter}`);
      }
      if (searchTerm) {
        params.push(`search=${encodeURIComponent(searchTerm)}`);
      }

      if (params.length > 0) {
        url += `?${params.join('&')}`;
      }

      const res = await apiClient.get(url);
      setFdrs(res.data.results || []);
    } catch (err) {
      console.error('Error fetching FDRs', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchFDRs();
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
      case 'ACTIVE':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      case 'UNDER_REVIEW':
      case 'SUBMITTED':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'NEEDS_CLARIFICATION':
        return 'bg-amber-100 text-amber-900 border-amber-300 font-bold animate-pulse';
      case 'EXPIRING_SOON':
        return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'EXPIRED':
      case 'REJECTED':
        return 'bg-red-100 text-red-800 border-red-200';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-200';
    }
  };

  const statuses = [
    { label: 'All Deposits', value: 'ALL' },
    { label: 'Submitted', value: 'SUBMITTED' },
    { label: 'Under Review', value: 'UNDER_REVIEW' },
    { label: 'Clarification Needed', value: 'NEEDS_CLARIFICATION' },
    { label: 'Verified', value: 'VERIFIED' },
    { label: 'Active', value: 'ACTIVE' },
    { label: 'Expiring Soon', value: 'EXPIRING_SOON' },
    { label: 'Expired', value: 'EXPIRED' },
  ];

  return (
    <div className="space-y-6">
      {/* Title & Submit Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-[#001e3d]">Institutional Fixed Deposit Records</h1>
          <p className="text-xs text-slate-500 mt-1">Complete register of FDRs pledged under AICTE regulations</p>
        </div>
        <Link
          to="/fdrs/submit"
          className="inline-flex items-center space-x-2 bg-[#001e3d] hover:bg-[#0d3b66] text-white px-4 py-2.5 rounded-lg text-xs font-semibold shadow transition"
        >
          <PlusCircle className="w-4 h-4" />
          <span>Submit New FDR</span>
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by FDR number, bank name, or approval cycle..."
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-300 text-xs focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
            />
          </div>
          <button
            type="submit"
            className="bg-slate-800 hover:bg-slate-900 text-white px-4 py-2 rounded-lg text-xs font-medium transition"
          >
            Search
          </button>
        </form>

        {/* Filter Pills */}
        <div className="flex items-center space-x-2 overflow-x-auto pb-1 text-xs scrollbar-thin">
          <span className="text-slate-400 text-[11px] font-semibold uppercase flex items-center space-x-1 mr-1">
            <Filter className="w-3 h-3" />
            <span>Filter:</span>
          </span>
          {statuses.map((item) => (
            <button
              key={item.value}
              onClick={() => setStatusFilter(item.value)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition ${
                statusFilter === item.value
                  ? 'bg-[#001e3d] text-white font-semibold'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-12 text-center text-sm text-slate-500">Loading FDR register...</div>
          ) : fdrs.length === 0 ? (
            <div className="p-12 text-center space-y-2">
              <FileText className="w-10 h-10 text-slate-300 mx-auto" />
              <div className="text-sm font-semibold text-slate-700">No FDRs match the selected filter</div>
              <p className="text-xs text-slate-400">Try adjusting your search criteria or submit a new FDR.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase tracking-wider">
                  <th className="py-3.5 px-4">FDR Number</th>
                  <th className="py-3.5 px-4">Bank Name & Branch</th>
                  <th className="py-3.5 px-4">Amount (₹)</th>
                  <th className="py-3.5 px-4">Issue Date</th>
                  <th className="py-3.5 px-4">Maturity Date</th>
                  <th className="py-3.5 px-4">Lien Status</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {fdrs.map((fdr) => (
                  <tr key={fdr.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-900">
                      <Link to={`/fdrs/${fdr.id}`} className="hover:text-[#0d3b66] hover:underline">
                        {fdr.fdr_number}
                      </Link>
                    </td>
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-800">{fdr.bank_name}</div>
                      <div className="text-[11px] text-slate-500">{fdr.branch || 'Main Branch'}</div>
                    </td>
                    <td className="py-3.5 px-4 font-bold text-slate-900">
                      ₹{Number(fdr.amount).toLocaleString('en-IN')}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{fdr.issue_date}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">{fdr.maturity_date}</td>
                    <td className="py-3.5 px-4">
                      {fdr.lien_marked_aicte ? (
                        <span className="text-emerald-700 font-semibold">AICTE Pledged</span>
                      ) : (
                        <span className="text-red-600 font-semibold">No Lien</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border ${getStatusBadge(fdr.status)}`}>
                        {fdr.status_display || fdr.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/fdrs/${fdr.id}`}
                        className="inline-flex items-center space-x-1 text-xs font-semibold text-[#001e3d] hover:text-[#0d3b66] hover:underline"
                      >
                        <span>Details</span>
                        <ExternalLink className="w-3 h-3" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
};
