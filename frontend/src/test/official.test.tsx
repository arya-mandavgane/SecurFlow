import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { OfficialDashboardPage } from '../pages/official/OfficialDashboardPage';
import { VerificationQueuePage } from '../pages/official/VerificationQueuePage';
import { InstitutionsPage } from '../pages/official/InstitutionsPage';

describe('Official Portal Component Tests', () => {
  it('renders OfficialDashboardPage with live status monitoring indicators', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <OfficialDashboardPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Aggregating system-wide FDR data & metrics/i)).toBeInTheDocument();
  });

  it('renders VerificationQueuePage with pipeline headers and filter bar', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <VerificationQueuePage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Official Verification Queue/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Smart-ranked queue prioritizing flagged OCR discrepancies/i)
    ).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Search FDR number, Institute name, AICTE ID, Bank/i)
    ).toBeInTheDocument();
  });

  it('renders InstitutionsPage master directory with search', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <InstitutionsPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Institutions & Document Repository/i)).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText(/Search by Institution Name, AICTE Institute ID, City/i)
    ).toBeInTheDocument();
  });
});
