import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Clock,
  AlertTriangle,
  Landmark,
  CheckCircle2,
  ArrowRight,
  Activity,
  CalendarClock,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '../../api/client';

interface OfficialStats {
  kpis: {
    total_fdrs: number;
    total_deposit_value: number;
    pending_verification: number;
    verified: number;
    expiring_30_days: number;
    expiring_60_days: number;
    expiring_90_days: number;
    expired: number;
    release_requests: number;
  };
  status_distribution: Array<{
    status: string;
    label: string;
    count: number;
    total_amount: number;
  }>;
  state_distribution: Array<{
    state: string;
    count: number;
    total_amount: number;
  }>;
  bank_distribution: Array<{
    bank: string;
    count: number;
    total_amount: number;
  }>;
  recent_activity: Array<{
    id: number;
    actor_name: string;
    action: string;
    action_display: string;
    entity_type: string;
    entity_id: string;
    timestamp: string;
    after_state: Record<string, any>;
  }>;
}

export const OfficialDashboardPage: React.FC = () => {
  const [stats, setStats] = useState<OfficialStats | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get('/fdrs/official-stats/');
      if (res.data?.success) {
        setStats(res.data.data);
      }
    } catch (err: any) {
      setError(err?.response?.data?.error?.message || 'Failed to load official dashboard data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatCurrency = (val: number) => {
    if (val >= 10000000) {
      return `₹${(val / 10000000).toFixed(2)} Cr`;
    }
    if (val >= 100000) {
      return `₹${(val / 100000).toFixed(2)} Lakh`;
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] space-y-4">
        <RefreshCw className="w-8 h-8 text-[#0d3b66] animate-spin" />
        <p className="text-slate-600 font-medium text-sm">Aggregating system-wide FDR data & metrics...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 p-6 rounded-xl flex flex-col items-center space-y-3">
        <AlertTriangle className="w-8 h-8 text-red-600" />
        <p className="font-semibold">{error || 'Unable to retrieve analytics.'}</p>
        <button
          onClick={fetchStats}
          className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 transition"
        >
          Retry
        </button>
      </div>
    );
  }

  const { kpis, status_distribution, state_distribution, bank_distribution, recent_activity } = stats;

  return (
    <div className="space-y-6">
      {/* Top Banner Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl shadow-sm border border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0d3b66]/10 text-[#0d3b66]">
              AICTE Headquarters
            </span>
            <span className="text-xs text-slate-500 font-mono">Live Monitoring</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Official Overview & Control Panel</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Real-time compliance surveillance, maturity forecasting, and FDR verification pipeline.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchStats}
            className="flex items-center space-x-2 px-3 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Refresh</span>
          </button>
          <Link
            to="/official/verification-queue"
            className="flex items-center space-x-2 px-4 py-2 bg-[#0d3b66] hover:bg-[#001e3d] text-white rounded-lg text-sm font-medium shadow-sm transition"
          >
            <span>Verification Queue</span>
            {kpis.pending_verification > 0 && (
              <span className="bg-[#e09f3e] text-slate-950 font-bold px-2 py-0.5 rounded-full text-xs">
                {kpis.pending_verification}
              </span>
            )}
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>

      {/* Primary KPI Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total FDRs */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Active Corpus</p>
            <p className="text-2xl font-bold text-slate-900">{formatCurrency(kpis.total_deposit_value)}</p>
            <p className="text-xs text-slate-600">{kpis.total_fdrs} total FDRs lodged in system</p>
          </div>
          <div className="w-12 h-12 bg-blue-50 text-[#0d3b66] rounded-xl flex items-center justify-center font-bold">
            <Landmark className="w-6 h-6" />
          </div>
        </div>

        {/* Pending Verification */}
        <Link
          to="/official/verification-queue"
          className="bg-white p-5 rounded-xl border border-amber-200 shadow-sm flex items-center justify-between hover:border-amber-400 transition group"
        >
          <div className="space-y-1">
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wider flex items-center space-x-1">
              <span>Pending Scrutiny</span>
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
            </p>
            <p className="text-2xl font-bold text-amber-900">{kpis.pending_verification}</p>
            <p className="text-xs text-amber-700 group-hover:underline flex items-center space-x-1">
              <span>Review submissions</span>
              <ArrowRight className="w-3 h-3" />
            </p>
          </div>
          <div className="w-12 h-12 bg-amber-50 text-amber-700 rounded-xl flex items-center justify-center">
            <Clock className="w-6 h-6" />
          </div>
        </Link>

        {/* Verified / Active */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wider">Verified Deposits</p>
            <p className="text-2xl font-bold text-emerald-900">{kpis.verified}</p>
            <p className="text-xs text-slate-600">Lien confirmed with bank</p>
          </div>
          <div className="w-12 h-12 bg-emerald-50 text-emerald-700 rounded-xl flex items-center justify-center">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        {/* Expiring in 30 Days */}
        <div className="bg-white p-5 rounded-xl border border-rose-200 shadow-sm flex items-center justify-between">
          <div className="space-y-1">
            <p className="text-xs font-semibold text-rose-700 uppercase tracking-wider">Expiring in ≤ 30 Days</p>
            <p className="text-2xl font-bold text-rose-900">{kpis.expiring_30_days}</p>
            <p className="text-xs text-slate-600">
              {kpis.expiring_60_days} within 60d • {kpis.expiring_90_days} within 90d
            </p>
          </div>
          <div className="w-12 h-12 bg-rose-50 text-rose-700 rounded-xl flex items-center justify-center">
            <CalendarClock className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* Secondary Quick Metrics Bar */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-slate-50 p-4 rounded-xl border border-slate-200">
        <div className="text-center">
          <span className="text-xs text-slate-500 font-medium">Expiring in 60 Days</span>
          <p className="text-lg font-bold text-slate-800">{kpis.expiring_60_days}</p>
        </div>
        <div className="text-center border-l border-slate-200">
          <span className="text-xs text-slate-500 font-medium">Expiring in 90 Days</span>
          <p className="text-lg font-bold text-slate-800">{kpis.expiring_90_days}</p>
        </div>
        <div className="text-center border-l border-slate-200">
          <span className="text-xs text-slate-500 font-medium">Expired (Action Required)</span>
          <p className="text-lg font-bold text-red-600">{kpis.expired}</p>
        </div>
        <div className="text-center border-l border-slate-200">
          <span className="text-xs text-slate-500 font-medium">Release Requests</span>
          <p className="text-lg font-bold text-indigo-600">{kpis.release_requests}</p>
        </div>
      </div>

      {/* Analytical Charts and Breakdowns */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Status Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900">Lifecycle Status Breakdown</h2>
            <span className="text-xs text-slate-500">{status_distribution.length} categories</span>
          </div>

          <div className="space-y-3">
            {status_distribution.map((item) => {
              const pct = kpis.total_fdrs > 0 ? (item.count / kpis.total_fdrs) * 100 : 0;
              return (
                <div key={item.status} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{item.label}</span>
                    <span className="font-semibold text-slate-900">
                      {item.count} ({pct.toFixed(0)}%) • {formatCurrency(item.total_amount)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-2 rounded-full ${
                        item.status === 'VERIFIED' || item.status === 'ACTIVE'
                          ? 'bg-emerald-500'
                          : item.status === 'SUBMITTED' || item.status === 'UNDER_REVIEW'
                          ? 'bg-[#e09f3e]'
                          : item.status === 'NEEDS_CLARIFICATION'
                          ? 'bg-amber-500'
                          : item.status === 'EXPIRED' || item.status === 'REJECTED'
                          ? 'bg-rose-500'
                          : 'bg-[#0d3b66]'
                      }`}
                      style={{ width: `${Math.max(pct, 3)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Top Banks Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900">Commercial Bank Exposure</h2>
            <span className="text-xs text-slate-500">Top 10 Banks</span>
          </div>

          <div className="space-y-3">
            {bank_distribution.map((item, idx) => {
              const pct = kpis.total_fdrs > 0 ? (item.count / kpis.total_fdrs) * 100 : 0;
              return (
                <div key={item.bank || idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700 truncate max-w-[180px]">{item.bank}</span>
                    <span className="font-semibold text-slate-900">
                      {item.count} FDRs • {formatCurrency(item.total_amount)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-[#0d3b66] h-2 rounded-full"
                      style={{ width: `${Math.max(pct, 4)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* State / Regional Distribution */}
        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h2 className="text-base font-bold text-slate-900">State-wise Distribution</h2>
            <span className="text-xs text-slate-500">Top Regions</span>
          </div>

          <div className="space-y-3">
            {state_distribution.map((item, idx) => {
              const pct = kpis.total_fdrs > 0 ? (item.count / kpis.total_fdrs) * 100 : 0;
              return (
                <div key={item.state || idx} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-slate-700">{item.state}</span>
                    <span className="font-semibold text-slate-900">
                      {item.count} • {formatCurrency(item.total_amount)}
                    </span>
                  </div>
                  <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-[#e09f3e] h-2 rounded-full"
                      style={{ width: `${Math.max(pct, 4)}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Recent System Activity Feed */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between border-b border-slate-100 pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-[#0d3b66]" />
            <h2 className="text-base font-bold text-slate-900">Live Compliance & Verification Audit Feed</h2>
          </div>
          <span className="text-xs text-slate-500 font-mono">Immutable Log</span>
        </div>

        <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
          {recent_activity.length === 0 ? (
            <p className="text-xs text-slate-500 py-4 text-center">No recent audit events recorded yet.</p>
          ) : (
            recent_activity.map((entry) => (
              <div key={entry.id} className="py-3 flex items-center justify-between text-xs hover:bg-slate-50 px-2 rounded-lg transition">
                <div className="flex items-center space-x-3">
                  <div className="w-7 h-7 rounded-full bg-slate-100 text-slate-700 flex items-center justify-center font-bold text-[10px]">
                    {entry.action.charAt(0)}
                  </div>
                  <div>
                    <div className="font-semibold text-slate-800">
                      {entry.actor_name}{' '}
                      <span className="text-slate-500 font-normal">
                        performed {entry.action_display} on {entry.entity_type} #{entry.entity_id}
                      </span>
                    </div>
                    {entry.after_state?.event && (
                      <p className="text-[11px] text-slate-500 mt-0.5">
                        Details: {entry.after_state.event}
                      </p>
                    )}
                  </div>
                </div>
                <div className="text-right text-[11px] text-slate-400 font-mono">
                  {new Date(entry.timestamp).toLocaleString('en-IN', {
                    dateStyle: 'short',
                    timeStyle: 'short'
                  })}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
