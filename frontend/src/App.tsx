import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/institution/DashboardPage';
import { FDRListPage } from './pages/institution/FDRListPage';
import { SubmitFDRPage } from './pages/institution/SubmitFDRPage';
import { FDRDetailPage } from './pages/institution/FDRDetailPage';
import { RenewalsReleasesPage } from './pages/institution/RenewalsReleasesPage';
import { OfficialDashboardPage } from './pages/official/OfficialDashboardPage';
import { VerificationQueuePage } from './pages/official/VerificationQueuePage';
import { SmartVerificationPage } from './pages/official/SmartVerificationPage';
import { InstitutionsPage } from './pages/official/InstitutionsPage';

const DashboardRedirector: React.FC = () => {
  const { user } = useAuth();
  if (user?.role === 'OFFICIAL' || user?.role === 'ADMIN') {
    return <Navigate to="/official/dashboard" replace />;
  }
  return <DashboardPage />;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication Route */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<DashboardRedirector />} />
              <Route path="/dashboard" element={<DashboardRedirector />} />

              {/* Institution Portal Routes */}
              <Route path="/fdrs" element={<FDRListPage />} />
              <Route path="/fdrs/submit" element={<SubmitFDRPage />} />
              <Route path="/fdrs/:id" element={<FDRDetailPage />} />
              <Route path="/renewals-releases" element={<RenewalsReleasesPage />} />

              {/* Official Workspace Routes */}
              <Route path="/official/dashboard" element={<OfficialDashboardPage />} />
              <Route path="/official/verification-queue" element={<VerificationQueuePage />} />
              <Route path="/official/verify/:id" element={<SmartVerificationPage />} />
              <Route path="/official/institutions" element={<InstitutionsPage />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<DashboardRedirector />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
