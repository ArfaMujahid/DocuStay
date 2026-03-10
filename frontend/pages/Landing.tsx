import React, { useState, useEffect } from 'react';
import { Button } from '../components/UI';

/** Role config with icons (Heroicons paths) */
const ROLES = [
  { id: 'owner', label: 'Owner', icon: 'M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4' },
  { id: 'property_manager', label: 'Property Manager', icon: 'M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z' },
  { id: 'tenant', label: 'Tenant', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { id: 'guest', label: 'Guest', icon: 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' },
];

/** High-quality property/home images (Unsplash – free to use, no watermark) */
const HERO_IMAGES = [
  'https://images.unsplash.com/photo-1600596542815-ffad4c1539a9?w=1920&q=80',
  'https://images.unsplash.com/photo-1580587771525-78b9dba3b914?w=1920&q=80',
  'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=1920&q=80',
  'https://images.unsplash.com/photo-1560448204-e02f11c3d0e2?w=1920&q=80',
  'https://images.unsplash.com/photo-1564013799919-ab600027ffc6?w=1920&q=80',
];

const CAROUSEL_INTERVAL_MS = 5000;

type LandingProps = {
  navigate: (view: string) => void;
};

const Landing: React.FC<LandingProps> = ({ navigate }) => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [roleSelector, setRoleSelector] = useState<'signup' | 'login' | null>(null);

  useEffect(() => {
    if (roleSelector) window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [roleSelector]);

  useEffect(() => {
    const t = setInterval(() => {
      setActiveIndex((i) => (i + 1) % HERO_IMAGES.length);
    }, CAROUSEL_INTERVAL_MS);
    return () => clearInterval(t);
  }, []);

  const onRoleSelect = (roleId: string) => {
    if (roleSelector === 'signup') {
      if (roleId === 'owner') navigate('register');
      else if (roleId === 'property_manager') navigate('register/manager');
      else if (roleId === 'tenant') navigate('guest-signup/tenant');
      else if (roleId === 'guest') navigate('guest-signup');
    } else {
      if (roleId === 'guest') navigate('guest-login');
      else if (roleId === 'owner') navigate('login');
      else if (roleId === 'property_manager') navigate('login/property_manager');
      else if (roleId === 'tenant') navigate('login/tenant');
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Hero: full-viewport background carousel + overlay + content */}
      <section className="relative min-h-[90vh] flex items-center justify-center overflow-hidden">
        {/* Background slideshow */}
        <div className="absolute inset-0">
          {HERO_IMAGES.map((src, i) => (
            <div
              key={src}
              className={`absolute inset-0 bg-cover bg-center transition-opacity duration-1000 ease-out ${
                i === activeIndex ? 'opacity-100 z-0' : 'opacity-0 z-[-1]'
              }`}
              style={{ backgroundImage: `url(${src})` }}
              aria-hidden={i !== activeIndex}
            />
          ))}
          {/* Dark overlay for text readability */}
          <div className="absolute inset-0 bg-slate-900/60 z-[1]" />
        </div>

        {/* Hero content */}
        <div className="relative z-10 max-w-4xl mx-auto px-6 text-center text-white">
          <h1 className="text-4xl sm:text-5xl md:text-6xl font-bold tracking-tight mb-4 drop-shadow-lg">
            Your property,{' '}
            <span className="text-sky-300">documented.</span>
          </h1>
          <p className="text-base sm:text-lg text-slate-200/90 max-w-2xl mx-auto mb-10 leading-relaxed">
            DocuStay is a neutral documentation platform: authorization records, identity verification, and an immutable audit trail for temporary stays.
          </p>

          {roleSelector ? (
            <div className="w-full max-w-lg mx-auto">
              <div className="bg-white rounded-2xl shadow-xl border border-slate-200/80 overflow-hidden">
                <div className="px-8 pt-8 pb-6">
                  <h2 className="text-xl font-semibold text-slate-900 mb-1">
                    {roleSelector === 'signup' ? 'Create an account as' : 'Sign in as'}
                  </h2>
                  <p className="text-sm text-slate-500 mb-6">
                    {roleSelector === 'signup'
                      ? 'Choose your role to get started'
                      : 'Select your account type to continue'}
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    {ROLES.map((r) => (
                      <button
                        key={r.id}
                        onClick={() => onRoleSelect(r.id)}
                        className="group flex items-center gap-3 px-5 py-4 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-white hover:border-slate-300 hover:shadow-md transition-all duration-200 text-left"
                      >
                        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-200/80 group-hover:bg-[#6B90F2]/15 text-slate-600 group-hover:text-[#6B90F2] transition-colors">
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={r.icon} />
                          </svg>
                        </span>
                        <span className="font-medium text-slate-800 group-hover:text-slate-900">{r.label}</span>
                      </button>
                    ))}
                  </div>
                </div>
                <div className="px-8 pb-6 pt-2">
                  <button
                    type="button"
                    onClick={() => setRoleSelector(null)}
                    className="flex items-center gap-2 text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7" />
                    </svg>
                    Back
                  </button>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button
                variant="primary"
                onClick={() => setRoleSelector('signup')}
                className="px-8 py-3.5 bg-[#6B90F2] hover:bg-[#5a7ed9] border-0 text-white font-semibold shadow-lg shadow-slate-900/20 rounded-xl"
              >
                Get started
              </Button>
              <button
                type="button"
                onClick={() => setRoleSelector('login')}
                className="px-8 py-3.5 rounded-xl text-sm font-medium border-2 border-white/80 text-white bg-white/5 hover:bg-white/15 backdrop-blur-sm transition-colors"
              >
                Already have an account?
              </button>
            </div>
          )}
        </div>

        {/* Carousel indicators */}
        <div className="absolute bottom-8 left-0 right-0 z-10 flex justify-center gap-2">
          {HERO_IMAGES.map((_, i) => (
            <button
              key={i}
              onClick={() => setActiveIndex(i)}
              className={`h-2 rounded-full transition-all duration-300 ${
                i === activeIndex ? 'w-8 bg-white' : 'w-2 bg-white/50 hover:bg-white/70'
              }`}
              aria-label={`Slide ${i + 1}`}
            />
          ))}
        </div>
      </section>

      {/* Value props */}
      <section className="py-20 px-6 bg-white">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-4">
            Why DocuStay?
          </h2>
          <p className="text-gray-600 text-center max-w-2xl mx-auto mb-16">
            Built for owners who want clear documentation and authorization records for temporary stays.
          </p>
          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                title: 'Clear agreements',
                desc: 'Guests sign region-specific agreements so everyone knows the terms of the stay.',
                icon: '📄',
              },
              {
                title: 'Identity verification',
                desc: 'Verify guest identity with Stripe Identity so you know who is staying.',
                icon: '✓',
              },
              {
                title: 'Utility controls',
                desc: 'Authority letters and utility provider management keep services in your name.',
                icon: '🔑',
              },
              {
                title: 'Stay limits & alerts',
                desc: 'Region-aware stay limits and status alerts keep your documentation up to date.',
                icon: '🛡️',
              },
            ].map((item) => (
              <div
                key={item.title}
                className="p-6 rounded-2xl bg-slate-50/80 border border-slate-100 hover:border-sky-200 hover:shadow-md transition-all"
              >
                <div className="text-2xl mb-3">{item.icon}</div>
                <h3 className="font-semibold text-gray-900 mb-2">{item.title}</h3>
                <p className="text-gray-600 text-sm leading-relaxed">{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works (compact) */}
      <section className="py-20 px-6 bg-gradient-to-b from-slate-50 to-white">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Simple flow for owners
          </h2>
          <p className="text-gray-600 mb-12">
            Register your property, verify your identity, add utilities, and invite guests with a single link.
          </p>
          <div className="flex flex-wrap justify-center gap-6 sm:gap-10">
            {['Add property', 'Verify identity', 'Invite guest', 'Guest signs'].map((step, i) => (
              <div key={step} className="flex items-center gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#6B90F2] text-white font-semibold text-sm">
                  {i + 1}
                </span>
                <span className="text-gray-700 font-medium">{step}</span>
                {i < 3 && <span className="hidden sm:inline text-slate-300">→</span>}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-6 bg-slate-900 text-white">
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">
            Ready to document your stays?
          </h2>
          <p className="text-slate-300 mb-8">
            Join DocuStay and manage short-term stays with confidence.
          </p>
          <Button
            variant="primary"
            onClick={() => setRoleSelector('signup')}
            className="px-8 py-3.5 bg-[#6B90F2] hover:bg-[#5a7ed9] border-0 text-white font-semibold rounded-xl"
          >
            Get started
          </Button>
        </div>
      </section>

      <footer className="py-6 px-4 bg-slate-950 text-slate-400 text-center text-sm">
        © {new Date().getFullYear()} DocuStay. Documentation platform—not a law firm.
      </footer>
    </div>
  );
};

export default Landing;
