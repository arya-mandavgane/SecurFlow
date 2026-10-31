import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { RenewalsReleasesPage } from '../pages/institution/RenewalsReleasesPage';

describe('Phase 6 Renewals and Maturity Tests', () => {
  it('renders RenewalsReleasesPage with maturity tabs and radar', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <RenewalsReleasesPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/FDR Renewals & Maturity Tracking/i)).toBeInTheDocument();
    expect(screen.getByText(/Maturity Radar \(30\/60\/90 Days\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Renewals & Replacement/i)).toBeInTheDocument();
  });
});
