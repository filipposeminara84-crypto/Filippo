import React, { useState, useEffect } from 'react';
import { useNavigate, Link, useSearchParams } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ShoppingCart, Eye, EyeOff, Loader2, Gift, Mail, ArrowLeft, Check } from 'lucide-react';
import { seedAPI, authAPI } from '../lib/api';

export default function LoginPage() {
  const [searchParams] = useSearchParams();
  const [isLogin, setIsLogin] = useState(true);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [nome, setNome] = useState('');
  const [referralCode, setReferralCode] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [seeding, setSeeding] = useState(false);
  const [resetSent, setResetSent] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  
  const { login, register } = useAuth();
  const navigate = useNavigate();

  // Check for referral code in URL
  useEffect(() => {
    const ref = searchParams.get('ref');
    if (ref) {
      setReferralCode(ref.toUpperCase());
      setIsLogin(false); // Switch to register mode
    }
  }, [searchParams]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    
    try {
      if (isLogin) {
        await login(email, password);
      } else {
        await register(email, password, nome, referralCode || null);
      }
      navigate('/');
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante l\'autenticazione');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    if (!resetEmail.trim()) return;
    
    setLoading(true);
    setError('');
    
    try {
      await authAPI.forgotPassword(resetEmail);
      setResetSent(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante la richiesta');
    } finally {
      setLoading(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      await seedAPI.seed();
      setError('');
      alert('Database popolato con successo! Ora puoi registrarti.');
    } catch (err) {
      console.error(err);
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex flex-col">
      {/* Header */}
      <header className="p-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <ShoppingCart className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-stone-900">Shopply</h1>
            <p className="text-sm text-stone-500">Spesa intelligente, risparmio reale</p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-3xl shadow-xl shadow-stone-200/50 p-8">
            
            {/* Forgot Password View */}
            {showForgotPassword ? (
              <>
                <button
                  onClick={() => {
                    setShowForgotPassword(false);
                    setResetSent(false);
                    setResetEmail('');
                    setError('');
                  }}
                  className="flex items-center gap-2 text-stone-500 hover:text-stone-700 mb-6"
                >
                  <ArrowLeft className="w-4 h-4" />
                  Torna al login
                </button>
                
                {resetSent ? (
                  <div className="text-center py-8">
                    <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <Check className="w-8 h-8 text-emerald-600" />
                    </div>
                    <h2 className="text-xl font-bold text-stone-900 mb-2">Email Inviata!</h2>
                    <p className="text-stone-500 mb-4">
                      Se l'indirizzo <strong>{resetEmail}</strong> è registrato, riceverai un link per reimpostare la password.
                    </p>
                    <p className="text-sm text-stone-400">
                      Controlla anche la cartella spam.
                    </p>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-3 mb-6">
                      <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                        <Mail className="w-6 h-6 text-orange-600" />
                      </div>
                      <div>
                        <h2 className="text-xl font-bold text-stone-900">Password Dimenticata?</h2>
                        <p className="text-sm text-stone-500">Ti invieremo un link per reimpostarla</p>
                      </div>
                    </div>

                    <form onSubmit={handleForgotPassword} className="space-y-5">
                      <div>
                        <label className="block text-sm font-medium text-stone-700 mb-2">
                          Email
                        </label>
                        <input
                          type="email"
                          value={resetEmail}
                          onChange={(e) => setResetEmail(e.target.value)}
                          className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-orange-500/20 focus:border-orange-500 transition-all"
                          placeholder="email@esempio.com"
                          required
                          data-testid="reset-email-input"
                        />
                      </div>

                      {error && (
                        <p className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg">
                          {error}
                        </p>
                      )}

                      <button
                        type="submit"
                        disabled={loading}
                        className="w-full h-12 bg-orange-500 hover:bg-orange-600 text-white font-semibold rounded-xl shadow-lg shadow-orange-500/30 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                        data-testid="send-reset-btn"
                      >
                        {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                        Invia Link di Reset
                      </button>
                    </form>
                  </>
                )}
              </>
            ) : (
              /* Login/Register View */
              <>
                <h2 className="text-2xl font-bold text-stone-900 mb-2">
                  {isLogin ? 'Bentornato!' : 'Crea Account'}
                </h2>
                <p className="text-stone-500 mb-8">
                  {isLogin 
                    ? 'Accedi per ottimizzare la tua spesa' 
                    : 'Registrati per iniziare a risparmiare'}
                </p>

                <form onSubmit={handleSubmit} className="space-y-5">
                  {!isLogin && (
                    <>
                      <div>
                        <label className="block text-sm font-medium text-stone-700 mb-2">
                          Nome
                        </label>
                        <input
                          type="text"
                          value={nome}
                          onChange={(e) => setNome(e.target.value)}
                          className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                          placeholder="Il tuo nome"
                          required={!isLogin}
                          data-testid="register-name-input"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-stone-700 mb-2 flex items-center gap-2">
                          <Gift className="w-4 h-4 text-purple-500" />
                          Codice Referral (opzionale)
                        </label>
                        <input
                          type="text"
                          value={referralCode}
                          onChange={(e) => setReferralCode(e.target.value.toUpperCase())}
                          className="w-full h-12 px-4 rounded-xl border border-purple-200 bg-purple-50 focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 transition-all font-mono tracking-wider"
                          placeholder="Es. MAR5X9K2"
                          maxLength={8}
                          data-testid="referral-code-input"
                        />
                        {referralCode && (
                          <p className="text-sm text-purple-600 mt-1 flex items-center gap-1">
                            <Gift className="w-3 h-3" />
                            Riceverai 25 punti bonus alla registrazione!
                          </p>
                        )}
                      </div>
                    </>
                  )}

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                  placeholder="email@esempio.com"
                  required
                  data-testid="email-input"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-stone-700 mb-2">
                  Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-12 px-4 pr-12 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="••••••••"
                    required
                    minLength={6}
                    data-testid="password-input"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-4 top-1/2 -translate-y-1/2 text-stone-400 hover:text-stone-600"
                  >
                    {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                  </button>
                </div>
              </div>

              {error && (
                <p className="text-sm text-red-500 bg-red-50 px-4 py-2 rounded-lg" data-testid="error-message">
                  {error}
                </p>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full h-12 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 transition-all active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                data-testid="submit-btn"
              >
                {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                {isLogin ? 'Accedi' : 'Registrati'}
              </button>
            </form>

            {/* Divider */}
            <div className="flex items-center gap-3 my-5">
              <div className="flex-1 h-px bg-stone-200"></div>
              <span className="text-xs text-stone-400 font-medium">oppure</span>
              <div className="flex-1 h-px bg-stone-200"></div>
            </div>

            {/* REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH */}
            <button
              type="button"
              onClick={() => {
                const redirectUrl = window.location.origin + '/';
                window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
              }}
              className="w-full h-12 bg-white border-2 border-stone-200 hover:border-stone-300 text-stone-700 font-medium rounded-xl transition-all active:scale-[0.98] flex items-center justify-center gap-3 hover:shadow-md"
              data-testid="google-login-btn"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4"/>
                <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
              </svg>
              Accedi con Google
            </button>

            <div className="mt-6 text-center space-y-3">
              {isLogin && (
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(true)}
                  className="text-sm text-orange-500 hover:text-orange-600 transition-colors"
                  data-testid="forgot-password-link"
                >
                  Password dimenticata?
                </button>
              )}
              <div>
                <button
                  onClick={() => setIsLogin(!isLogin)}
                  className="text-sm text-stone-500 hover:text-emerald-600 transition-colors"
                  data-testid="toggle-auth-mode"
                >
                  {isLogin ? 'Non hai un account? Registrati' : 'Hai già un account? Accedi'}
                </button>
              </div>
            </div>
              </>
            )}
          </div>

          {/* Seed Button for Demo */}
          <div className="mt-6 text-center">
            <button
              onClick={handleSeed}
              disabled={seeding}
              className="text-sm text-stone-400 hover:text-emerald-600 transition-colors flex items-center gap-2 mx-auto"
              data-testid="seed-btn"
            >
              {seeding && <Loader2 className="w-4 h-4 animate-spin" />}
              Inizializza Database Demo
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="p-6 text-center text-sm text-stone-400">
        <p>Shopply MVP - Area Pioltello</p>
      </footer>
    </div>
  );
}
