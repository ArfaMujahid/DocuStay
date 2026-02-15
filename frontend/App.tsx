
import React, { useState, useEffect } from 'react';
import { AppState, UserType, AccountStatus } from './types';
import { Card, Button, LoadingOverlay, ErrorModal } from './components/UI';
import { NotificationCenter } from './components/NotificationCenter';
import { authApi } from './services/api';
import Login from './pages/Auth/Login';
import RegisterOwner from './pages/Auth/RegisterOwner';
import VerifyContact from './pages/Auth/VerifyContact';
import OwnerDashboard from './pages/Owner/OwnerDashboard';
import AddProperty from './pages/Owner/AddProperty';
import RegisterFromInvite from './pages/Guest/RegisterFromInvite';
import IdentityVerification from './pages/Guest/IdentityVerification';
import { GuestDashboard } from './pages/Guest/GuestDashboard';
import { PropertyDetail } from './pages/Owner/PropertyDetail';
import SignAgreement from './pages/Guest/SignAgreement';
import Settings from './pages/Settings/Settings';
import HelpCenter from './pages/Support/HelpCenter';
import GuestSignup from './pages/Guest/GuestSignup';
import GuestLogin from './pages/Guest/GuestLogin';

const App: React.FC = () => {
  const [state, setState] = useState<AppState>({
    user: null,
  });
  const [view, setView] = useState<string>('login');
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success'; message: string } | null>(null);
  const [errorModal, setErrorModal] = useState<{ open: boolean; message: string }>({ open: false, message: '' });

  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#', '');
      if (hash) setView(hash);
      else setView('');
    };
    window.addEventListener('hashchange', handleHashChange);
    handleHashChange();
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const navigate = (newView: string) => {
    window.location.hash = newView;
    setView(newView);
  };

  const handleLogin = (userData: any) => {
    setState(prev => ({ ...prev, user: userData }));
    if (userData.user_type === UserType.PROPERTY_OWNER) {
      navigate('dashboard');
    } else {
      navigate('guest-dashboard');
    }
  };

  const handleLogout = () => {
    authApi.logout();
    setState({ user: null });
    navigate('login');
  };

  const showNotification = (type: 'success' | 'error', message: string) => {
    if (type === 'error') {
      setErrorModal({ open: true, message });
      return;
    }
    setNotification({ type: 'success', message });
    setTimeout(() => setNotification(null), 5000);
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-b from-blue-100/60 via-blue-50/30 to-sky-50/50 text-gray-800 overflow-x-hidden relative">
      {loading && <LoadingOverlay />}

      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-40">
        <div className="w-full px-4 sm:px-5">
          <div className="flex justify-between h-16 items-center">
            <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('')}>
              <div className="w-9 h-9 bg-blue-700 rounded-lg flex items-center justify-center">
                <span className="text-white font-semibold text-lg">D</span>
              </div>
              <span className="text-xl font-semibold text-gray-900">DocuStay <span className="text-blue-700 font-normal">AI</span></span>
            </div>
            
            <div className="flex items-center gap-6">
              {state.user ? (
                <>
                  <NotificationCenter />
                  <div className="hidden md:block text-right">
                    <p className="text-sm font-semibold text-gray-900">{state.user.user_name}</p>
                    <p className="text-xs text-gray-500 uppercase tracking-wide">
                      {(state.user.user_type || '').replace('_', ' ')}
                    </p>
                  </div>
                  <Button variant="outline" onClick={handleLogout} className="px-5 py-2">Logout</Button>
                </>
              ) : (
                <>
                  <button onClick={() => navigate('login')} className="text-gray-600 hover:text-gray-900 font-medium text-sm transition-colors">Login</button>
                  <Button variant="primary" onClick={() => navigate('register')} className="px-6 py-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-blue-600">Get Started</Button>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Success toast (errors use ErrorModal below) */}
      {notification && (
        <div className="fixed top-24 right-4 z-50 p-4 rounded-lg shadow-md border bg-white border-green-200 text-green-800">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-green-500"></div>
            <span className="font-medium">{notification.message}</span>
          </div>
        </div>
      )}

      {/* Global error modal – all errors displayed here */}
      <ErrorModal
        open={errorModal.open}
        message={errorModal.message}
        onClose={() => setErrorModal({ open: false, message: '' })}
      />

      {/* Main Content */}
      <main className="flex-grow flex flex-col">
        {view === 'login' && <Login onLogin={handleLogin} setLoading={setLoading} notify={showNotification} navigate={navigate} />}
        {(view === 'guest-login' || view.startsWith('guest-login/') || view.startsWith('invite/')) && (
          <GuestLogin
            inviteCode={view.startsWith('guest-login/') ? view.split('/')[1] : view.startsWith('invite/') ? view.split('/')[1] : undefined}
            onLogin={handleLogin}
            setLoading={setLoading}
            notify={showNotification}
            navigate={navigate}
          />
        )}
        {view === 'register' && <RegisterOwner setPendingVerification={(data) => setState(prev => ({ ...prev, pendingVerification: data }))} onLogin={handleLogin} navigate={navigate} setLoading={setLoading} notify={showNotification} />}
        {(view === 'guest-signup' || view.startsWith('guest-signup/')) && (
          <GuestSignup
            initialInviteCode={view.startsWith('guest-signup/') ? view.split('/')[1] : undefined}
            setPendingVerification={(data) => setState(prev => ({ ...prev, pendingVerification: data }))}
            navigate={navigate}
            setLoading={setLoading}
            notify={showNotification}
            onGuestLogin={(user) => { setState(prev => ({ ...prev, user })); navigate('guest-dashboard'); }}
          />
        )}
        {view === 'verify' && state.pendingVerification && <VerifyContact verification={state.pendingVerification} navigate={navigate} setLoading={setLoading} notify={showNotification} onVerified={(user) => setState(prev => ({ ...prev, user }))} />}
        
        {/* Owner Dashboard Views */}
        {(view === 'dashboard' || view === 'dashboard/properties') && state.user?.user_type === UserType.PROPERTY_OWNER && (
          <OwnerDashboard
            user={state.user}
            navigate={navigate}
            setLoading={setLoading}
            notify={showNotification}
            initialTab={view === 'dashboard/properties' ? 'properties' : undefined}
          />
        )}
        {view === 'add-property' && <AddProperty user={state.user} navigate={navigate} setLoading={setLoading} notify={showNotification} />}
        {view === 'settings' && <Settings user={state.user} navigate={navigate} />}
        {view === 'help' && <HelpCenter navigate={navigate} />}
        {view.startsWith('property/') && state.user?.user_type === UserType.PROPERTY_OWNER && <PropertyDetail propertyId={view.split('/')[1]} user={state.user} navigate={navigate} setLoading={setLoading} notify={showNotification} />}
        
        {/* Guest Flow Views */}
        {view === 'guest-dashboard' && state.user?.user_type === UserType.GUEST && <GuestDashboard user={state.user} navigate={navigate} notify={showNotification} />}
        {view === 'guest-identity' && state.user?.user_type === UserType.GUEST && <IdentityVerification user={state.user} navigate={navigate} setLoading={setLoading} notify={showNotification} />}
        {view === 'sign-agreement' && state.user?.user_type === UserType.GUEST && <SignAgreement user={state.user} navigate={navigate} notify={showNotification} />}

        {/* Home / Default */}
        {view === '' && (
          <div className="flex-grow flex flex-col items-center justify-center py-20 px-4">
            <div className="text-center max-w-2xl mx-auto">
              <h1 className="text-4xl md:text-5xl font-semibold text-gray-900 mb-4 leading-tight">
                Your property, <span className="text-blue-700">legally protected.</span>
              </h1>
              <p className="text-gray-600 mb-10 max-w-lg mx-auto">
                DocuStay helps property owners manage temporary stays with clear agreements and verification—reducing risk of tenancy claims.
              </p>
              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Button variant="primary" onClick={() => navigate('register')} className="px-8 py-3.5 bg-blue-700 hover:bg-blue-800 focus:ring-blue-600">Get started</Button>
                <Button variant="outline" onClick={() => navigate('login')} className="px-8 py-3.5 border-blue-300 text-blue-700 hover:bg-blue-100 hover:border-blue-400 focus:ring-blue-500">Sign in</Button>
              </div>
            </div>
          </div>
        )}
      </main>

      {!['', 'login', 'register', 'verify'].includes(view) && !view.startsWith('guest-login') && !view.startsWith('guest-signup') && !view.startsWith('invite/') && (
        <footer className="bg-white border-t border-gray-200 py-10">
          <div className="max-w-7xl mx-auto px-4 text-center">
            <p className="text-gray-500 text-sm">© 2024 DocuStay AI. Legal technology platform—not a law firm.</p>
          </div>
        </footer>
      )}
    </div>
  );
};

export default App;
