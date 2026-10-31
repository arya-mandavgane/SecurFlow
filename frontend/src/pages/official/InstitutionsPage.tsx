import React, { useEffect, useState } from 'react';
import {
  Building2,
  Search,
  MapPin,
  Mail,
  FileText,
  ArrowRight,
  Download,
  X,
  RefreshCw
} from 'lucide-react';
import { apiClient } from '../../api/client';
import { Institution, FDR, FDRDocument } from '../../types';

interface InstitutionDetails {
  institution: Institution;
  summary: {
    total_fdrs: number;
    total_pledged_value: number;
    active_value: number;
    document_count: number;
  };
  fdrs: FDR[];
  documents: FDRDocument[];
}

export const InstitutionsPage: React.FC = () => {
  const [institutions, setInstitutions] = useState<Institution[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [search, setSearch] = useState<string>('');

  // Selected institution modal
  const [selectedInstId, setSelectedInstId] = useState<number | null>(null);
  const [instDetails, setInstDetails] = useState<InstitutionDetails | null>(null);
  const [detailsLoading, setDetailsLoading] = useState<boolean>(false);
  const [activeTab, setActiveTab] = useState<'fdrs' | 'documents'>('fdrs');

  const fetchInstitutions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);

      const res = await apiClient.get(`/institutions/?${params.toString()}`);
      if (res.data?.results) {
        setInstitutions(res.data.results);
      } else if (Array.isArray(res.data)) {
        setInstitutions(res.data);
      }
    } catch {
      // non-fatal
    } finally {
      setLoading(false);
    }
  };

  const handleOpenDetails = async (id: number) => {
    setSelectedInstId(id);
    setDetailsLoading(true);
    setInstDetails(null);
    try {
      const res = await apiClient.get(`/institutions/${id}/fdrs/`);
      if (res.data?.success) {
        setInstDetails(res.data.data);
      }
    } catch (err: any) {
      alert('Failed to load institution history: ' + (err?.response?.data?.error?.message || err.message));
    } finally {
      setDetailsLoading(false);
    }
  };

  useEffect(() => {
    fetchInstitutions();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchInstitutions();
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#0d3b66]/10 text-[#0d3b66]">
              Institutional Master
            </span>
            <span className="text-xs text-slate-500 font-mono">Central Directory</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900 mt-1">Institutions & Document Repository</h1>
          <p className="text-sm text-slate-600 mt-0.5">
            Audit institution profiles, historical FDR portfolios, and verified document vaults.
          </p>
        </div>

        <button
          onClick={fetchInstitutions}
          className="flex items-center space-x-2 px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition self-start sm:self-auto"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="Search by Institution Name, AICTE Institute ID, City..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-9 pr-3 py-2 text-sm border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#0d3b66]"
            />
          </div>
          <button
            type="submit"
            className="px-5 py-2 bg-[#0d3b66] hover:bg-[#001e3d] text-white text-sm font-semibold rounded-lg transition"
          >
            Search
          </button>
        </form>
      </div>

      {/* Institutions Grid */}
      {loading ? (
        <div className="p-12 text-center space-y-3 bg-white rounded-xl border border-slate-200">
          <RefreshCw className="w-8 h-8 text-[#0d3b66] animate-spin mx-auto" />
          <p className="text-sm text-slate-500 font-medium">Loading technical institutions...</p>
        </div>
      ) : institutions.length === 0 ? (
        <div className="p-12 text-center space-y-3 bg-white rounded-xl border border-slate-200">
          <Building2 className="w-12 h-12 text-slate-400 mx-auto" />
          <h3 className="text-base font-bold text-slate-900">No Institutions Found</h3>
          <p className="text-sm text-slate-500">No institutions match the provided query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {institutions.map((inst) => (
            <div
              key={inst.id}
              className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:border-[#0d3b66] transition flex flex-col justify-between space-y-4"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[11px] font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono">
                    {inst.aicte_id}
                  </span>
                  <span className="text-xs text-slate-500 font-medium">{inst.state}</span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 line-clamp-2" title={inst.name}>
                  {inst.name}
                </h3>
                <div className="text-xs text-slate-500 space-y-1">
                  {inst.city && (
                    <div className="flex items-center space-x-1.5">
                      <MapPin className="w-3.5 h-3.5 text-slate-400" />
                      <span>{inst.city}, {inst.state}</span>
                    </div>
                  )}
                  {inst.email && (
                    <div className="flex items-center space-x-1.5">
                      <Mail className="w-3.5 h-3.5 text-slate-400" />
                      <span className="truncate">{inst.email}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <div className="text-xs">
                  <span className="text-slate-500 font-medium">FDR Deposits:</span>{' '}
                  <span className="font-bold text-slate-800">{inst.fdr_count || 0}</span>
                </div>
                <button
                  onClick={() => handleOpenDetails(inst.id)}
                  className="flex items-center space-x-1 text-xs font-semibold text-[#0d3b66] hover:text-[#001e3d] transition"
                >
                  <span>View History</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Institution Details & Document Repository Modal */}
      {selectedInstId && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl border border-slate-200">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-[#0d3b66] text-white flex items-center justify-center font-bold">
                  <Building2 className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-slate-900">
                    {instDetails?.institution.name || 'Loading Institution Profile...'}
                  </h2>
                  <p className="text-xs text-slate-500 font-mono">
                    AICTE ID: {instDetails?.institution.aicte_id} • {instDetails?.institution.city}, {instDetails?.institution.state}
                  </p>
                </div>
              </div>
              <button
                onClick={() => setSelectedInstId(null)}
                className="p-2 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-200 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto space-y-6 flex-1">
              {detailsLoading || !instDetails ? (
                <div className="py-12 text-center space-y-3">
                  <RefreshCw className="w-8 h-8 text-[#0d3b66] animate-spin mx-auto" />
                  <p className="text-sm text-slate-500">Retrieving institutional FDR history & documents...</p>
                </div>
              ) : (
                <>
                  {/* Summary Metric Cards */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                      <span className="text-[11px] text-slate-500 font-semibold uppercase">Total FDRs</span>
                      <p className="text-lg font-bold text-slate-900 mt-0.5">{instDetails.summary.total_fdrs}</p>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                      <span className="text-[11px] text-slate-500 font-semibold uppercase">Total Pledged</span>
                      <p className="text-lg font-bold text-slate-900 mt-0.5">
                        ₹{(instDetails.summary.total_pledged_value / 100000).toFixed(1)} L
                      </p>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                      <span className="text-[11px] text-emerald-700 font-semibold uppercase">Active / Verified</span>
                      <p className="text-lg font-bold text-emerald-900 mt-0.5">
                        ₹{(instDetails.summary.active_value / 100000).toFixed(1)} L
                      </p>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-center">
                      <span className="text-[11px] text-slate-500 font-semibold uppercase">Documents Vault</span>
                      <p className="text-lg font-bold text-slate-900 mt-0.5">{instDetails.summary.document_count}</p>
                    </div>
                  </div>

                  {/* Tabs */}
                  <div className="flex items-center space-x-2 border-b border-slate-200">
                    <button
                      onClick={() => setActiveTab('fdrs')}
                      className={`pb-2.5 px-3 text-xs font-bold transition border-b-2 ${
                        activeTab === 'fdrs'
                          ? 'border-[#0d3b66] text-[#0d3b66]'
                          : 'border-transparent text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      FDR Portfolio ({instDetails.fdrs.length})
                    </button>
                    <button
                      onClick={() => setActiveTab('documents')}
                      className={`pb-2.5 px-3 text-xs font-bold transition border-b-2 ${
                        activeTab === 'documents'
                          ? 'border-[#0d3b66] text-[#0d3b66]'
                          : 'border-transparent text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      Document Vault ({instDetails.documents.length})
                    </button>
                  </div>

                  {/* FDR Portfolio Tab */}
                  {activeTab === 'fdrs' && (
                    <div className="space-y-2">
                      {instDetails.fdrs.length === 0 ? (
                        <p className="text-xs text-slate-500 italic py-4">No FDR deposits logged yet.</p>
                      ) : (
                        <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                          <table className="w-full text-left border-collapse">
                            <thead>
                              <tr className="bg-slate-50 text-slate-600 border-b border-slate-200 font-semibold">
                                <th className="py-2.5 px-3">FDR Number</th>
                                <th className="py-2.5 px-3">Bank</th>
                                <th className="py-2.5 px-3 text-right">Amount (INR)</th>
                                <th className="py-2.5 px-3">Maturity Date</th>
                                <th className="py-2.5 px-3">Status</th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-100">
                              {instDetails.fdrs.map((f) => (
                                <tr key={f.id} className="hover:bg-slate-50">
                                  <td className="py-2.5 px-3 font-bold text-[#0d3b66]">{f.fdr_number}</td>
                                  <td className="py-2.5 px-3">{f.bank_name}</td>
                                  <td className="py-2.5 px-3 text-right font-semibold">
                                    ₹{Number(f.amount).toLocaleString('en-IN')}
                                  </td>
                                  <td className="py-2.5 px-3">{f.maturity_date}</td>
                                  <td className="py-2.5 px-3">
                                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-slate-100 text-slate-800">
                                      {f.status_display}
                                    </span>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Document Vault Tab */}
                  {activeTab === 'documents' && (
                    <div className="space-y-2">
                      {instDetails.documents.length === 0 ? (
                        <p className="text-xs text-slate-500 italic py-4">No documents stored in vault.</p>
                      ) : (
                        <div className="space-y-2">
                          {instDetails.documents.map((doc) => (
                            <div
                              key={doc.id}
                              className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                            >
                              <div className="flex items-center space-x-3">
                                <FileText className="w-5 h-5 text-[#0d3b66]" />
                                <div>
                                  <p className="font-semibold text-slate-900">{doc.file_name}</p>
                                  <p className="text-[11px] text-slate-500 font-mono">
                                    {doc.file_type_display} • {(doc.file_size / 1024).toFixed(1)} KB • SHA-256:{' '}
                                    {doc.checksum.substring(0, 16)}...
                                  </p>
                                </div>
                              </div>
                              <a
                                href={doc.download_url}
                                download
                                className="flex items-center space-x-1 px-3 py-1.5 bg-white border border-slate-200 hover:border-[#0d3b66] text-slate-700 rounded text-xs font-semibold transition"
                              >
                                <Download className="w-3.5 h-3.5" />
                                <span>Download</span>
                              </a>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
