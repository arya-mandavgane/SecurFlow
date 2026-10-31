import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, FileText, PlusCircle, RefreshCw, AlertCircle, Building2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const { user } = useAuth();

  const navLinks = [
    {
      to: '/dashboard',
      label: 'Institution Dashboard',
      icon: LayoutDashboard,
      badge: null,
    },
    {
      to: '/fdrs',
      label: 'My FDRs & Deposits',
      icon: FileText,
      badge: null,
    },
    {
      to: '/fdrs/submit',
      label: 'Submit New FDR',
      icon: PlusCircle,
      badge: 'New',
    },
    {
      to: '/fdrs?status=NEEDS_CLARIFICATION',
      label: 'Clarification Requests',
      icon: AlertCircle,
      badge: null,
    },
    {
      to: '/renewals-releases',
      label: 'Renewals & Releases',
      icon: RefreshCw,
      badge: null,
    },
  ];

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onClose}
          className="fixed inset-0 bg-slate-900/50 z-40 md:hidden backdrop-blur-sm"
        />
      )}

      <aside
        className={`fixed md:sticky top-16 left-0 z-40 h-[calc(100vh-4rem)] w-64 bg-slate-900 text-slate-200 border-r border-slate-800 transition-transform duration-200 ease-in-out flex flex-col justify-between ${
          isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        <div className="p-4 space-y-6">
          {/* Institutional Info Header */}
          {user?.institution && (
            <div className="bg-slate-800/60 p-3 rounded-lg border border-slate-700/50">
              <div className="flex items-center space-x-2 text-xs text-[#e09f3e] font-semibold uppercase tracking-wider">
                <Building2 className="w-3.5 h-3.5" />
                <span>Institute Portal</span>
              </div>
              <div className="text-sm font-medium text-white mt-1 truncate">
                {user.institution.name}
              </div>
              <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                ID: {user.institution.aicte_id}
              </div>
            </div>
          )}

          {/* Nav Items */}
          <nav className="space-y-1">
            {navLinks.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition ${
                      isActive
                        ? 'bg-[#0d3b66] text-white font-semibold shadow-sm border-l-4 border-[#e09f3e]'
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                    }`
                  }
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="w-4 h-4 text-slate-400 group-hover:text-white" />
                    <span>{item.label}</span>
                  </div>
                  {item.badge && (
                    <span className="bg-[#e09f3e] text-[#001e3d] text-[10px] font-bold px-1.5 py-0.5 rounded uppercase">
                      {item.badge}
                    </span>
                  )}
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* Footer Quick Status */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/40 text-[11px] text-slate-400 flex items-center justify-between">
          <span>AICTE Live Gateway</span>
          <span className="flex items-center text-emerald-400 space-x-1 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <span>Online</span>
          </span>
        </div>
      </aside>
    </>
  );
};
