import React, { useState, useEffect } from 'react';
import { publicApi, API_URL, type VerifyResponse } from '../../services/api';
import { validatePhone, sanitizePhoneInput } from '../../utils/validatePhone';

function formatDateTime(s: string): string {
  return new Date(s).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' });
}

function formatDate(s: string): string {
  return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

const APP_ORIGIN = typeof window !== 'undefined' ? window.location.origin : '';

function hasRecord(result: VerifyResponse): boolean {
  return !!(result.property_name || result.property_address);
}

const STATUS_COLORS: Record<string, string> = {
  ACTIVE: 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40',
  PENDING: 'bg-amber-500/20 text-amber-300 border border-amber-400/40',
  REVOKED: 'bg-red-500/20 text-red-300 border border-red-400/40',
  EXPIRED: 'bg-slate-500/20 text-slate-300 border border-slate-400/40',
  COMPLETED: 'bg-blue-500/20 text-blue-300 border border-blue-400/40',
  CANCELLED: 'bg-slate-500/20 text-slate-300 border border-slate-400/40',
};

export const VerifyPage: React.FC = () => {
  const [tokenId, setTokenId] = useState('');
  const [propertyAddress, setPropertyAddress] = useState('');
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VerifyResponse | null>(null);
  const [showLedger, setShowLedger] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    const hash = window.location.hash || '';
    const fromHash = new URLSearchParams(hash.split('?')[1] || '');
    const fromSearch = new URLSearchParams(window.location.search || '');
    const token = fromHash.get('token') || fromHash.get('token_id') || fromSearch.get('token') || fromSearch.get('token_id') || '';
    const address = fromHash.get('address') || fromHash.get('property_address') || fromSearch.get('address') || fromSearch.get('property_address') || '';
    if (token) setTokenId(token);
    if (address) setPropertyAddress(decodeURIComponent(address));
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setResult(null);
    setShowLedger(false);
    if (!(tokenId ?? '').trim()) { setError('Token ID is required.'); return; }
    const phoneVal = (phone ?? '').trim();
    if (phoneVal) {
      const phoneCheck = validatePhone(phoneVal);
      if (!phoneCheck.valid) { setError(phoneCheck.error ?? 'Invalid phone number.'); return; }
    }
    setSubmitting(true);
    try {
      const res = await publicApi.verify({
        token_id: (tokenId ?? '').trim(),
        property_address: (propertyAddress ?? '').trim() || undefined,
        name: (name ?? '').trim() || undefined,
        phone: (phone ?? '').trim() || undefined,
      });
      setResult(res);
    } catch (err) {
      setError((err as Error)?.message ?? 'Verification failed.');
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass = 'w-full px-4 py-2.5 rounded-lg border border-white/20 bg-white/10 text-white placeholder-white/50 focus:ring-2 focus:ring-[hsl(265,89%,66%)] focus:border-[hsl(265,89%,66%)] outline-none transition-colors';

  return (
    <div className="min-h-screen flex flex-col relative z-10 bg-[hsl(230,35%,4%)] text-white print:bg-white print:text-gray-900">
      <div className="max-w-xl mx-auto w-full px-4 sm:px-6 py-8 sm:py-10 space-y-6 print:py-6">
        <header className="text-center">
          <h1 className="text-2xl font-bold text-white">Verify authorization</h1>
          <p className="text-white/80 mt-1 text-sm">
            Enter the token (Invitation ID) to check the current status of this property.
          </p>
        </header>

        {/* --- Search form (hidden when printing) --- */}
        <form onSubmit={handleSubmit} className="glass rounded-xl border border-white/10 shadow-sm p-6 sm:p-8 space-y-4 print:hidden">
          <div>
            <label htmlFor="verify-token" className="block text-sm font-medium text-white/90 mb-1.5">Token ID <span className="text-red-400">*</span></label>
            <input id="verify-token" type="text" value={tokenId} onChange={(e) => setTokenId(e.target.value)} placeholder="e.g. INV-XXXX" className={inputClass} required />
          </div>
          <div>
            <label htmlFor="verify-address" className="block text-sm font-medium text-white/80 mb-1.5">Property address <span className="text-white/50 font-normal">(optional)</span></label>
            <textarea id="verify-address" value={propertyAddress} onChange={(e) => setPropertyAddress(e.target.value)} placeholder="Street, city, state, ZIP" rows={2} className={`${inputClass} resize-none`} />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="verify-name" className="block text-sm font-medium text-white/80 mb-1.5">Name (optional)</label>
              <input id="verify-name" type="text" value={name} onChange={(e) => setName(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label htmlFor="verify-phone" className="block text-sm font-medium text-white/80 mb-1.5">Phone (optional)</label>
              <input id="verify-phone" type="text" value={phone} onChange={(e) => setPhone(sanitizePhoneInput(e.target.value))} placeholder="+15551234567" className={inputClass} />
            </div>
          </div>
          {error && (
            <p className="text-sm text-red-200 bg-red-500/20 border border-red-400/40 rounded-lg px-4 py-3 flex items-center gap-2">
              <svg className="w-4 h-4 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
              {error}
            </p>
          )}
          <button type="submit" disabled={submitting} className="w-full sm:w-auto min-w-[140px] px-6 py-2.5 rounded-lg bg-[hsl(265,89%,66%)] hover:bg-[hsl(265,75%,58%)] text-white font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
            {submitting ? <span className="inline-flex items-center gap-2"><svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" /></svg>Verifying…</span> : 'Verify'}
          </button>
        </form>

        {/* --- Result section --- */}
        {result && (
          <section id="verify-result" className="glass rounded-xl border border-white/10 overflow-hidden print:bg-white print:border-gray-200 print:shadow-none print:break-inside-avoid">
            {/* Print header */}
            <div className="hidden print:block px-6 py-3 border-b border-gray-200">
              <h2 className="text-lg font-bold text-gray-900">DocuStay Verification Record</h2>
              <p className="text-sm text-gray-500 mt-0.5">{result.verified_at ? `Verified: ${formatDateTime(result.verified_at)}` : ''}</p>
              <p className="text-xs text-gray-400">Source: {result.verification_source || 'DocuStay Verification Portal'}</p>
            </div>

            {/* Status banner */}
            <div className={`px-6 py-4 border-b border-white/10 ${result.valid ? 'bg-emerald-500/20 border-emerald-400/30' : hasRecord(result) ? 'bg-slate-500/20 border-slate-400/30' : 'bg-amber-500/20 border-amber-400/30'} print:bg-gray-50 print:border-gray-200`}>
              <div className="flex items-center justify-between">
                <h2 className="text-sm font-bold uppercase tracking-wider text-white/90 print:text-gray-700 print:text-base">Property Status</h2>
                {result.resident_status && (
                  <span className={`text-xs font-semibold uppercase tracking-wide px-2.5 py-1 rounded ${result.resident_status === 'away' ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40'}`}>
                    Resident {result.resident_status === 'away' ? 'Away' : 'Present'}
                  </span>
                )}
              </div>
            </div>

            <div className="p-6 sm:p-8 space-y-6">
              {/* Status badge */}
              {result.valid ? (
                <div className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-emerald-500/20 text-emerald-300 border border-emerald-400/40">
                  <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" /></svg>
                  <span className="font-semibold">Active authorization</span>
                </div>
              ) : hasRecord(result) ? (
                <div className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-slate-500/20 text-slate-200 border border-slate-400/40">
                  <span className="font-semibold">Verification record</span>
                  {result.status && <span className={`px-2.5 py-1 rounded text-xs font-semibold uppercase tracking-wide ${STATUS_COLORS[result.status] || 'bg-white/10 text-white/80'}`}>{result.status}</span>}
                </div>
              ) : (
                <div className="inline-flex items-center gap-2.5 px-4 py-2.5 rounded-lg bg-amber-500/20 text-amber-300 border border-amber-400/40">
                  <svg className="w-5 h-5 shrink-0" fill="currentColor" viewBox="0 0 20 20"><path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" /></svg>
                  <span className="font-semibold">No record found</span>
                </div>
              )}
              {!hasRecord(result) && result.reason && <p className="text-white/80">{result.reason}</p>}

              {hasRecord(result) && (
                <>
                  {result.reason && <p className="text-sm text-white/90 -mt-2 font-medium">{result.reason}</p>}

                  {/* Property information */}
                  <div className="rounded-lg border border-white/10 bg-white/5 p-4 print:bg-white print:border-gray-300 print:text-gray-900">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-white/60 mb-3 print:text-gray-500">Property information</h3>
                    <p className="text-base font-semibold text-white print:text-gray-900">{result.property_name || '—'}</p>
                    <p className="text-sm text-white/80 mt-1 leading-relaxed print:text-gray-700">{result.property_address || '—'}</p>
                  </div>

                  {/* Assigned tenants */}
                  {result.assigned_tenants && result.assigned_tenants.length > 0 && (
                    <div className="rounded-lg border border-white/10 bg-white/5 p-4 print:bg-white print:border-gray-300">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-white/60 mb-3 print:text-gray-500">Assigned tenants</h3>
                      <div className="space-y-2">
                        {result.assigned_tenants.map((t, i) => (
                          <div key={i} className="flex items-center justify-between">
                            <span className="text-sm font-medium text-white print:text-gray-900">{t.name}</span>
                            <span className={`text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded ${t.status === 'away' ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40'}`}>
                              {t.status === 'away' ? 'Away' : 'Present'}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Guest authorization */}
                  {result.guest_name && (
                    <div className="rounded-lg border border-white/10 bg-white/5 p-4 print:bg-white print:border-gray-300">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-white/60 mb-3 print:text-gray-500">Guest authorization</h3>
                      <div className="space-y-3 text-sm">
                        <div className="flex justify-between gap-4">
                          <span className="text-white/60 print:text-gray-500">Guest</span>
                          <span className="text-white font-medium print:text-gray-900">{result.guest_name}</span>
                        </div>
                        {result.status && (
                          <div className="flex justify-between gap-4">
                            <span className="text-white/60 print:text-gray-500">Status</span>
                            <span className={`font-semibold uppercase tracking-wide text-xs px-2.5 py-1 rounded ${STATUS_COLORS[result.status] || 'bg-white/10 text-white/80'}`}>{result.status}</span>
                          </div>
                        )}
                        {result.stay_start_date && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Authorized</span>
                            <span className="text-gray-900 font-medium">
                              {formatDate(result.stay_start_date)}{result.stay_end_date ? ` – ${formatDate(result.stay_end_date)}` : ''}
                            </span>
                          </div>
                        )}
                        {result.checked_in_at && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Became active</span>
                            <span className="text-gray-900 font-medium">{formatDateTime(result.checked_in_at)}</span>
                          </div>
                        )}
                        {result.status === 'REVOKED' && result.revoked_at && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Revoked at</span>
                            <span className="text-gray-900 font-medium">{formatDateTime(result.revoked_at)}</span>
                          </div>
                        )}
                        {result.status === 'COMPLETED' && result.checked_out_at && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Ended at</span>
                            <span className="text-gray-900 font-medium">{formatDateTime(result.checked_out_at)}</span>
                          </div>
                        )}
                        {result.cancelled_at && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Cancelled at</span>
                            <span className="text-gray-900 font-medium">{formatDateTime(result.cancelled_at)}</span>
                          </div>
                        )}
                        {result.status === 'EXPIRED' && result.stay_end_date && (
                          <div className="flex justify-between gap-4">
                            <span className="text-gray-500">Expired</span>
                            <span className="text-gray-900 font-medium">{formatDate(result.stay_end_date)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Authorization history (archived records) */}
                  {result.authorization_history && result.authorization_history.length > 1 && (
                    <div className="rounded-lg border border-gray-200 bg-gray-50/50 p-4 print:bg-white print:border-gray-300">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Authorization history</h3>
                      <div className="space-y-2">
                        {result.authorization_history.map((auth) => (
                          <div key={auth.authorization_number} className="flex items-center justify-between text-sm p-2 rounded-lg bg-white border border-gray-100">
                            <div>
                              <span className="font-medium text-gray-800">Authorization #{auth.authorization_number}</span>
                              <span className="text-gray-500 ml-2">{auth.guest_name}</span>
                              {auth.start_date && <span className="text-gray-400 ml-2 text-xs">{formatDate(auth.start_date)}{auth.end_date ? ` – ${formatDate(auth.end_date)}` : ''}</span>}
                            </div>
                            <span className={`text-xs font-semibold uppercase tracking-wide px-2 py-0.5 rounded ${STATUS_COLORS[auth.status] || 'bg-gray-100 text-gray-600'}`}>{auth.status}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Documents section */}
                  <div className="rounded-lg border-2 border-[hsl(265,89%,66%)]/40 bg-[hsl(265,89%,66%)]/10 p-4 print:border-blue-300 print:bg-blue-50/50">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[hsl(265,89%,76%)] mb-3 print:text-blue-800">Documents</h3>
                    <div className="flex flex-wrap gap-3">
                      {result.signed_agreement_available && result.signed_agreement_url && (
                        <a href={`${API_URL}${result.signed_agreement_url}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[hsl(265,89%,66%)] hover:bg-[hsl(265,75%,58%)] text-white text-sm font-semibold transition-colors">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                          View Authorization Agreement
                        </a>
                      )}
                      {result.poa_url && (
                        <a href={`${API_URL}${result.poa_url}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[hsl(265,89%,66%)] hover:bg-[hsl(265,75%,58%)] text-white text-sm font-semibold transition-colors">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                          View Power of Attorney
                        </a>
                      )}
                      <button type="button" onClick={() => setShowLedger(!showLedger)} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 text-sm font-semibold transition-colors">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" /></svg>
                        {showLedger ? 'Hide' : 'View'} Activity Ledger
                      </button>
                      <button type="button" onClick={() => window.print()} className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-white/10 hover:bg-white/20 text-white border border-white/20 text-sm font-semibold transition-colors print:hidden">
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" /></svg>
                        Print Evidence Snapshot
                      </button>
                    </div>
                    {!result.signed_agreement_available && !result.poa_url && (
                      <p className="text-sm text-white/60 mt-2">No signed documents available for this record.</p>
                    )}
                  </div>

                  {/* Authority & links */}
                  <div className="space-y-3 pt-2 border-t border-white/10">
                    {result.poa_signed_at && (
                      <p className="text-sm text-white/70">Property documented under Master POA (signed {formatDate(result.poa_signed_at)}).</p>
                    )}
                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      {result.live_slug && (
                        <a href={`${APP_ORIGIN}/#live/${result.live_slug}`} target="_blank" rel="noopener noreferrer" className="text-[hsl(265,89%,76%)] hover:text-[hsl(265,89%,86%)] font-medium hover:underline inline-flex items-center gap-1">
                          Open full evidence page
                          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" /></svg>
                        </a>
                      )}
                    </div>
                  </div>

                  {/* Verification timestamp */}
                  <div className="rounded-lg bg-white/5 border border-white/10 p-3 text-center print:bg-gray-50 print:border-gray-200">
                    <p className="text-sm font-semibold text-white/90 print:text-slate-700">
                      {result.verified_at ? `Verified: ${formatDateTime(result.verified_at)}` : ''}
                    </p>
                    <p className="text-xs text-white/60 mt-0.5 print:text-slate-500">Source: {result.verification_source || 'DocuStay Verification Portal'}</p>
                    {result.live_slug && <p className="text-xs text-white/50 mt-0.5 print:text-slate-400">Record ID: {result.live_slug}</p>}
                  </div>
                </>
              )}
            </div>

            {/* Activity ledger (toggled) */}
            {hasRecord(result) && (showLedger || false) && result.audit_entries && result.audit_entries.length > 0 && (
              <div className="border-t border-white/10 px-6 py-4 bg-white/5 print:bg-white print:block">
                <h3 className="text-xs font-bold uppercase tracking-wider text-white/60 mb-3 print:text-gray-500">Activity ledger</h3>
                <ul className="space-y-2 text-sm text-white/80 max-h-72 overflow-y-auto print:max-h-none print:text-gray-700">
                  {result.audit_entries.map((entry, i) => (
                    <li key={i} className="flex gap-3 items-start">
                      <span className="text-white/50 shrink-0 text-xs whitespace-nowrap print:text-gray-400">{entry.created_at ? formatDateTime(entry.created_at) : '—'}</span>
                      <span>{entry.message || entry.title}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Always show ledger in print */}
            {hasRecord(result) && !showLedger && result.audit_entries && result.audit_entries.length > 0 && (
              <div className="hidden print:block border-t border-gray-200 px-6 py-4 bg-white">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-500 mb-3">Activity ledger</h3>
                <ul className="space-y-2 text-sm text-gray-700">
                  {result.audit_entries.map((entry, i) => (
                    <li key={i} className="flex gap-3 items-start">
                      <span className="text-gray-400 shrink-0 text-xs whitespace-nowrap">{entry.created_at ? formatDateTime(entry.created_at) : '—'}</span>
                      <span>{entry.message || entry.title}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        )}

        <footer className="text-center text-xs text-white/60 pt-6 print:pt-2 print:text-gray-500">
          <p className="font-medium text-white/70 print:text-gray-600">DocuStay Verify</p>
          <p className="mt-0.5 text-white/50 print:text-gray-400">Read-only · All attempts are logged</p>
        </footer>
      </div>
    </div>
  );
};
