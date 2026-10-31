import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { apiClient } from '../../api/client';
import { FDR } from '../../types';
import { useAuth } from '../../context/AuthContext';
import {
  ShieldAlert,
  Clock,
  CheckCircle2,
  AlertCircle,
  PlusCircle,
  ArrowRight,
  TrendingUp,
  FileCheck,
  Building
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [fdrs, setFdrs] = useState<FDR[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetchFDRs();
  }, []);

  const fetchFDRs = async () => {
    try {
      setLoading(true);
      const res = await apiClient.get('/fdrs/');
      setFdrs(res.data.results || []);
    } catch (err) {
      console.error('Error fetching dashboard FDRs', err);
    } finally {
      setLoading(false);
    }
  };

  // KPIs
  const totalFdrs = fdrs.length;
  const verifiedFdrs = fdrs.filter((f) => ['VERIFIED', 'ACTIVE'].includes(f.status));
  const pendingFdrs = fdrs.filter((f) => ['SUBMITTED', 'UNDER_REVIEW'].includes(f.status));
  const clarificationFdrs = fdrs.filter((f) => f.status === 'NEEDS_CLARIFICATION');
  const expiringSoonFdrs = fdrs.filter((f) => f.status === 'EXPIRING_SOON');

  const totalValue = verifiedFdrs.reduce((acc, curr) => acc + Number(curr.amount || 0), 0);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'VERIFIED':
      case 'ACTIVE':
        return 'bg-emerald-100 text-emerald-800 border-emerald-300';
      case 'UNDER_REVIEW':
      case 'SUBMITTED':
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case 'NEEDS_CLARIFICATION':
        return 'bg-amber-100 text-amber-800 border-amber-300 animate-pulse';
      case 'EXPIRING_SOON':
        return 'bg-orange-100 text-orange-800 border-orange-300';
      case 'EXPIRED':
      case 'REJECTED':
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300';
    }
  };

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-[#001e3d] via-[#0d3b66] to-[#001e3d] rounded-2xl p-6 sm:p-8 text-white shadow-md relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2 text-xs text-[#e09f3e] font-semibold tracking-wider uppercase">
              <Building className="w-4 h-4" />
              <span>{user?.institution?.name || 'Institution Portal'}</span>
              {user?.institution?.aicte_id && (
                <span className="bg-[#e09f3e]/20 text-[#e09f3e] px-2 py-0.5 rounded text-[11px] font-mono">
                  AICTE ID: {user.institution.aicte_id}
                </span>
              )}
            </div>
            <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">
              FDR & Security Deposit Overview
            </h1>
            <p className="text-sm text-slate-300 max-w-xl">
              Track active deposits, complete verification responses, and manage renewal timelines under AICTE compliance.
            </p>
          </div>

          <Link
            to="/fdrs/submit"
            className="inline-flex items-center space-x-2 bg-[#e09f3e] hover:bg-[#c98a2f] text-[#001e3d] font-bold px-5 py-3 rounded-xl shadow-lg transition duration-150 self-start md:self-auto"
          >
            <PlusCircle className="w-5 h-5" />
            <span>Submit New FDR</span>
          </Link>
        </div>
      </div>

      {/* Urgent Clarification Alert If Any */}
      {clarificationFdrs.length > 0 && (
        <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-r-xl shadow-sm flex items-start justify-between">
          <div className="flex items-start space-x-3">
            <AlertCircle className="w-5 h-5 text-amber-600 mt-0.5 flex-shrink-0" />
            <div>
              <h2 className="text-sm font-bold text-amber-900">Action Required: Official Clarifications Pending</h2>
              <p className="text-xs text-amber-800 mt-0.5">
                AICTE officials have requested clarifications on {clarificationFdrs.length} FDR submission(s). Please review the remarks and re-submit supporting documents.
              </p>
            </div>
          </div>
          <Link
            to={`/fdrs/${clarificationFdrs[0].id}`}
            className="text-xs font-semibold text-amber-900 bg-amber-200/80 hover:bg-amber-300 px-3 py-1.5 rounded-lg transition"
          >
            Review & Respond &rarr;
          </Link>
        </div>
      )}

      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total FDRs</span>
            <span className="p-2 bg-blue-50 text-[#0d3b66] rounded-lg">
              <FileCheck className="w-5 h-5" />
            </span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 mt-2">{loading ? '...' : totalFdrs}</div>
          <div className="text-xs text-slate-500 mt-1">Submitted under AICTE portal</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Pledged Deposit Value</span>
            <span className="p-2 bg-emerald-50 text-emerald-600 rounded-lg">
              <TrendingUp className="w-5 h-5" />
            </span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 mt-2">
            {loading ? '...' : `₹${(totalValue / 100000).toFixed(2)} Lakhs`}
          </div>
          <div className="text-xs text-emerald-600 font-medium mt-1">Lien in favour of AICTE</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Under Verification</span>
            <span className="p-2 bg-amber-50 text-amber-600 rounded-lg">
              <Clock className="w-5 h-5" />
            </span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 mt-2">{loading ? '...' : pendingFdrs.length}</div>
          <div className="text-xs text-slate-500 mt-1">With AICTE Approval Committee</div>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Expiring / Action</span>
            <span className="p-2 bg-orange-50 text-orange-600 rounded-lg">
              <ShieldAlert className="w-5 h-5" />
            </span>
          </div>
          <div className="text-2xl font-extrabold text-slate-900 mt-2">
            {loading ? '...' : expiringSoonFdrs.length + clarificationFdrs.length}
          </div>
          <div className="text-xs text-orange-600 font-medium mt-1">Maturing or pending response</div>
        </div>
      </div>

      {/* Recent Submissions Section */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-800">Recent Fixed Deposit Receipts</h2>
            <p className="text-xs text-slate-500">Live records submitted by your institution</p>
          </div>
          <Link
            to="/fdrs"
            className="text-xs font-semibold text-[#0d3b66] hover:text-[#001e3d] flex items-center space-x-1"
          >
            <span>View All FDRs</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          {loading ? (
            <div className="p-8 text-center text-sm text-slate-500">Loading FDR records...</div>
          ) : fdrs.length === 0 ? (
            <div className="p-8 text-center">
              <CheckCircle2 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-sm font-semibold text-slate-700">No FDR records found</p>
              <p className="text-xs text-slate-500 mt-1">Submit your first FDR using the button above.</p>
            </div>
          ) : (
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold uppercase tracking-wider">
                  <th className="py-3 px-4">FDR Number</th>
                  <th className="py-3 px-4">Bank & Branch</th>
                  <th className="py-3 px-4">Amount (₹)</th>
                  <th className="py-3 px-4">Maturity Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {fdrs.slice(0, 5).map((fdr) => (
                  <tr key={fdr.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4 font-mono font-medium text-slate-900">{fdr.fdr_number}</td>
                    <td className="py-3.5 px-4">
                      <div className="font-medium text-slate-800">{fdr.bank_name}</div>
                      <div className="text-[11px] text-slate-500">{fdr.branch || 'Main Branch'}</div>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-slate-900">
                      ₹{Number(fdr.amount).toLocaleString('en-IN')}
                    </td>
                    <td className="py-3.5 px-4 text-slate-600">{fdr.maturity_date}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-semibold border ${getStatusBadge(fdr.status)}`}>
                        {fdr.status_display || fdr.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        to={`/fdrs/${fdr.id}`}
                        className="text-xs font-semibold text-[#0d3b66] hover:underline"
                      >
                        View &rarr;
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
