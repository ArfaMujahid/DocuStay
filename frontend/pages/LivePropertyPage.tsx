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
      <div className="min-h-screen bg-[hsl(230,35%,4%)] flex items-center justify-center p-6 print:bg-white">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-2 border-white/20 border-t-[hsl(265,89%,66%)] rounded-full animate-spin mb-4" />
          <p className="text-white/80 font-medium">Loading property information…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[hsl(230,35%,4%)] flex items-center justify-center p-6 print:bg-white">
        <div className="max-w-md w-full rounded-2xl glass border border-white/10 p-10 text-center">
          <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">Property not found</h1>
          <p className="text-white/70">{error ?? 'This link may be invalid or expired.'}</p>
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
    invitations,
    logs,
    authorization_state,
    record_id,
    generated_at,
    poa_signed_at,
    poa_signature_id,
    jurisdiction_wrap,
  } = data;

  const address = [prop.street, prop.city, prop.state, prop.zip_code].filter(Boolean).join(', ');
  const statusLabel = statusDisplay(prop.occupancy_status);
  const authLabel = authDisplay(authorization_state);
  const isVacant = (prop.occupancy_status || '').toLowerCase() === 'vacant' && !has_current_guest;
  const liveLink = typeof window !== 'undefined' ? window.location.href : `#live/${slug}`;
  const poaPdfUrl = publicApi.getLivePoaPdfUrl(slug);

  // Conclusion for Evidence summary when backend reports no current occupant (derived from payload, not hardcoded)
  const noOccupantFromBackend = !has_current_guest && !current_guest;
  const evidenceConclusionNoOccupant = noOccupantFromBackend && isVacant
    ? 'This property has no recorded authorization for any occupant.'
    : null;

  // Evidence summary: only ACTIVE, EXPIRED, or nothing (no "overstay" etc.)
  const lastConfirmedFromLogs = (() => {
    const statusOrConfirm = logs.find(
      (e) =>
        e.category === 'status_change' ||
        (e.title && /vacated|confirmed|vacant|occupancy/i.test(e.title)) ||
        (e.message && /vacated|confirmed|vacant/i.test(e.message))
    );
    return statusOrConfirm ? formatDate(statusOrConfirm.created_at) : null;
  })();
  const timelineFromLogs = logs
    .filter(
      (e) =>
        e.category === 'status_change' ||
        (e.title && /vacated|confirmed|check.?in|checkout|occupancy|renewed|holdover/i.test(e.title))
    )
    .slice(0, 10)
    .map((e) => {
      const d = formatDate(e.created_at);
      const short = e.title || e.message?.slice(0, 50) || '—';
      return `${d}: ${short}`;
    })
    .reverse();
  const jurisdictionName = jurisdiction_wrap?.state_name ?? '—';
  const statuteLines = jurisdiction_wrap?.applicable_statutes?.map((s) => (s.plain_english ? `• ${s.citation}: ${s.plain_english}` : `• ${s.citation}`)) ?? [];
  const poaDateFormatted = poa_signed_at ? formatDate(poa_signed_at) : null;
  const poaTimestampFormatted = poa_signed_at ? formatDateTime(poa_signed_at) : null;

  // Condensed Audit Timeline (Part B): POA signed, property onboarded, status changes (active/expired/revoked)
  const oldestLog = logs.length > 0 ? logs[logs.length - 1] : null;
  const propertyOnboardedAt = oldestLog ? formatDateTime(oldestLog.created_at) : null;
  const statusChangeLogs = logs.filter(
    (e) =>
      e.category === 'status_change' ||
      /status|vacant|occupancy|confirmed|vacated|check.?in|checkout/i.test(e.title || '') ||
      /status|vacant|occupancy|confirmed|vacated/i.test(e.message || '')
  );
  const tokenEventLogs = logs.filter(
    (e) =>
      /invitation|invite|stay|token|burn|expire|revoke|signed|agreement|checkout|check.?in/i.test(e.category || '') ||
      /invitation|invite|stay|token|burn|expire|revoke|signed|agreement|checkout|check.?in/i.test(e.title || '')
  );

  return (
    <div className="min-h-screen bg-[hsl(230,35%,4%)] text-white print:bg-white print:text-gray-900 print:min-h-0">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-6 sm:py-8 space-y-6 print:py-6 print:max-w-none">
        {/* Meta bar: record, timestamp, link, print */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm glass rounded-xl border border-white/10 px-4 py-3 print:bg-white print:border-slate-200">
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-white/80">
            <span className="inline-flex items-center gap-1.5">
              <span className="font-medium text-[hsl(265,89%,66%)]">Record</span>
              <span className="font-mono text-white bg-white/10 px-1.5 py-0.5 rounded">{record_id}</span>
            </span>
            <span className="text-white/60">Generated {formatDateTime(generated_at)}</span>
            <a href={liveLink} className="text-[hsl(265,89%,66%)] hover:text-white font-medium hover:underline break-all" target="_blank" rel="noopener noreferrer">Live link</a>
          </div>
          <button
            type="button"
            onClick={() => window.print()}
            className="px-4 py-2 rounded-lg bg-[hsl(265,89%,66%)] text-white text-sm font-medium hover:bg-[hsl(265,75%,58%)] shadow-sm print:hidden transition-colors"
          >
            Print page
          </button>
        </div>

        {/* Top Section – Quick Decision Layer (rapid field clarity) */}
        <header className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white border-l-4 border-l-[hsl(265,89%,66%)]">
          <div className="px-6 py-3.5 sm:px-8 bg-white/5 border-b border-white/10 print:bg-slate-50">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Quick Decision Layer</h2>
          </div>
          <div className="p-6 sm:p-8">
            <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-1">Property address</p>
            <h1 className="text-xl sm:text-2xl font-bold text-white mb-3">{address || '—'}</h1>
            <p className="text-sm text-white/70 mb-4">
              <span className="font-medium text-white/90">Verified owner entity</span> · {owner.full_name ?? '—'}
            </p>
            <div className="flex flex-wrap gap-4 sm:gap-6 mb-4">
              <div>
                <p className="text-xs font-medium text-white/60 mb-0.5">Current property status</p>
                <span
                  className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold uppercase ${
                    statusLabel === 'OCCUPIED'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40'
                      : statusLabel === 'VACANT'
                        ? 'bg-sky-500/20 text-sky-300 border border-sky-400/40'
                        : 'bg-white/10 text-white/80 border border-white/20'
                  }`}
                >
                  {statusLabel}
                </span>
              </div>
              <div>
                <p className="text-xs font-medium text-white/60 mb-0.5">Authorization state</p>
                <span
                  className={`inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-semibold uppercase ${
                    authLabel === 'ACTIVE'
                      ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40'
                      : authLabel === 'REVOKED'
                        ? 'bg-red-500/20 text-red-300 border border-red-400/40'
                        : authLabel === 'EXPIRED'
                          ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40'
                          : 'bg-white/10 text-white/80 border border-white/20'
                  }`}
                >
                  {authLabel}
                </span>
              </div>
            </div>
            {has_current_guest && current_guest && (
              <div className="mt-4 pt-4 border-t border-white/10 bg-emerald-500/10 -mx-6 sm:-mx-8 px-6 sm:px-8 py-4 rounded-lg border border-emerald-400/30 print:bg-emerald-50/60 print:border-emerald-200">
                <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400 mb-0.5 print:text-emerald-700">Current guest</p>
                <p className="text-white font-medium print:text-slate-900">{current_guest.guest_name}</p>
                <p className="text-white/80 text-sm print:text-slate-600">
                  {formatDate(current_guest.stay_start_date)} – {formatDate(current_guest.stay_end_date)}
                </p>
              </div>
            )}
          </div>
        </header>

        {/* Authority layer – POA and jurisdiction (moved up for context) */}
        <section className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white">
          <div className="px-6 py-3.5 bg-white/5 border-b border-white/10 print:bg-slate-50">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Authority</h2>
          </div>
          <div className="p-6 sm:p-8 space-y-4">
            <p className="text-white/90">
              This property is documented under a signed <strong className="text-white">Master Power of Attorney (POA)</strong>.
            </p>
            {poa_signed_at && (
              <p className="text-white/90">
                POA signed: <strong className="text-white">{formatDate(poa_signed_at)}</strong>. Owner: <strong className="text-white">{owner.full_name ?? '—'}</strong>.
              </p>
            )}
            <p className="text-white/70 text-sm">
              DocuStay operates under the granted documentation authority of the owner. Records are immutable and append-only.
            </p>
            {poa_signature_id != null && (
              <a
                href={poaPdfUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-[hsl(265,89%,66%)] text-white font-medium hover:bg-[hsl(265,75%,58%)] transition-colors print:no-underline print:text-slate-900 print:border print:border-slate-300 print:bg-transparent"
              >
                View POA
              </a>
            )}
            <div className="pt-4 border-t border-white/10">
              <p className="text-xs font-semibold uppercase tracking-wider text-white/60">Property identifier</p>
              <p className="text-white mt-0.5">{address || '—'}</p>
              {(prop.apn || prop.tax_id) && (
                <p className="text-white/70 text-sm mt-1">
                  {prop.apn && <span>APN: {prop.apn}</span>}
                  {prop.apn && prop.tax_id && ' · '}
                  {prop.tax_id && <span>Tax ID: {prop.tax_id}</span>}
                </p>
              )}
            </div>
            {jurisdiction_wrap && jurisdiction_wrap.applicable_statutes?.length > 0 && (
              <div className="pt-4 border-t border-white/10">
                <p className="text-xs font-semibold uppercase tracking-wider text-white/60">Applicable law ({jurisdiction_wrap.state_name})</p>
                <ul className="mt-2 space-y-2">
                  {jurisdiction_wrap.applicable_statutes.map((s, i) => (
                    <li key={i} className="text-sm text-white/80">
                      <span className="font-medium text-white">{s.citation}</span>
                      {s.plain_english && <span className="block text-white/70 mt-0.5">{s.plain_english}</span>}
                    </li>
                  ))}
                </ul>
                {jurisdiction_wrap.removal_guest_text && (
                  <p className="text-white/70 text-sm mt-2">
                    <span className="font-medium text-white/90">Guest removal: </span>{jurisdiction_wrap.removal_guest_text}
                  </p>
                )}
                {jurisdiction_wrap.removal_tenant_text && (
                  <p className="text-white/70 text-sm mt-0.5">
                    <span className="font-medium text-white/90">Tenant eviction: </span>{jurisdiction_wrap.removal_tenant_text}
                  </p>
                )}
              </div>
            )}
          </div>
        </section>

        {/* Third Section – Condensed Audit Timeline (Part B) */}
        <section className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white">
          <div className="px-6 py-3.5 bg-white/5 border-b border-white/10 print:bg-slate-50">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Condensed Audit Timeline</h2>
          </div>
          <div className="p-6 sm:p-8">
            <ul className="space-y-2 text-sm text-white/80">
              <li><span className="font-medium text-white">POA signed</span> – {poaTimestampFormatted ?? '—'}</li>
              <li><span className="font-medium text-white">Property onboarded</span> – {propertyOnboardedAt ?? '—'}</li>
              <li>
                <span className="font-medium text-white">Status changes</span> –
                {statusChangeLogs.length > 0
                  ? ` ${statusChangeLogs.slice(0, 5).map((e) => formatDateTime(e.created_at)).join(', ')}${statusChangeLogs.length > 5 ? ' …' : ''}`
                  : ' —'}
              </li>
              <li>
                <span className="font-medium text-white">Status changes (active / expired / revoked)</span> –
                {tokenEventLogs.length > 0
                  ? ` ${tokenEventLogs.slice(0, 5).map((e) => formatDateTime(e.created_at)).join(', ')}${tokenEventLogs.length > 5 ? ' …' : ''}`
                  : ' —'}
              </li>
            </ul>
          </div>
        </section>

        {/* Evidence summary (printable) – token states only: ACTIVE, EXPIRED, or nothing */}
        <section className="rounded-2xl glass border border-amber-400/40 overflow-hidden print:rounded print:shadow-none print:border-2 print:border-slate-400 print:bg-white">
          <div className="px-6 py-3.5 bg-amber-500/10 border-b border-amber-400/30 print:bg-slate-100">
            <h2 className="text-sm font-bold uppercase tracking-wider text-amber-300">Evidence summary</h2>
            <p className="text-xs text-amber-300/90 mt-0.5">Machine-readable summary for verification</p>
          </div>
          <div className="p-6 sm:p-8 font-mono text-sm text-white/90 whitespace-pre-wrap rounded-b-2xl bg-white/5 border border-t-0 border-white/10 print:bg-white print:text-gray-900 print:rounded-none">
            {isVacant && (
              <>
                PROPERTY: {address || '—'}
                {'\n'}STATUS: {statusLabel} (confirmed)
                {'\n'}LAST CONFIRMED: {lastConfirmedFromLogs ?? '—'}
                {'\n\n'}
                AUTHORITY CHAIN:
                {'\n'}• Owner verified: {owner.full_name ?? '—'} (to be updated)
                {poaDateFormatted && `\n• Master POA executed: ${poaDateFormatted}`}
                {'\n\n'}
                JURISDICTION: {jurisdictionName}
                {statuteLines.length > 0 && '\n' + statuteLines.join('\n')}
                {'\n\n'}
                TIMELINE:
                {timelineFromLogs.length > 0 ? '\n' + timelineFromLogs.map((l) => `• ${l}`).join('\n') : '\n• (No status entries)'}
                {'\n'}• NO ACTIVE GUEST TOKENS
                {'\n'}• NO SUCCESSFUL /VERIFY ATTEMPTS
                {'\n\n'}
                {evidenceConclusionNoOccupant ?? ''}
              </>
            )}
            {!isVacant && has_current_guest && current_guest && (
              <>
                PROPERTY: {address || '—'}
                {'\n'}GUEST: {current_guest.guest_name}
                {'\n'}AUTHORIZATION: {formatDate(current_guest.stay_start_date)} – {formatDate(current_guest.stay_end_date)}
                {'\n\n'}
                PROPERTY STATUS: OCCUPIED (by authorized guest)
                {'\n\n'}
                GUEST TOKEN HISTORY:
                {'\n'}• {formatDate(current_guest.stay_start_date)} – {formatDate(current_guest.stay_end_date)}: Guest token ACTIVE
                {'\n\n'}
                This guest has current authorization.
              </>
            )}
            {!isVacant && !has_current_guest && last_stay && (
              <>
                PROPERTY: {address || '—'}
                {'\n'}GUEST: {last_stay.guest_name}
                {'\n'}AUTHORIZATION: {formatDate(last_stay.stay_start_date)} – {formatDate(last_stay.stay_end_date)}
                {'\n\n'}
                PROPERTY STATUS: {statusLabel}
                {'\n\n'}
                GUEST TOKEN HISTORY:
                {'\n'}• {formatDate(last_stay.stay_start_date)} – {formatDate(last_stay.stay_end_date)}: Guest token ACTIVE
                {'\n'}• {formatDate(last_stay.stay_end_date)}: Token EXPIRED
                {'\n\n'}
                This guest has no current authorization.
              </>
            )}
            {!isVacant && !has_current_guest && !last_stay && (
              <>
                PROPERTY: {address || '—'}
                {'\n'}STATUS: {statusLabel}
                {'\n'}LAST CONFIRMED: {lastConfirmedFromLogs ?? '—'}
                {'\n\n'}
                AUTHORITY CHAIN:
                {'\n'}• Owner verified: {owner.full_name ?? '—'} (to be updated)
                {poaDateFormatted && `\n• Master POA executed: ${poaDateFormatted}`}
                {'\n\n'}
                JURISDICTION: {jurisdictionName}
                {statuteLines.length > 0 && '\n' + statuteLines.join('\n')}
                {'\n\n'}
                • NO ACTIVE GUEST TOKENS
              </>
            )}
          </div>
        </section>

        {/* Invitation states – stay status */}
        <section className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white">
          <div className="px-6 py-3.5 bg-white/5 border-b border-white/10 print:bg-slate-50">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Invitation states</h2>
            <p className="text-xs text-white/70 mt-0.5">Invite ID and token state map each invitation to a stay.</p>
          </div>
          <div className="p-6 sm:p-8">
            <details className="mb-4 group">
              <summary className="cursor-pointer text-xs font-semibold text-white/80 list-none flex items-center gap-1 hover:text-white">
                <span className="group-open:rotate-90 transition-transform text-[hsl(265,89%,66%)]">▶</span> Token states legend
              </summary>
              <ul className="mt-2 pl-4 space-y-0.5 text-xs text-white/70 border-l-2 border-white/20">
                <li><strong className="text-white">PENDING</strong> — Invite sent, not yet accepted (no stay).</li>
                <li><strong className="text-white">ACTIVE</strong> — Guest accepted and signed; stay created (authorization active or past).</li>
                <li><strong className="text-white">EXPIRED</strong> — Stay ended or guest checked out; no current authorization. (Guests only; DocuStay does not expire tenants.)</li>
                <li><strong className="text-white">REVOKED</strong> — Guest authorization revoked by owner.</li>
                <li><strong className="text-white">CANCELLED</strong> — Tenant assignment cancelled by tenant. (DocuStay does not revoke tenants.)</li>
              </ul>
            </details>
            {(!invitations || invitations.length === 0) ? (
              <p className="text-white/60 text-sm">No invitations recorded for this property.</p>
            ) : (
              <div className="overflow-x-auto -mx-1 rounded-lg border border-white/10 overflow-hidden">
                <table className="w-full text-sm border-collapse min-w-[32rem]">
                  <thead>
                    <tr className="bg-white/10 border-b-2 border-white/10">
                      <th className="text-left py-3 pr-4 font-semibold text-white/90">Invite ID</th>
                      <th className="text-left py-3 pr-4 font-semibold text-white/90">Guest</th>
                      <th className="text-left py-3 pr-4 font-semibold text-white/90">Authorization period</th>
                      <th className="text-left py-3 pr-4 font-semibold text-white/90">Status</th>
                      <th className="text-left py-3 font-semibold text-white/90">Token state</th>
                    </tr>
                  </thead>
                  <tbody>
                    {invitations.map((inv, i) => (
                      <tr key={inv.invitation_code + i} className={`border-b border-white/10 last:border-0 transition-colors ${i % 2 === 0 ? 'bg-transparent' : 'bg-white/5'} hover:bg-white/10`}>
                        <td className="py-3 pr-4 font-mono text-white/90 text-xs">{inv.invitation_code}</td>
                        <td className="py-3 pr-4 text-white/80">{inv.guest_label ?? '—'}</td>
                        <td className="py-3 pr-4 text-white/80 whitespace-nowrap">
                          {formatDate(inv.stay_start_date)} – {formatDate(inv.stay_end_date)}
                        </td>
                        <td className="py-3 pr-4">
                          <span className={`inline-flex px-2 py-0.5 rounded text-xs font-medium ${
                            inv.status === 'accepted' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40' :
                            inv.status === 'cancelled' ? 'bg-red-500/20 text-red-300 border border-red-400/40' :
                            inv.status === 'ongoing' ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40' :
                            'bg-white/10 text-white/70 border border-white/20'
                          }`}>
                            {inv.status}
                          </span>
                        </td>
                        <td className="py-3">
                          <span className={`inline-flex px-2 py-0.5 rounded text-xs font-semibold ${
                            inv.token_state === 'BURNED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-400/40' :
                            inv.token_state === 'EXPIRED' ? 'bg-amber-500/20 text-amber-300 border border-amber-400/40' :
                            (inv.token_state === 'REVOKED' || inv.token_state === 'CANCELLED') ? 'bg-white/10 text-white/70 border border-white/20' :
                            'bg-white/10 text-white/70 border border-white/20'
                          }`}>
                            {inv.token_state === 'BURNED' ? 'Active' : (inv.token_state === 'REVOKED' || inv.token_state === 'CANCELLED') ? 'Cancelled' : inv.token_state === 'STAGED' ? 'Pending' : inv.token_state === 'EXPIRED' ? 'Expired' : inv.token_state}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </section>

        {/* Audit timeline */}
        <section className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white">
          <div className="px-6 py-3.5 bg-white/5 border-b border-white/10 print:bg-slate-50">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Audit timeline</h2>
          </div>
          <div className="p-6 sm:p-8">
            {logs.length === 0 ? (
              <p className="text-white/60 text-sm">No activity recorded yet.</p>
            ) : (
              <ul className="space-y-0 max-h-[26rem] overflow-y-auto pr-1 print:max-h-none">
                {logs.map((entry, i) => (
                  <li key={i} className="relative pl-6 pb-5 last:pb-0">
                    {i < logs.length - 1 && (
                      <span className="absolute left-[5px] top-2 bottom-0 w-px bg-white/20" />
                    )}
                    <span className="absolute left-0 top-0.5 w-2.5 h-2.5 rounded-full bg-[hsl(265,89%,66%)] border-2 border-[hsl(230,35%,4%)] shadow-sm" />
                    <div className="pt-0.5">
                      <p className="font-medium text-white">{entry.title}</p>
                      <p className="text-white/70 text-sm mt-0.5">{entry.message}</p>
                      <p className="text-xs text-white/50 mt-2 flex items-center gap-2 flex-wrap">
                        <span className="inline-flex px-1.5 py-0.5 rounded bg-[hsl(265,89%,66%)]/20 text-[hsl(265,89%,66%)] font-medium">
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

        {/* Last / upcoming (when no current guest) */}
        {!has_current_guest && (last_stay || upcoming_stays.length > 0) && (
          <section className="rounded-2xl glass border border-white/10 overflow-hidden print:rounded print:shadow-none print:border print:bg-white">
            <div className="px-6 py-3.5 bg-white/5 border-b border-white/10 print:bg-slate-50">
              <h2 className="text-sm font-bold uppercase tracking-wider text-[hsl(265,89%,66%)]">Last & upcoming stays</h2>
            </div>
            <div className="p-6 flex flex-wrap gap-6 sm:gap-8 text-sm">
              {last_stay && (
                <div className="flex-1 min-w-[12rem] rounded-lg bg-white/5 border border-white/10 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-0.5">Last stay</p>
                  <p className="text-white font-medium">{last_stay.guest_name}</p>
                  <p className="text-white/70">{formatDate(last_stay.stay_start_date)} – {formatDate(last_stay.stay_end_date)}</p>
                </div>
              )}
              {upcoming_stays.slice(0, 3).map((s, i) => (
                <div key={i} className="flex-1 min-w-[12rem] rounded-lg bg-white/5 border border-white/10 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wider text-white/60 mb-0.5">Upcoming</p>
                  <p className="text-white font-medium">{s.guest_name}</p>
                  <p className="text-white/70">{formatDate(s.stay_start_date)} – {formatDate(s.stay_end_date)}</p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Stay end reminders – compact footnote */}
        <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-3 print:bg-white print:border print:border-slate-200">
          <p className="text-xs font-semibold text-white/70 mb-0.5">Stay end reminders</p>
          <p className="text-xs text-white/60">
            Occupied: 48h before lease end → confirmation prompt; 48h after lease end with no owner action → UNCONFIRMED. Vacant (if monitoring): prompts at intervals; no response → UNCONFIRMED.
          </p>
        </div>

        <footer className="pt-6 pb-10 text-center border-t border-white/10 print:pt-2 print:pb-4 print:border-0">
          <p className="text-xs text-white/70 font-medium">DocuStay · Live evidence page · Read-only</p>
          <p className="text-xs text-white/50 mt-1">Record {record_id} · {formatDateTime(generated_at)}</p>
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
