import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ReleaseEvaluationPage } from '../pages/official/ReleaseEvaluationPage';

describe('Phase 7 Release & Refund Workflow Tests', () => {
  it('renders ReleaseEvaluationPage with official evaluation panels and metrics', () => {
    render(
      <AuthProvider>
        <BrowserRouter>
          <ReleaseEvaluationPage />
        </BrowserRouter>
      </AuthProvider>
    );

    expect(screen.getByText(/Lien Release & Refund Approvals/i)).toBeInTheDocument();
    expect(screen.getByText(/Pending Official Evaluation/i)).toBeInTheDocument();
    expect(screen.getByText(/Approved & Released/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/Search FDR number, Institute name, AICTE ID/i)).toBeInTheDocument();
  });
});
