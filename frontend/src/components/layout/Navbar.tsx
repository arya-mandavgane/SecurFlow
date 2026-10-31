import React from 'react';
import { useAuth } from '../../context/AuthContext';
import { LogOut, Bell, Building } from 'lucide-react';

interface NavbarProps {
  onToggleSidebar?: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ onToggleSidebar }) => {
  const { user, logout } = useAuth();

  return (
    <header className="bg-[#001e3d] text-white border-b-2 border-[#e09f3e] sticky top-0 z-40 shadow-sm">
      <div className="px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Left: Mobile Toggle & Logo */}
        <div className="flex items-center space-x-3">
          {onToggleSidebar && (
            <button
              onClick={onToggleSidebar}
              className="md:hidden p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-slate-800"
              aria-label="Open sidebar"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          )}

          <div className="flex items-center space-x-3">
            <img
              src="/logo.png"
              alt="SecurFlow Logo"
              className="h-10 bg-white/95 px-2 py-0.5 rounded-md shadow-sm object-contain"
            />
            <div className="hidden sm:block">
              <span className="text-base font-bold tracking-tight text-white block leading-tight">SecurFlow</span>
              <span className="text-[11px] text-slate-300 block">AICTE FDR & Security Deposit Management</span>
            </div>
          </div>
        </div>

        {/* Center / Right: Institution Identifier & User Profile */}
        <div className="flex items-center space-x-4">
          {user?.institution && (
            <div className="hidden lg:flex items-center space-x-2 bg-slate-800/80 border border-slate-700/60 rounded-md px-3 py-1.5 text-xs text-slate-200">
              <Building className="w-3.5 h-3.5 text-[#e09f3e]" />
              <span className="font-medium max-w-[220px] truncate">{user.institution.name}</span>
              <span className="bg-slate-700 text-slate-300 px-1.5 py-0.5 rounded text-[10px] font-mono">
                {user.institution.aicte_id}
              </span>
            </div>
          )}

          {/* Notification Bell */}
          <button
            className="p-1.5 text-slate-300 hover:text-white hover:bg-slate-800 rounded-full transition relative"
            title="Notifications"
          >
            <Bell className="w-4 h-4" />
            <span className="absolute top-1 right-1 w-2 h-2 bg-amber-500 rounded-full animate-ping"></span>
          </button>

          {/* User Badge */}
          <div className="flex items-center space-x-2 pl-2 border-l border-slate-700">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-white leading-tight">
                {user?.first_name || user?.username}
              </div>
              <div className="text-[10px] text-emerald-400 font-medium">
                {user?.role_display || user?.role}
              </div>
            </div>

            <button
              onClick={() => logout()}
              className="flex items-center space-x-1 text-xs text-slate-300 hover:text-red-400 bg-slate-800 hover:bg-slate-700/80 px-2.5 py-1.5 rounded-md transition"
              title="Logout"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Logout</span>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};
