import React, { useState, useEffect } from 'react';
import { publicApi, type PortfolioPagePayload } from '../services/api';

export const PortfolioPage: React.FC<{ slug: string }> = ({ slug }) => {
  const [data, setData] = useState<PortfolioPagePayload | null>(null);
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
      .getPortfolio(slug)
      .then(setData)
      .catch((e) => setError((e as Error)?.message ?? 'Failed to load'))
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[hsl(230,35%,4%)]">
        <div className="text-center">
          <div className="inline-block w-10 h-10 border-2 border-white/20 border-t-[hsl(265,89%,66%)] rounded-full animate-spin mb-4" />
          <p className="text-white/80 font-medium">Loading portfolio…</p>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 bg-[hsl(230,35%,4%)]">
        <div className="max-w-md w-full rounded-2xl glass border border-white/10 p-10 text-center">
          <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center mx-auto mb-4">
            <svg className="w-7 h-7 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h1 className="text-xl font-semibold text-white mb-2">Portfolio not found</h1>
          <p className="text-white/70">{error ?? 'This link may be invalid or expired.'}</p>
        </div>
      </div>
    );
  }

  const { owner, properties } = data;
  const displayName = (owner.full_name || owner.email || 'Property Owner').trim() || 'Property Owner';
  const hasContact = owner.email || owner.phone || owner.state;

  return (
    <div className="min-h-screen bg-[hsl(230,35%,4%)] text-white">
      {/* Top bar – accent */}
      <div className="h-1.5 bg-gradient-to-r from-[hsl(265,89%,66%)] via-[hsl(265,75%,58%)] to-white/20" />

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 sm:py-14">
        {/* Hero / Owner card */}
        <header className="mb-12">
          <div className="rounded-2xl glass border border-white/10 overflow-hidden">
            <div className="flex flex-col sm:flex-row">
              <div className="sm:w-48 flex-shrink-0 p-8 sm:p-10 bg-gradient-to-br from-[hsl(265,89%,66%)]/30 to-[hsl(265,75%,58%)]/20 flex items-center justify-center border-b sm:border-b-0 sm:border-r border-white/10">
                <div className="w-20 h-20 rounded-2xl bg-white/15 backdrop-blur flex items-center justify-center font-bold text-3xl text-white border border-white/20">
                  {displayName.charAt(0).toUpperCase()}
                </div>
              </div>
              <div className="flex-1 min-w-0 p-8 sm:p-10">
                <p className="text-xs font-semibold uppercase tracking-wider text-[hsl(265,89%,66%)] mb-1">Portfolio</p>
                <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">{displayName}</h1>
                <p className="text-white/60 text-sm mt-1">DocuStay verified property owner</p>
                {hasContact && (
                  <div className="mt-6 pt-6 border-t border-white/10 space-y-3">
                    {owner.email && (
                      <div className="flex items-center gap-3">
                        <span className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </span>
                        <div className="min-w-0">
                          <p className="text-xs font-medium text-white/60 uppercase tracking-wider">Email</p>
                          <a href={`mailto:${owner.email}`} className="text-white font-medium hover:text-[hsl(265,89%,66%)] transition-colors break-all">
                            {owner.email}
                          </a>
                        </div>
                      </div>
                    )}
                    {owner.phone && (
                      <div className="flex items-center gap-3">
                        <span className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                          </svg>
                        </span>
                        <div>
                          <p className="text-xs font-medium text-white/60 uppercase tracking-wider">Phone</p>
                          <a href={`tel:${owner.phone}`} className="text-white font-medium hover:text-[hsl(265,89%,66%)] transition-colors">
                            {owner.phone}
                          </a>
                        </div>
                      </div>
                    )}
                    {owner.state && (
                      <div className="flex items-center gap-3">
                        <span className="flex-shrink-0 w-9 h-9 rounded-lg bg-white/10 flex items-center justify-center">
                          <svg className="w-4 h-4 text-white/70" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                        </span>
                        <div>
                          <p className="text-xs font-medium text-white/60 uppercase tracking-wider">State</p>
                          <p className="text-white font-medium">{owner.state}</p>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Properties section */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
            <h2 className="text-sm font-semibold uppercase tracking-wider text-white/70">Properties</h2>
            <div className="h-px flex-1 bg-gradient-to-r from-transparent via-white/20 to-transparent" />
          </div>
          {properties.length === 0 ? (
            <div className="rounded-2xl border border-white/10 glass p-12 text-center">
              <div className="w-14 h-14 rounded-xl bg-white/10 flex items-center justify-center mx-auto mb-4">
                <svg className="w-7 h-7 text-white/50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                </svg>
              </div>
              <p className="text-white/80 font-medium">No properties listed yet.</p>
              <p className="text-white/50 text-sm mt-1">Check back later for updates.</p>
            </div>
          ) : (
            <div className="grid gap-5 sm:grid-cols-2">
              {properties.map((prop) => (
                <div
                  key={prop.id}
                  className="rounded-2xl border border-white/10 glass p-6 hover:border-white/20 transition-all duration-200"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <h3 className="font-semibold text-white text-lg truncate">
                        {prop.name || `${prop.city}, ${prop.state}`}
                      </h3>
                      <p className="text-white/70 text-sm mt-1 flex items-center gap-1.5">
                        <svg className="w-4 h-4 text-white/50 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        </svg>
                        {prop.city}, {prop.state}
                      </p>
                    </div>
                    <span className="flex-shrink-0 inline-flex items-center px-2.5 py-1 rounded-lg bg-[hsl(265,89%,66%)]/20 text-[hsl(265,89%,66%)] text-xs font-medium border border-[hsl(265,89%,66%)]/30">
                      {prop.region_code}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-white/10">
                    {prop.property_type_label && (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-white/10 text-white/80 text-xs font-medium">
                        {prop.property_type_label.replace(/_/g, ' ')}
                      </span>
                    )}
                    {prop.is_multi_unit ? (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-white/10 text-white/80 text-xs font-medium">
                        {prop.unit_count != null && prop.unit_count > 0
                          ? `${prop.unit_count} unit${prop.unit_count !== 1 ? 's' : ''}`
                          : 'Multi-unit'}
                      </span>
                    ) : prop.bedrooms ? (
                      <span className="inline-flex items-center px-2.5 py-1 rounded-lg bg-white/10 text-white/80 text-xs font-medium">
                        {prop.bedrooms} bed{prop.bedrooms !== '1' ? 's' : ''}
                      </span>
                    ) : null}
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Footer */}
        <footer className="mt-14 pt-8 border-t border-white/10 flex flex-col sm:flex-row items-center justify-between gap-4 text-white/50 text-sm">
          <span>Powered by DocuStay</span>
          <a
            href="#"
            className="text-[hsl(265,89%,66%)] hover:text-[hsl(265,75%,58%)] font-medium transition-colors"
            onClick={(e) => e.preventDefault()}
          >
            docustay.com
          </a>
        </footer>
      </div>
    </div>
  );
};
