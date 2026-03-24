import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { ShoppingCart, ArrowLeft, Lock, Loader2, Check, AlertCircle } from 'lucide-react';
import { authAPI } from '../lib/api';

export default function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [maskedEmail, setMaskedEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setVerifying(false);
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const res = await authAPI.verifyResetToken(token);
      setTokenValid(res.data.valid);
      if (res.data.valid) {
        setMaskedEmail(res.data.email);
      } else {
        setError(res.data.message);
      }
    } catch (err) {
      setTokenValid(false);
      setError('Token non valido');
    } finally {
      setVerifying(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 6) {
      setError('La password deve essere di almeno 6 caratteri');
      return;
    }

    if (password !== confirmPassword) {
      setError('Le password non coincidono');
      return;
    }

    setLoading(true);
    try {
      await authAPI.resetPassword(token, password);
      setSuccess(true);
      setTimeout(() => navigate('/login'), 3000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Errore durante il reset');
    } finally {
      setLoading(false);
    }
  };

  if (verifying) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-orange-50 flex flex-col">
      {/* Header */}
      <header className="p-6">
        <Link to="/login" className="flex items-center gap-2 text-stone-600 hover:text-stone-900">
          <ArrowLeft className="w-5 h-5" />
          <span>Torna al login</span>
        </Link>
      </header>

      {/* Main */}
      <main className="flex-1 flex items-center justify-center px-4 pb-12">
        <div className="w-full max-w-md">
          <div className="bg-white rounded-3xl shadow-xl shadow-stone-200/50 p-8">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-emerald-500 rounded-2xl flex items-center justify-center">
                <Lock className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-stone-900">Reimposta Password</h1>
                {maskedEmail && (
                  <p className="text-sm text-stone-500">Per: {maskedEmail}</p>
                )}
              </div>
            </div>

            {!token ? (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-orange-500 mx-auto mb-4" />
                <p className="text-stone-600 mb-4">Nessun token fornito</p>
                <Link
                  to="/login"
                  className="text-emerald-600 hover:underline"
                >
                  Torna al login
                </Link>
              </div>
            ) : !tokenValid ? (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
                <p className="text-stone-600 mb-2">{error || 'Link non valido o scaduto'}</p>
                <p className="text-sm text-stone-500 mb-4">
                  Richiedi un nuovo link dalla pagina di login
                </p>
                <Link
                  to="/login"
                  className="text-emerald-600 hover:underline"
                >
                  Torna al login
                </Link>
              </div>
            ) : success ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Check className="w-8 h-8 text-emerald-600" />
                </div>
                <h2 className="text-xl font-bold text-stone-900 mb-2">Password Reimpostata!</h2>
                <p className="text-stone-500 mb-4">
                  Ora puoi accedere con la nuova password
                </p>
                <p className="text-sm text-stone-400">
                  Reindirizzamento al login...
                </p>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Nuova Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="Minimo 6 caratteri"
                    required
                    minLength={6}
                    data-testid="new-password-input"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-stone-700 mb-2">
                    Conferma Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="w-full h-12 px-4 rounded-xl border border-stone-200 bg-stone-50 focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500 transition-all"
                    placeholder="Ripeti la password"
                    required
                    minLength={6}
                    data-testid="confirm-password-input"
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
                  className="w-full h-12 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 transition-all active:scale-[0.98] disabled:opacity-50 flex items-center justify-center gap-2"
                  data-testid="reset-password-btn"
                >
                  {loading && <Loader2 className="w-5 h-5 animate-spin" />}
                  Reimposta Password
                </button>
              </form>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
