import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { LoginPage } from '../pages/auth/LoginPage';
import { SubmitFDRPage } from '../pages/institution/SubmitFDRPage';

describe('Key Forms Component Tests', () => {
  it('renders LoginPage with tagline and demo credential buttons', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <LoginPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/SecurFlow Portal Login/i)).toBeInTheDocument();
    expect(
      screen.getByText(/One Platform\. Complete FDR Lifecycle\. Smarter Compliance\./i)
    ).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/principal@vjti\.ac\.in/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In to Portal/i })).toBeInTheDocument();

    // Verify quick fill buttons
    const vjtiBtn = screen.getByRole('button', { name: /VJTI Mumbai/i });
    expect(vjtiBtn).toBeInTheDocument();
    fireEvent.click(vjtiBtn);
  });

  it('renders SubmitFDRPage and validates mandatory fields on Next', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <SubmitFDRPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Submit New Fixed Deposit Receipt/i)).toBeInTheDocument();
    expect(screen.getAllByText(/Deposit Details/i).length).toBeGreaterThan(0);
    expect(screen.getByPlaceholderText(/FDR-2025-SBI-987654/i)).toBeInTheDocument();

    // Clicking Next without required inputs displays validation error
    const nextBtn = screen.getByRole('button', { name: /Continue to Document Upload/i });
    fireEvent.click(nextBtn);

    expect(
      screen.getByText(/Please complete all mandatory FDR parameters\./i)
    ).toBeInTheDocument();
  });
});
