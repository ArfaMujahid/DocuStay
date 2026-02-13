
import React, { useState, useEffect, useCallback } from 'react';
import { Card, Button, Input } from '../../components/UI';
import { InviteGuestModal } from '../../components/InviteGuestModal';
import { UserSession } from '../../types';
import { analyzeStay, JURISDICTION_RULES } from '../../services/jleService';
import { RiskAssessment } from '../../components/RiskAssessment';
import { propertiesApi, dashboardApi, type Property, type OwnerStayView } from '../../services/api';

const PROPERTY_TYPES = [
  { id: 'house', name: 'House' },
  { id: 'apartment', name: 'Apartment' },
  { id: 'condo', name: 'Condo' },
  { id: 'townhouse', name: 'Townhouse' },
];

function isOverstayed(endDateStr: string): boolean {
  const end = new Date(endDateStr);
  end.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return end.getTime() < today.getTime();
}

export const PropertyDetail: React.FC<{ propertyId: string; user: UserSession; navigate: (v: string) => void; setLoading?: (l: boolean) => void; notify?: (t: 'success' | 'error', m: string) => void }> = ({ propertyId, user, navigate, setLoading: setGlobalLoading = () => {}, notify = () => {} }) => {
  const [activeTab, setActiveTab] = useState('overview');
  const [property, setProperty] = useState<Property | null>(null);
  const [stays, setStays] = useState<OwnerStayView[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showInviteModal, setShowInviteModal] = useState(false);
  const [editOpen, setEditOpen] = useState(false);
  const [editSaving, setEditSaving] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);
  const [deleteSaving, setDeleteSaving] = useState(false);
  const [shieldToggling, setShieldToggling] = useState(false);
  const [editForm, setEditForm] = useState({
    property_name: '',
    street_address: '',
    city: '',
    state: '',
    zip_code: '',
    property_type: 'house',
    bedrooms: '1',
    is_primary_residence: false,
  });

  const id = Number(propertyId);
  const stateKey = property?.state ?? 'FL';
  const jurisdictionInfo = JURISDICTION_RULES[stateKey as keyof typeof JURISDICTION_RULES] ?? JURISDICTION_RULES.FL;
  const propertyStays = stays.filter((s) => s.property_id === id);
  const activeStaysForProperty = propertyStays.filter((s) => !s.checked_out_at && !s.cancelled_at);
  const activeStay = activeStaysForProperty.find((s) => !isOverstayed(s.stay_end_date)) ?? activeStaysForProperty[0];
  const isOccupied = activeStaysForProperty.length > 0;
  const shieldOn = !!(property?.shield_mode_enabled);
  const shieldStatus = shieldOn ? (isOccupied ? 'PASSIVE GUARD' : 'ACTIVE ENFORCEMENT') : null;
  const currentGuestRisk = activeStay
    ? analyzeStay(stateKey, {
        durationDays: activeStay.max_stay_allowed_days,
        paymentInvolved: false,
        exclusivePossession: false,
        checkInDate: activeStay.stay_start_date,
        checkOutDate: activeStay.stay_end_date,
      })
    : null;

  const loadData = useCallback(() => {
    if (!id || isNaN(id)) {
      const msg = 'Invalid property';
      setError(msg);
      notify('error', msg);
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    Promise.all([propertiesApi.get(id), dashboardApi.ownerStays()])
      .then(([prop, staysData]) => {
        setProperty(prop);
        setStays(staysData);
      })
      .catch((e) => {
        const msg = (e as Error)?.message ?? 'Failed to load property.';
        setError(msg);
        notify('error', msg);
      })
      .finally(() => setLoading(false));
  }, [id, notify]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const openEdit = () => {
    if (property) {
      setEditForm({
        property_name: property.name ?? '',
        street_address: property.street ?? '',
        city: property.city ?? '',
        state: property.state ?? '',
        zip_code: property.zip_code ?? '',
        property_type: property.property_type_label ?? 'house',
        bedrooms: property.bedrooms ?? '1',
        is_primary_residence: property.owner_occupied ?? false,
      });
      setEditOpen(true);
    }
  };

  const saveEdit = async () => {
    if (!property) return;
    setEditSaving(true);
    try {
      const updated = await propertiesApi.update(property.id, {
        property_name: editForm.property_name || undefined,
        street_address: editForm.street_address,
        city: editForm.city,
        state: editForm.state,
        zip_code: editForm.zip_code || undefined,
        property_type: editForm.property_type,
        bedrooms: editForm.bedrooms,
        is_primary_residence: editForm.is_primary_residence,
      });
      setProperty(updated);
      setEditOpen(false);
    } catch (e) {
      notify('error', (e as Error)?.message ?? 'Failed to update property.');
    } finally {
      setEditSaving(false);
    }
  };

  const handleDeleteConfirm = async () => {
    if (!property) return;
    setDeleteSaving(true);
    setDeleteError(null);
    try {
      await propertiesApi.delete(property.id);
      setDeleteConfirmOpen(false);
      notify('success', 'Property removed from dashboard. It has been moved to Inactive properties.');
      navigate('dashboard');
    } catch (e) {
      const msg = (e as Error)?.message ?? 'Failed to remove property.';
      setDeleteError(msg);
      notify('error', msg);
    } finally {
      setDeleteSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-grow p-4 md:p-8 max-w-7xl mx-auto w-full">
        <p className="text-gray-400">Loading property…</p>
      </div>
    );
  }
  if (error || !property) {
    return (
      <div className="flex-grow p-4 md:p-8 max-w-7xl mx-auto w-full">
        <Card className="p-8 text-center max-w-md mx-auto">
          <p className="text-slate-600 mb-4">Something went wrong loading this property.</p>
          <div className="flex gap-3 justify-center">
            <Button variant="outline" onClick={() => navigate('dashboard')}>Back to Dashboard</Button>
            <Button variant="primary" onClick={() => { setError(null); loadData(); }}>Try again</Button>
          </div>
        </Card>
      </div>
    );
  }

  const address = [property.street, property.city, property.state, property.zip_code].filter(Boolean).join(', ');

  return (
    <div className="flex-grow p-4 md:p-8 max-w-7xl mx-auto w-full">
      <header className="mb-10">
        <button onClick={() => navigate('dashboard')} className="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6 font-bold text-sm uppercase tracking-widest transition-colors">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
          Back to Dashboard
        </button>
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6">
          <div>
            <div className="flex items-center gap-4 mb-2">
              <h1 className="text-4xl md:text-5xl font-black text-slate-800 tracking-tighter">{property.name || address || 'Property'}</h1>
              <span className="px-3 py-1 rounded-full bg-blue-600 text-[10px] font-black uppercase tracking-widest text-white shadow-lg shadow-blue-500/30">Active</span>
            </div>
            <p className="text-slate-600 font-medium text-lg">{address || '—'}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={openEdit} className="px-6 py-2.5">Edit Property</Button>
            <Button variant="primary" onClick={() => setShowInviteModal(true)} className="px-6 py-2.5">Invite Guest</Button>
            <Button
              variant="ghost"
              onClick={() => { setDeleteConfirmOpen(true); setDeleteError(null); }}
              className="px-6 py-2.5 text-red-600 hover:text-red-700 hover:bg-red-50"
            >
              Remove Property
            </Button>
          </div>
        </div>
      </header>

      <div className="flex border-b border-slate-200 mb-10 overflow-x-auto no-scrollbar">
        {['Overview', 'Guests', 'Guest History', 'Legal Info', 'Settings'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab.toLowerCase())}
            className={`px-8 py-4 text-sm font-bold uppercase tracking-[0.2em] whitespace-nowrap transition-all border-b-2 ${activeTab === tab.toLowerCase() ? 'text-blue-600 border-blue-500' : 'text-slate-500 border-transparent hover:text-slate-700'}`}
          >
            {tab}
          </button>
        ))}
      </div>

      <div className="animate-in fade-in slide-in-from-bottom-2 duration-500">
        {activeTab === 'overview' && (
          <div className="grid lg:grid-cols-3 gap-8">
            <div className="lg:col-span-2 space-y-8">
              {property && (
                <div className="grid md:grid-cols-2 gap-6">
                  <Card className="p-6 border-slate-200 bg-slate-50/80">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Occupancy status</h3>
                    <div className="flex items-center gap-3 flex-wrap">
                      <span className={`inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${isOccupied ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-200 text-slate-700'}`}>
                        <span className={`w-2 h-2 rounded-full ${isOccupied ? 'bg-emerald-500' : 'bg-slate-400'}`} />
                        {isOccupied ? 'OCCUPIED' : 'VACANT'}
                      </span>
                      {isOccupied && activeStay && (
                        <span className="text-sm text-slate-600">
                          Current guest: <span className="font-medium text-slate-800">{activeStay.guest_name}</span>
                          {' · '}
                          Lease end: <span className="font-medium text-slate-800">{activeStay.stay_end_date}</span>
                        </span>
                      )}
                    </div>
                  </Card>
                  <Card className="p-6 border-slate-200">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Shield Mode</h3>
                    <div className="flex flex-wrap items-center gap-4">
                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          role="switch"
                          aria-checked={shieldOn}
                          disabled={shieldToggling || !shieldOn}
                          title={!shieldOn ? "Shield Mode turns on automatically on the last day of a guest's stay" : 'Turn Shield Mode off'}
                          onClick={async () => {
                            if (!property || !shieldOn) return;
                            setShieldToggling(true);
                            try {
                              const updated = await propertiesApi.update(property.id, { shield_mode_enabled: false });
                              setProperty(updated);
                              notify('success', 'Shield Mode turned off.');
                            } catch (e) {
                              notify('error', (e as Error)?.message ?? 'Failed to update Shield Mode.');
                            } finally {
                              setShieldToggling(false);
                            }
                          }}
                          className={`relative inline-flex h-6 w-11 flex-shrink-0 rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 ${shieldOn ? 'cursor-pointer bg-emerald-600' : 'cursor-not-allowed bg-slate-200 opacity-60'} ${shieldToggling ? 'opacity-50' : ''}`}
                        >
                          <span className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition-transform ${shieldOn ? 'translate-x-5' : 'translate-x-1'}`} />
                        </button>
                        <span className="text-sm font-medium text-slate-800">{shieldOn ? 'ON' : 'OFF'}</span>
                      </div>
                      {shieldOn && shieldStatus && (
                        <span className="text-sm text-slate-600">
                          Status: <span className="font-semibold text-slate-800">{shieldStatus}</span>
                        </span>
                      )}
                      {!shieldOn && (
                        <span className="text-xs text-slate-500">Turns on automatically on the last day of a guest&apos;s stay</span>
                      )}
                      <span className="text-xs text-slate-400">$10/month subscription</span>
                    </div>
                  </Card>
                </div>
              )}

              <Card className="p-8 border-slate-200 bg-white/65 backdrop-blur-xl">
                <h3 className="text-xl font-bold text-slate-800 mb-6">Jurisdiction Shield</h3>
                <div className="grid md:grid-cols-2 gap-10">
                  <div>
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-12 h-12 bg-blue-500/10 text-blue-600 rounded-2xl flex items-center justify-center font-black">{property.region_code || property.state}</div>
                      <div>
                        <p className="text-xs text-slate-500 uppercase font-black tracking-widest">State Rules</p>
                        <p className="text-slate-800 font-bold">{jurisdictionInfo.name}</p>
                      </div>
                    </div>
                    <div className="space-y-4">
                      <div className="flex justify-between items-center p-4 rounded-xl bg-slate-100 border border-slate-200">
                        <span className="text-sm text-slate-600">Max Safe Stay</span>
                        <span className="text-sm font-black text-green-600">{jurisdictionInfo.maxSafeStayDays} Days</span>
                      </div>
                      <div className="flex justify-between items-center p-4 rounded-xl bg-slate-100 border border-slate-200">
                        <span className="text-sm text-slate-600">Primary Statute</span>
                        <span className="text-sm font-black text-blue-600">{jurisdictionInfo.keyStatute}</span>
                      </div>
                    </div>
                  </div>
                  <div className="p-6 rounded-2xl bg-amber-50 border border-amber-200">
                    <p className="text-xs text-amber-700 font-black uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="3" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>
                      Tenancy Trap Warning
                    </p>
                    <p className="text-sm text-slate-600 leading-relaxed font-medium">Guests staying 30+ days in Florida may claim tenancy rights under {jurisdictionInfo.keyStatute}. DocuStay enforces a hard 29-day limit to maintain your legal shield.</p>
                  </div>
                </div>
              </Card>

              <div className="grid md:grid-cols-2 gap-8">
                <Card className="p-8 border-slate-200">
                  <h3 className="text-sm font-black text-slate-500 uppercase tracking-widest mb-6">Property Info</h3>
                  <div className="space-y-4">
                    <div className="flex justify-between text-sm"><span className="text-slate-500">Property Type</span><span className="text-slate-800 font-bold">{property.property_type_label || property.property_type || '—'}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-slate-500">Bedrooms</span><span className="text-slate-800 font-bold">{property.bedrooms ?? '—'}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-slate-500">Region</span><span className="text-slate-800 font-bold">{property.region_code}</span></div>
                    <div className="flex justify-between text-sm"><span className="text-slate-500">Ownership</span><span className="text-green-600 font-black uppercase text-[10px]">Verified ✓</span></div>
                  </div>
                </Card>
                <Card className="p-8 border-slate-200 bg-white/65 backdrop-blur-xl">
                  <h3 className="text-sm font-black text-gray-500 uppercase tracking-widest mb-6">Evidence Status</h3>
                  <p className="text-slate-600 text-sm mb-6 leading-relaxed">Stays and legal records are stored in your dashboard.</p>
                  <Button variant="outline" className="w-full text-xs font-black uppercase tracking-widest">Download Latest (ZIP)</Button>
                </Card>
              </div>
            </div>

            <div>
              <h3 className="text-xs font-black text-gray-600 uppercase tracking-[0.2em] mb-4">Active Risk Monitoring</h3>
              {currentGuestRisk ? <RiskAssessment data={currentGuestRisk} /> : <p className="text-slate-500 text-sm">No active stay at this property.</p>}
            </div>
          </div>
        )}

        {activeTab === 'guests' && (
          <Card className="overflow-hidden border-slate-200">
            <table className="w-full text-left">
              <thead className="bg-slate-100 text-slate-500 uppercase text-[10px] tracking-widest font-black">
                <tr>
                  <th className="px-6 py-4 text-center w-20">Risk</th>
                  <th className="px-6 py-4">Guest</th>
                  <th className="px-6 py-4">Check-in</th>
                  <th className="px-6 py-4">Check-out</th>
                  <th className="px-6 py-4">Status</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {propertyStays.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-slate-500">No guests at this property.</td>
                  </tr>
                ) : (
                  propertyStays.map((stay) => {
                    const overstay = isOverstayed(stay.stay_end_date);
                    return (
                      <tr key={stay.stay_id} className="hover:bg-slate-50 transition-colors group">
                        <td className="px-6 py-5 text-center">
                          <div className={`w-3 h-3 rounded-full mx-auto ${stay.risk_indicator === 'high' ? 'bg-red-500' : stay.risk_indicator === 'medium' ? 'bg-yellow-500' : 'bg-green-500'} shadow-[0_0_8px_rgba(34,197,94,0.6)]`}></div>
                        </td>
                        <td className="px-6 py-5">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 rounded-full bg-blue-600/20 text-blue-600 flex items-center justify-center font-black text-xs">{stay.guest_name.charAt(0)}</div>
                            <div>
                              <p className="text-sm font-bold text-slate-800">{stay.guest_name}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-5 text-sm text-slate-600 font-mono">{stay.stay_start_date}</td>
                        <td className="px-6 py-5 text-sm text-slate-600 font-mono">{stay.stay_end_date}</td>
                        <td className="px-6 py-5">
                          <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-widest border ${overstay ? 'bg-red-50 text-red-600 border-red-200' : 'bg-green-50 text-green-600 border-green-200'}`}>
                            {overstay ? 'Overstayed' : 'Active'}
                          </span>
                        </td>
                        <td className="px-6 py-5 text-right"><Button variant="ghost" className="text-xs">Revoke</Button></td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </Card>
        )}

        {activeTab === 'legal info' && (
          <div className="max-w-3xl space-y-8">
            <h3 className="text-3xl font-black text-slate-800 tracking-tighter">Jurisdiction Deep Dive: {jurisdictionInfo.name}</h3>

            <section>
              <h4 className="text-lg font-bold text-blue-600 mb-4 uppercase tracking-wider">Tenancy Creation Rules</h4>
              <p className="text-slate-600 leading-relaxed mb-4">In {jurisdictionInfo.name}, tenancy can be established automatically if a guest stays beyond {jurisdictionInfo.tenancyThresholdDays} days. Once established, removing an unwanted occupant requires a formal court eviction process rather than immediate removal.</p>
              <ul className="list-disc list-inside text-slate-500 space-y-2 text-sm italic">
                <li>Receiving mail at the property</li>
                <li>Moving in substantial personal furniture</li>
                <li>Exclusive control of keys or entrance</li>
              </ul>
            </section>

            <section className="p-6 rounded-2xl bg-white/65 backdrop-blur-xl border border-slate-200">
              <h4 className="text-lg font-bold text-slate-800 mb-4 uppercase tracking-wider">Stay Classification Logic</h4>
              <div className="grid gap-4 text-sm">
                <div className="p-4 rounded-xl bg-green-50 border border-green-200">
                  <span className="font-black text-green-600 mr-2">GUEST:</span>
                  <span className="text-slate-600">Duration &lt; {jurisdictionInfo.maxSafeStayDays - jurisdictionInfo.warningDays} days. Minimum risk.</span>
                </div>
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
                  <span className="font-black text-amber-600 mr-2">TEMPORARY OCCUPANT:</span>
                  <span className="text-slate-600">Approaching threshold. Extra verification logs active.</span>
                </div>
                <div className="p-4 rounded-xl bg-red-50 border border-red-200">
                  <span className="font-black text-red-500 mr-2">TENANT RISK:</span>
                  <span className="text-slate-600">Immediate action required. Stay duration unsafe for {property.state}.</span>
                </div>
              </div>
            </section>
          </div>
        )}

        {activeTab === 'guest history' && (
          <p className="text-slate-500">Guest history for this property will appear here when available.</p>
        )}

        {activeTab === 'settings' && (
          <p className="text-gray-500">Property settings will appear here.</p>
        )}
      </div>

      {/* Remove property (soft-delete) confirmation */}
      {deleteConfirmOpen && property && (
        <>
          <div className="fixed inset-0 bg-black/70 z-40" onClick={() => !deleteSaving && (setDeleteConfirmOpen(false), setDeleteError(null))} />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
              <div className="p-6 border-b border-slate-200">
                <h3 className="text-lg font-bold text-slate-800">Remove Property</h3>
              </div>
              <div className="p-6 space-y-4">
                <p className="text-slate-600 text-sm">
                  Remove <span className="font-bold text-slate-800">{property.name || address || 'this property'}</span> from your dashboard? Allowed only when there is no active guest stay. The property will move to <strong>Inactive properties</strong> and can be reactivated anytime. Data is kept for logs.
                </p>
                <div className="flex gap-3">
                  <Button variant="outline" onClick={() => { setDeleteConfirmOpen(false); setDeleteError(null); }} disabled={deleteSaving} className="flex-1">Cancel</Button>
                  <Button variant="danger" onClick={handleDeleteConfirm} disabled={deleteSaving} className="flex-1">
                    {deleteSaving ? 'Removing…' : 'Remove Property'}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}

      {/* Edit property modal */}
      {editOpen && property && (
        <>
          <div className="fixed inset-0 bg-black/70 z-40" onClick={() => setEditOpen(false)} />
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto">
            <Card className="w-full max-w-lg my-8">
              <div className="p-6 border-b border-slate-200 flex items-center justify-between">
                <h3 className="text-lg font-bold text-slate-800">Edit Property</h3>
                <button onClick={() => setEditOpen(false)} className="text-slate-500 hover:text-slate-800">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <div className="p-6 space-y-4">
                <Input
                  label="Property name (optional)"
                  name="property_name"
                  value={editForm.property_name}
                  onChange={(e) => setEditForm({ ...editForm, property_name: e.target.value })}
                  placeholder="e.g. Miami Beach Condo"
                />
                <Input
                  label="Street address"
                  name="street_address"
                  value={editForm.street_address}
                  onChange={(e) => setEditForm({ ...editForm, street_address: e.target.value })}
                  placeholder="123 Main St"
                  required
                />
                <div className="grid grid-cols-2 gap-4">
                  <Input
                    label="City"
                    name="city"
                    value={editForm.city}
                    onChange={(e) => setEditForm({ ...editForm, city: e.target.value })}
                    placeholder="Miami"
                    required
                  />
                  <Input
                    label="State"
                    name="state"
                    value={editForm.state}
                    onChange={(e) => setEditForm({ ...editForm, state: e.target.value })}
                    placeholder="FL"
                    required
                  />
                </div>
                <Input
                  label="ZIP code"
                  name="zip_code"
                  value={editForm.zip_code}
                  onChange={(e) => setEditForm({ ...editForm, zip_code: e.target.value })}
                  placeholder="33139"
                />
                <div>
                  <label className="block text-sm font-medium text-slate-600 mb-2">Property type</label>
                  <div className="flex flex-wrap gap-2">
                    {PROPERTY_TYPES.map((t) => (
                      <button
                        key={t.id}
                        type="button"
                        onClick={() => setEditForm({ ...editForm, property_type: t.id })}
                        className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${editForm.property_type === t.id ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600 hover:text-slate-800'}`}
                      >
                        {t.name}
                      </button>
                    ))}
                  </div>
                </div>
                <Input
                  label="Bedrooms"
                  name="bedrooms"
                  value={editForm.bedrooms}
                  onChange={(e) => setEditForm({ ...editForm, bedrooms: e.target.value })}
                  options={[
                    { value: '1', label: '1' },
                    { value: '2', label: '2' },
                    { value: '3', label: '3' },
                    { value: '4', label: '4' },
                    { value: '5', label: '5+' },
                  ]}
                />
                <label className="flex items-center gap-3 cursor-pointer p-3 rounded-xl bg-slate-100 border border-slate-200">
                  <input
                    type="checkbox"
                    checked={editForm.is_primary_residence}
                    onChange={(e) => setEditForm({ ...editForm, is_primary_residence: e.target.checked })}
                    className="w-5 h-5 rounded border-slate-300 bg-white text-blue-600"
                  />
                  <span className="text-sm font-medium text-slate-800">Primary residence / owner-occupied</span>
                </label>
                <div className="flex gap-3 pt-4">
                  <Button variant="outline" onClick={() => setEditOpen(false)} className="flex-1">Cancel</Button>
                  <Button variant="primary" onClick={saveEdit} disabled={editSaving || !editForm.street_address || !editForm.city || !editForm.state} className="flex-1">
                    {editSaving ? 'Saving…' : 'Save changes'}
                  </Button>
                </div>
              </div>
            </Card>
          </div>
        </>
      )}

      <InviteGuestModal
        open={showInviteModal}
        onClose={() => setShowInviteModal(false)}
        user={user}
        setLoading={setGlobalLoading}
        notify={notify}
        navigate={navigate}
        initialPropertyId={id}
      />
    </div>
  );
};
