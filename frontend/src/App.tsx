import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/institution/DashboardPage';
import { FDRListPage } from './pages/institution/FDRListPage';
import { SubmitFDRPage } from './pages/institution/SubmitFDRPage';
import { FDRDetailPage } from './pages/institution/FDRDetailPage';
import { RenewalsReleasesPage } from './pages/institution/RenewalsReleasesPage';

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
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/fdrs" element={<FDRListPage />} />
              <Route path="/fdrs/submit" element={<SubmitFDRPage />} />
              <Route path="/fdrs/:id" element={<FDRDetailPage />} />
              <Route path="/renewals-releases" element={<RenewalsReleasesPage />} />
            </Route>
          </Route>

          {/* Catch-all */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
