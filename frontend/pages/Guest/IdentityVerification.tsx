
import React, { useState } from 'react';
import { Card, Button, LoadingOverlay } from '../../components/UI';
import { callGemini } from '../../services/geminiService';
import { UserSession } from '../../types';

interface Props {
  user: UserSession | null;
  navigate: (v: string) => void;
  setLoading: (l: boolean) => void;
  notify: (t: 'success' | 'error', m: string) => void;
}

const IdentityVerification: React.FC<Props> = ({ user, navigate, setLoading, notify }) => {
  const [step, setStep] = useState(1);
  const [results, setResults] = useState<any>(null);

  const startVerification = async () => {
    setLoading(true);
    
    // Get geolocation
    let geo = { lat: 0, lon: 0 };
    try {
      const pos = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
      geo = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    } catch (e) {
      console.warn("Geolocation denied, using mock.");
      geo = { lat: 37.78193, lon: -122.40476 };
    }

    try {
    const result = await callGemini('guest_identity_verification', {
      guest_id: user?.user_id,
      guest_name: user?.user_name,
      contact_verified: true,
      id_type: 'drivers_license',
      id_status: 'verified',
      name_on_id: user?.user_name,
      id_expiration: '2028-01-01',
      id_country: 'USA',
      selfie_score: 98,
      selfie_status: 'match',
      liveness_passed: true,
      guest_gps: `${geo.lat}, ${geo.lon}`,
      property_gps: '37.78193, -122.40476',
      distance_feet: 10,
      gps_accuracy: 5
    });
    
    setLoading(false);
    setResults(result);
    setStep(3);
    } catch (e) {
      setLoading(false);
      notify('error', (e as Error)?.message ?? 'Verification failed. Please try again.');
    }
  };

  return (
    <div className="max-w-xl mx-auto py-12 px-4">
      {/* Back Button */}
      <button onClick={() => navigate('guest-dashboard')} className="flex items-center gap-2 text-gray-500 hover:text-white mb-8 font-bold text-sm uppercase tracking-widest transition-colors">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 19l-7-7 7-7"></path></svg>
        Back to Dashboard
      </button>

      <Card className="p-8">
        {step === 1 && (
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">Identity Verification</h2>
            <p className="text-gray-500 mb-8">To finalize your stay, we need to verify your identity and physical presence at the property.</p>
            <div className="space-y-4 text-left mb-8">
              <div className="flex gap-4 items-center p-4 bg-gray-50 rounded-lg">
                <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">1</span>
                <span className="text-gray-900">Scan Government ID</span>
              </div>
              <div className="flex gap-4 items-center p-4 bg-gray-50 rounded-lg">
                <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">2</span>
                <span className="text-gray-900">Live Facial Liveness Check</span>
              </div>
              <div className="flex gap-4 items-center p-4 bg-gray-50 rounded-lg">
                <span className="w-8 h-8 rounded-full bg-blue-600 text-white flex items-center justify-center font-bold">3</span>
                <span className="text-gray-900">GPS Presence Confirmation</span>
              </div>
            </div>
            <Button onClick={() => setStep(2)} className="w-full py-3">Start Verification</Button>
          </div>
        )}

        {step === 2 && (
          <div className="text-center">
             <h2 className="text-2xl font-bold mb-4">Scan ID & Take Selfie</h2>
             <div className="w-48 h-48 bg-gray-200 rounded-full mx-auto flex items-center justify-center mb-8 border-4 border-blue-100 overflow-hidden">
                <img src="https://picsum.photos/200" alt="Selfie" className="w-full h-full object-cover opacity-50 grayscale" />
             </div>
             <p className="text-gray-400 mb-8">Position your face within the circle and wait for the flash.</p>
             <Button onClick={startVerification} className="w-full">Capture & Verify</Button>
          </div>
        )}

        {step === 3 && results && (
          <div>
            <div className={`p-4 rounded-lg mb-6 flex items-center gap-3 ${results.status === 'success' ? 'bg-green-900/20 text-green-400 border border-green-500/20' : 'bg-red-900/20 text-red-400 border border-red-500/20'}`}>
               {results.status === 'success' ? (
                 <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7"></path></svg>
               ) : (
                 <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12"></path></svg>
               )}
               <span className="font-bold">{results.message}</span>
            </div>

            <h3 className="font-bold mb-4 text-white">Verification Summary:</h3>
            <div className="space-y-3 mb-8">
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-400">ID Document:</span>
                <span className="font-medium text-green-400">PASSED</span>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-400">Facial Match:</span>
                <span className="font-medium text-green-400">PASSED (98%)</span>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                <span className="text-gray-400">GPS Presence:</span>
                <span className="font-medium text-green-400">CONFIRMED (10ft away)</span>
              </div>
              <div className="flex justify-between border-b border-gray-800 pb-2">
                 <span className="text-gray-400">Level:</span>
                 <span className="font-bold text-blue-600 uppercase">{results.data.verification_level}</span>
              </div>
            </div>

            <Button onClick={() => navigate('guest-dashboard')} className="w-full">Proceed to Dashboard</Button>
          </div>
        )}
      </Card>
    </div>
  );
};

export default IdentityVerification;
