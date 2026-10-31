import { useState, useEffect } from 'react';

interface ServiceHealth {
  status: string;
  service: string;
  version: string;
}

export default function App() {
  const [backendHealth, setBackendHealth] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/health/')
      .then((res) => res.json())
      .then((data) => {
        setBackendHealth(data);
        setLoading(false);
      })
      .catch(() => {
        setBackendHealth({ status: 'standby', service: 'securflow-backend', version: '1.0.0' });
        setLoading(false);
      });
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Header */}
      <header className="bg-[#001e3d] border-b-4 border-[#e09f3e] text-white px-6 py-4 shadow-md">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <img src="/logo.png" alt="SecurFlow Logo" className="h-11 bg-white/95 px-2.5 py-1 rounded-md shadow object-contain" />
            <div>
              <h1 className="text-xl font-bold tracking-tight">SecurFlow</h1>
              <p className="text-xs text-slate-300">AICTE Security Deposit & FDR Management Portal</p>
            </div>
          </div>
          <div className="hidden md:flex items-center space-x-3 text-xs bg-slate-800/60 px-3 py-1.5 rounded-md border border-slate-700">
            <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span>Government of India &bull; AICTE New Delhi</span>
          </div>
        </div>
      </header>

      {/* Hero Body */}
      <main className="max-w-7xl mx-auto px-6 py-12 flex-1 w-full flex flex-col items-center justify-center text-center">
        <img src="/logo.png" alt="SecurFlow Logo" className="h-20 mb-6 drop-shadow-md rounded-xl bg-white p-2.5 border border-slate-200 object-contain" />
        <div className="inline-block px-3.5 py-1 mb-4 text-xs font-semibold uppercase tracking-wider text-blue-900 bg-blue-100 rounded-full">
          Phase 1 Foundation Ready
        </div>
        <h2 className="text-4xl md:text-5xl font-extrabold text-[#001e3d] max-w-3xl leading-tight">
          One Platform. Complete FDR Lifecycle. <span className="text-[#0d3b66]">Smarter Compliance.</span>
        </h2>
        <p className="mt-4 text-lg text-slate-600 max-w-2xl">
          SecurFlow centralizes FDR submissions, intelligent OCR document validation, 
          automated maturity alerting, and lien refund management for technical institutions nationwide.
        </p>

        {/* Status Dashboard Skeleton */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-3 gap-6 w-full max-w-4xl text-left">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="text-xs uppercase font-semibold text-slate-400 mb-1">Core Backend</div>
            <div className="text-xl font-bold text-slate-800">Django REST API</div>
            <div className="mt-3 flex items-center text-xs font-medium text-emerald-600">
              <span className="h-2 w-2 bg-emerald-500 rounded-full mr-2"></span>
              {loading ? 'Checking status...' : `Status: ${backendHealth?.status || 'Online'}`}
            </div>
            <div className="text-xs text-slate-500 mt-2">PostgreSQL 16 + pgvector &bull; Celery</div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="text-xs uppercase font-semibold text-slate-400 mb-1">AI Assistant Microservice</div>
            <div className="text-xl font-bold text-slate-800">FastAPI + pgvector</div>
            <div className="mt-3 flex items-center text-xs font-medium text-blue-600">
              <span className="h-2 w-2 bg-blue-500 rounded-full mr-2"></span>
              Port 8001 &bull; RAG Guideline Q&A
            </div>
            <div className="text-xs text-slate-500 mt-2">PyMuPDF Document Ingestion</div>
          </div>

          <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-200">
            <div className="text-xs uppercase font-semibold text-slate-400 mb-1">OCR Engine</div>
            <div className="text-xl font-bold text-slate-800">FastAPI + PaddleOCR</div>
            <div className="mt-3 flex items-center text-xs font-medium text-amber-600">
              <span className="h-2 w-2 bg-amber-500 rounded-full mr-2"></span>
              Port 8002 &bull; Extraction & Mismatches
            </div>
            <div className="text-xs text-slate-500 mt-2">Automated Lien Clause Verifier</div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-slate-900 text-slate-400 text-xs py-6 px-6 text-center border-t border-slate-800">
        <p>SecurFlow &copy; 2026 All India Council for Technical Education (AICTE). All rights reserved.</p>
      </footer>
    </div>
  );
}
