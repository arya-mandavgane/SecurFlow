import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { apiClient } from '../../api/client';
import {
  Upload,
  CheckCircle,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  IndianRupee,
  ShieldCheck,
  Trash2
} from 'lucide-react';

export const SubmitFDRPage: React.FC = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState<number>(1);
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [formData, setFormData] = useState({
    fdr_number: '',
    bank_name: 'State Bank of India',
    branch: '',
    amount: '',
    interest_rate: '7.10',
    issue_date: '',
    maturity_date: '',
    purpose_approval_cycle: 'AICTE Approval Cycle 2025-26',
    lien_marked_aicte: true,
    remarks: '',
  });

  // Document State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileType, setFileType] = useState<string>('FDR_COPY');

  const topBanks = [
    'State Bank of India',
    'Punjab National Bank',
    'Bank of Baroda',
    'Canara Bank',
    'Union Bank of India',
    'Indian Bank',
    'HDFC Bank',
    'ICICI Bank',
    'Axis Bank',
    'Kotak Mahindra Bank',
  ];

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    if (type === 'checkbox') {
      const checked = (e.target as HTMLInputElement).checked;
      setFormData((prev) => ({ ...prev, [name]: checked }));
    } else {
      setFormData((prev) => ({ ...prev, [name]: value }));
    }
  };

  const handleFileDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      validateAndSetFile(e.target.files[0]);
    }
  };

  const validateAndSetFile = (file: File) => {
    setErrorMsg(null);
    const validExtensions = ['.pdf', '.jpg', '.jpeg', '.png'];
    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();

    if (!validExtensions.includes(ext)) {
      setErrorMsg('Unsupported file format. Please upload PDF, JPG, or PNG document.');
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMsg('File exceeds 15MB limit.');
      return;
    }

    setSelectedFile(file);
  };

  const handleNext = () => {
    setErrorMsg(null);
    if (step === 1) {
      if (!formData.fdr_number || !formData.bank_name || !formData.amount || !formData.issue_date || !formData.maturity_date) {
        setErrorMsg('Please complete all mandatory FDR parameters.');
        return;
      }
      if (new Date(formData.maturity_date) <= new Date(formData.issue_date)) {
        setErrorMsg('Maturity date must be after the issue date.');
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (!selectedFile) {
        setErrorMsg('Please upload a scanned copy of the FDR certificate.');
        return;
      }
      setStep(3);
    }
  };

  const handleSubmitFinal = async () => {
    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      // 1. Create FDR Record
      const fdrPayload = {
        fdr_number: formData.fdr_number,
        bank_name: formData.bank_name,
        branch: formData.branch || 'Main Branch',
        amount: formData.amount,
        interest_rate: formData.interest_rate || null,
        issue_date: formData.issue_date,
        maturity_date: formData.maturity_date,
        purpose_approval_cycle: formData.purpose_approval_cycle,
        lien_marked_aicte: formData.lien_marked_aicte,
        remarks: formData.remarks,
      };

      const res = await apiClient.post('/fdrs/', fdrPayload);
      const newFdrId = res.data.id;

      // 2. Upload Document if selected
      if (selectedFile) {
        const docData = new FormData();
        docData.append('file', selectedFile);
        docData.append('file_type', fileType);

        await apiClient.post(`/fdrs/${newFdrId}/documents/`, docData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
      }

      // 3. Navigate to detail view
      navigate(`/fdrs/${newFdrId}`);
    } catch (err: any) {
      const msg =
        err.response?.data?.error?.message ||
        JSON.stringify(err.response?.data?.error?.details || err.response?.data) ||
        'Failed to submit FDR. Please check entered details.';
      setErrorMsg(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#001e3d]">Submit New Fixed Deposit Receipt</h1>
          <p className="text-xs text-slate-500 mt-1">
            Deposit details and scanned bank advice for AICTE verification
          </p>
        </div>
        <Link to="/fdrs" className="text-xs font-semibold text-slate-600 hover:text-slate-900">
          Cancel & Return
        </Link>
      </div>

      {/* Stepper Header */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between text-xs">
        <div className={`flex items-center space-x-2 ${step >= 1 ? 'text-[#001e3d] font-bold' : 'text-slate-400'}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 1 ? 'bg-[#001e3d] text-white' : 'bg-slate-100 text-slate-500'}`}>
            1
          </div>
          <span>Deposit Details</span>
        </div>

        <div className="w-12 h-0.5 bg-slate-200"></div>

        <div className={`flex items-center space-x-2 ${step >= 2 ? 'text-[#001e3d] font-bold' : 'text-slate-400'}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 2 ? 'bg-[#001e3d] text-white' : 'bg-slate-100 text-slate-500'}`}>
            2
          </div>
          <span>Document Upload</span>
        </div>

        <div className="w-12 h-0.5 bg-slate-200"></div>

        <div className={`flex items-center space-x-2 ${step >= 3 ? 'text-[#001e3d] font-bold' : 'text-slate-400'}`}>
          <div className={`w-7 h-7 rounded-full flex items-center justify-center font-bold ${step >= 3 ? 'bg-[#001e3d] text-white' : 'bg-slate-100 text-slate-500'}`}>
            3
          </div>
          <span>Review & Confirm</span>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3.5 bg-red-50 border border-red-200 rounded-lg text-red-700 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Step 1: Deposit Details */}
      {step === 1 && (
        <div className="bg-white p-6 sm:p-8 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                FDR Receipt Number *
              </label>
              <input
                type="text"
                name="fdr_number"
                value={formData.fdr_number}
                onChange={handleInputChange}
                placeholder="e.g. FDR-2025-SBI-987654"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Bank Name *
              </label>
              <select
                name="bank_name"
                value={formData.bank_name}
                onChange={handleInputChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              >
                {topBanks.map((bank) => (
                  <option key={bank} value={bank}>{bank}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Branch Location
              </label>
              <input
                type="text"
                name="branch"
                value={formData.branch}
                onChange={handleInputChange}
                placeholder="e.g. Fort Main Branch, Mumbai"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Deposit Amount (₹ INR) *
              </label>
              <div className="relative">
                <IndianRupee className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
                <input
                  type="number"
                  name="amount"
                  value={formData.amount}
                  onChange={handleInputChange}
                  placeholder="e.g. 2500000"
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none font-semibold"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Interest Rate (% p.a.)
              </label>
              <input
                type="number"
                step="0.01"
                name="interest_rate"
                value={formData.interest_rate}
                onChange={handleInputChange}
                placeholder="e.g. 7.10"
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                AICTE Approval Purpose / Cycle *
              </label>
              <input
                type="text"
                name="purpose_approval_cycle"
                value={formData.purpose_approval_cycle}
                onChange={handleInputChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Issue Date *
              </label>
              <input
                type="date"
                name="issue_date"
                value={formData.issue_date}
                onChange={handleInputChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Maturity Date *
              </label>
              <input
                type="date"
                name="maturity_date"
                value={formData.maturity_date}
                onChange={handleInputChange}
                className="w-full px-3.5 py-2.5 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none"
              />
            </div>
          </div>

          {/* Lien Checkbox */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-lg flex items-start space-x-3">
            <input
              type="checkbox"
              id="lien_marked"
              name="lien_marked_aicte"
              checked={formData.lien_marked_aicte}
              onChange={handleInputChange}
              className="w-4 h-4 text-[#001e3d] rounded mt-0.5"
            />
            <label htmlFor="lien_marked" className="text-xs text-slate-700 font-medium cursor-pointer">
              <span className="font-bold text-slate-900 block">Lien / Pledge Noted in favour of AICTE</span>
              I confirm that the fixed deposit is pledged jointly with Member Secretary, AICTE New Delhi as required by AICTE Approval Process Handbook regulations.
            </label>
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="button"
              onClick={handleNext}
              className="bg-[#001e3d] hover:bg-[#0d3b66] text-white px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center space-x-2 transition"
            >
              <span>Continue to Document Upload</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Document Upload */}
      {step === 2 && (
        <div className="bg-white p-6 sm:p-8 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Document Type
            </label>
            <select
              value={fileType}
              onChange={(e) => setFileType(e.target.value)}
              className="w-full max-w-xs px-3.5 py-2 rounded-lg border border-slate-300 text-sm focus:ring-2 focus:ring-[#001e3d] focus:outline-none mb-4"
            >
              <option value="FDR_COPY">FDR Original Scanned Copy</option>
              <option value="BANK_LETTER">Bank Lien / Pledge Advice Letter</option>
              <option value="RENEWAL_ADVICE">Renewal Certificate</option>
              <option value="OTHER">Other Compliance Document</option>
            </select>
          </div>

          {/* Drag & Drop Zone */}
          <div
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleFileDrop}
            className={`border-2 border-dashed rounded-xl p-8 text-center transition ${
              selectedFile ? 'border-emerald-400 bg-emerald-50/30' : 'border-slate-300 hover:border-[#001e3d] bg-slate-50'
            }`}
          >
            {selectedFile ? (
              <div className="flex flex-col items-center space-y-2">
                <CheckCircle className="w-10 h-10 text-emerald-600" />
                <div className="text-sm font-bold text-slate-800">{selectedFile.name}</div>
                <div className="text-xs text-slate-500">{(selectedFile.size / 1024).toFixed(1)} KB &bull; Ready for upload</div>
                <button
                  type="button"
                  onClick={() => setSelectedFile(null)}
                  className="mt-2 text-xs text-red-600 hover:underline flex items-center space-x-1"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Remove file</span>
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <Upload className="w-10 h-10 text-slate-400" />
                <div>
                  <label className="cursor-pointer text-sm font-bold text-[#001e3d] hover:underline">
                    <span>Click to browse</span>
                    <input
                      type="file"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={handleFileChange}
                      className="hidden"
                    />
                  </label>
                  <span className="text-sm text-slate-600"> or drag and drop file here</span>
                </div>
                <p className="text-xs text-slate-400">PDF, JPG, or PNG up to 15MB. Tamper-proof SHA-256 will be calculated.</p>
              </div>
            )}
          </div>

          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={() => setStep(1)}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center space-x-1"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Details</span>
            </button>
            <button
              type="button"
              onClick={handleNext}
              className="bg-[#001e3d] hover:bg-[#0d3b66] text-white px-6 py-2.5 rounded-lg text-sm font-semibold flex items-center space-x-2 transition"
            >
              <span>Review Submission</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Final Submit */}
      {step === 3 && (
        <div className="bg-white p-6 sm:p-8 rounded-xl border border-slate-200 shadow-sm space-y-6">
          <div className="border-b border-slate-100 pb-4">
            <h2 className="text-base font-bold text-slate-900">Review Submission Summary</h2>
            <p className="text-xs text-slate-500">Verify information before registering with AICTE</p>
          </div>

          <div className="grid grid-cols-2 gap-4 text-xs">
            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">FDR Receipt Number</span>
              <span className="font-mono font-bold text-slate-900 text-sm">{formData.fdr_number}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Deposit Amount</span>
              <span className="font-bold text-slate-900 text-sm">₹{Number(formData.amount).toLocaleString('en-IN')}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Bank & Branch</span>
              <span className="font-semibold text-slate-900">{formData.bank_name} ({formData.branch || 'Main'})</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Maturity Date</span>
              <span className="font-semibold text-slate-900">{formData.maturity_date}</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Lien Clause</span>
              <span className="font-semibold text-emerald-700">AICTE Pledged</span>
            </div>

            <div className="p-3 bg-slate-50 rounded-lg">
              <span className="text-slate-500 block">Attached Document</span>
              <span className="font-semibold text-slate-900">{selectedFile?.name || 'FDR Certificate'}</span>
            </div>
          </div>

          <div className="flex justify-between pt-4">
            <button
              type="button"
              onClick={() => setStep(2)}
              disabled={isSubmitting}
              className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center space-x-1"
            >
              <ArrowLeft className="w-4 h-4" />
              <span>Back to Document</span>
            </button>

            <button
              type="button"
              onClick={handleSubmitFinal}
              disabled={isSubmitting}
              className="bg-emerald-600 hover:bg-emerald-700 text-white px-8 py-2.5 rounded-lg text-sm font-bold flex items-center space-x-2 transition shadow disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Submitting to AICTE...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4" />
                  <span>Submit FDR for Verification</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
