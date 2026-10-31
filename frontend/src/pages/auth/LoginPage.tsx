import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { Lock, Mail, ArrowRight, AlertCircle } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [username, setUsername] = useState<string>('principal@vjti.ac.in');
  const [password, setPassword] = useState<string>('SecurFlow@2026');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      await login(username, password);
      navigate('/dashboard');
    } catch (err: any) {
      const msg =
        err.response?.data?.error?.message ||
        err.response?.data?.detail ||
        'Authentication failed. Please verify credentials.';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const setDemoCredentials = (u: string, p: string = 'SecurFlow@2026') => {
    setUsername(u);
    setPassword(p);
    setErrorMsg(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Top Govt Bar */}
      <div className="bg-[#001e3d] text-white px-6 py-2.5 flex items-center justify-between text-xs border-b-2 border-[#e09f3e]">
        <div className="flex items-center space-x-2">
          <span className="font-semibold tracking-wide">All India Council for Technical Education (AICTE)</span>
          <span className="text-slate-400">|</span>
          <span className="text-slate-300">Ministry of Education, Govt. of India</span>
        </div>
        <div className="hidden sm:flex items-center space-x-3 text-slate-300">
          <span>Official FDR Gateway</span>
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
        </div>
      </div>

      <div className="flex-1 flex items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl border border-slate-200 overflow-hidden">
          {/* Card Header */}
          <div className="p-8 text-center bg-gradient-to-b from-slate-50 to-white border-b border-slate-100">
            <img
              src="/logo.png"
              alt="SecurFlow Logo"
              className="h-16 mx-auto mb-4 object-contain drop-shadow-sm"
            />
            <h2 className="text-xl font-bold text-[#001e3d]">SecurFlow Portal Login</h2>
            <p className="text-xs text-slate-500 mt-1.5 font-medium leading-relaxed">
              One Platform. Complete FDR Lifecycle. Smarter Compliance.
            </p>
          </div>

          {/* Form */}
          <div className="p-8 space-y-6">
            {errorMsg && (
              <div className="p-3.5 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start space-x-2.5">
                <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0 text-red-600" />
                <span>{errorMsg}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Email / Username
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    required
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    placeholder="e.g. principal@vjti.ac.in"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#001e3d] focus:border-transparent transition"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                  Account Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                  <input
                    type="password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:outline-none focus:ring-2 focus:ring-[#001e3d] focus:border-transparent transition"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={isSubmitting}
                className="w-full bg-[#001e3d] hover:bg-[#0d3b66] text-white py-2.5 rounded-lg text-sm font-semibold flex items-center justify-center space-x-2 transition shadow disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                    <span>Authenticating...</span>
                  </>
                ) : (
                  <>
                    <span>Sign In to Portal</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

            {/* Quick Demo Credentials */}
            <div className="pt-4 border-t border-slate-100">
              <div className="text-[11px] font-semibold uppercase tracking-wider text-slate-400 text-center mb-3">
                Quick Demo Accounts (1-Click Fill)
              </div>
              <div className="grid grid-cols-2 gap-2 text-xs">
                <button
                  type="button"
                  onClick={() => setDemoCredentials('principal@vjti.ac.in')}
                  className="p-2 text-left rounded border border-slate-200 hover:border-[#001e3d] hover:bg-slate-50 transition"
                >
                  <div className="font-semibold text-slate-800">VJTI Mumbai</div>
                  <div className="text-[10px] text-slate-500">Institution User</div>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('registrar@coep.ac.in')}
                  className="p-2 text-left rounded border border-slate-200 hover:border-[#001e3d] hover:bg-slate-50 transition"
                >
                  <div className="font-semibold text-slate-800">COEP Tech Pune</div>
                  <div className="text-[10px] text-slate-500">Institution User</div>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('official1@aicte.gov.in')}
                  className="p-2 text-left rounded border border-slate-200 hover:border-[#001e3d] hover:bg-slate-50 transition"
                >
                  <div className="font-semibold text-slate-800">AICTE Official</div>
                  <div className="text-[10px] text-emerald-600">Verification Officer</div>
                </button>

                <button
                  type="button"
                  onClick={() => setDemoCredentials('admin@aicte.gov.in')}
                  className="p-2 text-left rounded border border-slate-200 hover:border-[#001e3d] hover:bg-slate-50 transition"
                >
                  <div className="font-semibold text-slate-800">Administrator</div>
                  <div className="text-[10px] text-blue-600">Portal Admin</div>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="text-center py-4 text-xs text-slate-500 border-t border-slate-200 bg-white">
        SecurFlow &copy; 2026 All India Council for Technical Education. Protected under Government Information Security Regulations.
      </footer>
    </div>
  );
};
