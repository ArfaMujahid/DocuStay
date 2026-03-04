import React, { useState, useEffect } from 'react';
import { publicApi, type LivePropertyPagePayload } from '../services/api';

function formatDate(s: string): string {
  return new Date(s).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatDateTime(s: string): string {
  return new Date(s).toLocaleString('en-US', { dateStyle: 'short', timeStyle: 'short' });
}

function statusDisplay(status: string): string {
  const s = (status || 'unknown').toLowerCase();
  if (s === 'vacant') return 'VACANT';
  if (s === 'occupied') return 'OCCUPIED';
  if (s === 'unconfirmed') return 'UNCONFIRMED';
  return 'UNKNOWN';
}

function authDisplay(auth: string): string {
  const a = (auth || 'none').toUpperCase();
  if (a === 'ACTIVE' || a === 'NONE' || a === 'EXPIRED' || a === 'REVOKED') return a;
  return 'NONE';
}

function tokenDisplay(token: string): string {
  const t = (token || 'staged').toLowerCase();
  return t === 'released' ? 'RELEASED' : 'STAGED';
}

export const LivePropertyPage: React.FC<{ slug: string }> = ({ slug }) => {
  const [data, setData] = useState<LivePropertyPagePayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!slug) {
      setError('Invalid link');
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    publicApi
      .getLivePage(slug)
      .then(setData)
      .catch((e) => setError((e as Error)?.message ?? 'Failed to load'))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-100/60 via-blue-50/30 to-sky-50/50 flex items-center justify-center p-6 print:bg-white">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-2 border-blue-200 border-t-blue-700 rounded-full animate-spin mb-4" />
          <p className="text-slate-700 font-medium">Loading property information…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-blue-100/60 via-blue-50/30 to-sky-50/50 flex items-center justify-center p-6 print:bg-white">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-lg border border-blue-200/60 p-10 text-center">
          <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-slate-800 mb-2">Property not found</h1>
          <p className="text-slate-600">{error ?? 'This link may be invalid or expired.'}</p>
        </div>
      </div>
    );
  }

  const {
    property: prop,
    owner,
    has_current_guest,
    current_guest,
    last_stay,
    upcoming_stays,
    logs,
    authorization_state,
    record_id,
    generated_at,
    poa_signed_at,
    poa_signature_id,
  } = data;

  const address = [prop.street, prop.city, prop.state, prop.zip_code].filter(Boolean).join(', ');
  const statusLabel = statusDisplay(prop.occupancy_status);
  const authLabel = authDisplay(authorization_state);
  const tokenLabel = tokenDisplay(prop.token_state ?? 'staged');
  const isVacant = (prop.occupancy_status || '').toLowerCase() === 'vacant' && !has_current_guest;
  const liveLink = typeof window !== 'undefined' ? window.location.href : `#live/${slug}`;
  const poaPdfUrl = publicApi.getLivePoaPdfUrl(slug);

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-100/60 via-blue-50/30 to-sky-50/50 print:bg-white print:min-h-0">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8 print:py-6 print:max-w-none">
        {/* Evidence header: Record ID, timestamp, live link */}
        <div className="bg-white rounded-xl border border-slate-200/80 px-4 py-3 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm print:border print:rounded print:shadow-none">
          <span className="font-medium text-slate-700">
            Record ID: <span className="font-mono text-slate-900">{record_id}</span>
          </span>
          <span className="text-slate-600">
            Generated: {formatDateTime(generated_at)}
          </span>
          <span className="text-slate-600 break-all">
            Live link: <a href={liveLink} className="text-blue-600 underline print:no-underline" target="_blank" rel="noopener noreferrer">{liveLink}</a>
          </span>
          <button
            type="button"
            onClick={() => window.print()}
            className="ml-auto px-3 py-1.5 rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 text-sm font-medium print:hidden"
          >
            Print
          </button>
        </div>

        {/* 1. Quick Decision Layer */}
        <section className="bg-white rounded-2xl shadow-sm border border-blue-200/60 overflow-hidden print:rounded print:shadow-none print:border">
          <div className="px-6 py-4 bg-blue-50/80 border-b border-blue-200/60 print:bg-slate-50 print:border-slate-200">
            <h2 className="text-sm font-bold uppercase tracking-wider text-blue-700 print:text-slate-700">Quick decision layer</h2>
          </div>
          <div className="p-6 sm:p-8 space-y-4">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Property address</p>
              <p className="text-lg font-semibold text-slate-900 mt-0.5">{address || '—'}</p>
            </div>
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Verified owner</p>
              <p className="text-slate-900 mt-0.5">{owner.full_name ?? '—'}</p>
            </div>
            <div className="flex flex-wrap gap-3 items-center">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Status</span>
              <span
                className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold uppercase ${
                  statusLabel === 'OCCUPIED'
                    ? 'bg-emerald-100 text-emerald-800'
                    : statusLabel === 'VACANT'
                      ? 'bg-sky-100 text-sky-800'
                      : 'bg-slate-100 text-slate-700'
                }`}
              >
                {statusLabel}
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Authorization</span>
              <span
                className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold uppercase ${
                  authLabel === 'ACTIVE'
                    ? 'bg-emerald-100 text-emerald-800'
                    : authLabel === 'REVOKED'
                      ? 'bg-red-100 text-red-800'
                      : authLabel === 'EXPIRED'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-slate-100 text-slate-700'
                }`}
              >
                {authLabel}
              </span>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Token</span>
              <span className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold uppercase bg-slate-100 text-slate-700">
                {tokenLabel}
              </span>
            </div>
            {isVacant && (
              <div className="pt-2 border-t border-slate-200">
                <p className="text-sm text-slate-600">
                  Status: VACANT · Authorization: NONE · Token: STAGED
                </p>
              </div>
            )}
            {has_current_guest && current_guest && (
              <div>
                <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">Tenant (active)</p>
                <p className="text-slate-900 font-medium mt-0.5">{current_guest.guest_name}</p>
                <p className="text-slate-600 text-sm mt-0.5">
                  {formatDate(current_guest.stay_start_date)} – {formatDate(current_guest.stay_end_date)}
                </p>
              </div>
            )}
          </div>
        </section>

        {/* 2. Authority Layer */}
        <section className="bg-white rounded-2xl shadow-sm border border-blue-200/60 overflow-hidden print:rounded print:shadow-none print:border">
          <div className="px-6 py-4 bg-blue-50/80 border-b border-blue-200/60 print:bg-slate-50 print:border-slate-200">
            <h2 className="text-sm font-bold uppercase tracking-wider text-blue-700 print:text-slate-700">Authority layer</h2>
          </div>
          <div className="p-6 sm:p-8 space-y-4">
            <p className="text-slate-700">
              This property is documented under a signed <strong>Master Power of Attorney (POA)</strong>.
            </p>
            {poa_signed_at && (
              <p className="text-slate-700">
                POA signed: <strong>{formatDate(poa_signed_at)}</strong>. Owner entity: <strong>{owner.full_name ?? '—'}</strong>.
              </p>
            )}
            <p className="text-slate-600 text-sm">
              DocuStay operates under the granted documentation authority of the owner. Records are immutable and append-only.
            </p>
            {poa_signature_id != null && (
              <a
                href={poaPdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 print:no-underline print:text-slate-900 print:border print:border-slate-300 print:bg-transparent"
              >
                View POA
              </a>
            )}
          </div>
        </section>

        {/* 3. Condensed Audit Timeline */}
        <section className="bg-white rounded-2xl shadow-sm border border-blue-200/60 overflow-hidden print:rounded print:shadow-none print:border">
          <div className="px-6 py-4 bg-blue-50/80 border-b border-blue-200/60 print:bg-slate-50 print:border-slate-200">
            <h2 className="text-sm font-bold uppercase tracking-wider text-blue-700 print:text-slate-700">Condensed audit timeline</h2>
          </div>
          <div className="p-6 sm:p-8">
            {logs.length === 0 ? (
              <p className="text-slate-500 text-sm">No activity recorded yet.</p>
            ) : (
              <ul className="space-y-0 max-h-[28rem] overflow-y-auto pr-1 print:max-h-none">
                {logs.map((entry, i) => (
                  <li key={i} className="relative pl-6 pb-6 last:pb-0">
                    {i < logs.length - 1 && (
                      <span className="absolute left-[5px] top-2 bottom-0 w-px bg-blue-200 print:bg-slate-200" />
                    )}
                    <span className="absolute left-0 top-0.5 w-2.5 h-2.5 rounded-full bg-blue-400 border-2 border-white shadow-sm print:bg-slate-400 print:border-white" />
                    <div className="pt-0.5">
                      <p className="font-medium text-slate-800">{entry.title}</p>
                      <p className="text-slate-600 text-sm mt-0.5">{entry.message}</p>
                      <p className="text-xs text-slate-400 mt-2 flex items-center gap-2">
                        <span className="inline-flex px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium print:bg-slate-100 print:text-slate-700">
                          {entry.category.replace(/_/g, ' ')}
                        </span>
                        {formatDateTime(entry.created_at)}
                      </p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        {/* Optional: last stay / upcoming (condensed) */}
        {!has_current_guest && (last_stay || upcoming_stays.length > 0) && (
          <section className="bg-white rounded-2xl shadow-sm border border-slate-200/80 overflow-hidden print:rounded print:shadow-none print:border">
            <div className="px-6 py-3 border-b border-slate-200">
              <h2 className="text-sm font-bold uppercase tracking-wider text-slate-600">Last / upcoming</h2>
            </div>
            <div className="p-4 flex flex-wrap gap-6 text-sm">
              {last_stay && (
                <div>
                  <span className="text-slate-500">Last: </span>
                  <span className="text-slate-800">{last_stay.guest_name}</span>
                  <span className="text-slate-500 ml-1">
                    {formatDate(last_stay.stay_start_date)} – {formatDate(last_stay.stay_end_date)}
                  </span>
                </div>
              )}
              {upcoming_stays.slice(0, 3).map((s, i) => (
                <div key={i}>
                  <span className="text-slate-500">Upcoming: </span>
                  <span className="text-slate-800">{s.guest_name}</span>
                  <span className="text-slate-500 ml-1">
                    {formatDate(s.stay_start_date)} – {formatDate(s.stay_end_date)}
                  </span>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Footer */}
        <footer className="pt-4 pb-8 text-center print:pt-2 print:pb-4">
          <p className="text-xs text-slate-500 font-medium">DocuStay · Live evidence page · Read-only</p>
          <p className="text-xs text-slate-400 mt-1">Record ID: {record_id} · Generated: {formatDateTime(generated_at)}</p>
        </footer>
      </div>

      <style>{`
        @media print {
          body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          .print\\:bg-white { background: white !important; }
          .print\\:max-h-none { max-height: none !important; }
        }
      `}</style>
    </div>
  );
};
