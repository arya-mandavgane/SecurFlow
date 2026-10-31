export type UserRole = 'INSTITUTION' | 'OFFICIAL' | 'ADMIN';

export interface Institution {
  id: number;
  name: string;
  aicte_id: string;
  state: string;
  city?: string;
  address?: string;
  contact_person?: string;
  email?: string;
  phone?: string;
  fdr_count?: number;
  total_pledged_amount?: number;
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
  role_display?: string;
  institution?: Institution | null;
  phone_number?: string;
  designation?: string;
}

export type FDRStatus =
  | 'SUBMITTED'
  | 'UNDER_REVIEW'
  | 'VERIFIED'
  | 'REJECTED'
  | 'NEEDS_CLARIFICATION'
  | 'ACTIVE'
  | 'EXPIRING_SOON'
  | 'EXPIRED'
  | 'RENEWED'
  | 'RELEASE_REQUESTED'
  | 'RELEASED';

export interface FDRDocument {
  id: number;
  file: string;
  file_name: string;
  file_type: 'FDR_COPY' | 'BANK_LETTER' | 'RENEWAL_ADVICE' | 'RELEASE_NOC' | 'OTHER';
  file_type_display: string;
  uploaded_by_name?: string;
  checksum: string;
  file_size: number;
  mime_type: string;
  upload_timestamp: string;
  download_url: string;
}

export interface VerificationRecord {
  id: number;
  official_name?: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CLARIFICATION_REQUESTED';
  status_display: string;
  remarks: string;
  mismatches: Array<{
    field?: string;
    submitted?: any;
    ocr_found?: any;
    expected?: any;
    found?: any;
    severity?: string;
    issue?: string;
  }>;
  is_automated_draft: boolean;
  timestamp: string;
}

export interface FDR {
  id: number;
  fdr_number: string;
  institution: Institution;
  institution_name?: string;
  institution_aicte_id?: string;
  bank_name: string;
  branch: string;
  amount: string | number;
  interest_rate?: string | number | null;
  issue_date: string;
  maturity_date: string;
  lien_marked_aicte: boolean;
  purpose_approval_cycle: string;
  status: FDRStatus;
  status_display: string;
  document_count?: number;
  documents?: FDRDocument[];
  verification_records?: VerificationRecord[];
  parent_fdr?: number | null;
  parent_fdr_number?: string | null;
  extracted_data?: Record<string, any>;
  remarks?: string;
  created_at: string;
  updated_at?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  success: boolean;
  error?: {
    status_code?: number;
    message?: string;
    details?: any;
  };
}
